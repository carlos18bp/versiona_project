"""A1: wizard + sample project seed → the wow link (metric S1)."""

import pytest

from orgs.onboarding import complete_onboarding
from orgs.services import ensure_personal_org


@pytest.fixture(autouse=True)
def _test_env(settings, tmp_path):
    settings.DJANGO_ENV = 'test'
    settings.SEAL_SIGNING_KEY_PATH = str(tmp_path / 'seal_key.pem')


@pytest.fixture
def fresh_user(django_user_model):
    user = django_user_model.objects.create_user(
        email='nueva@versiona.test', password='secreta123', first_name='Nueva'
    )
    ensure_personal_org(user)
    return user


@pytest.mark.django_db
@pytest.mark.escenario('A1-F01')
def test_onboarding_seeds_the_sample_with_a_working_comparison(fresh_user):
    """The wow: two analyzed versions + the auto comparison, without the user
    uploading anything."""
    state = complete_onboarding(fresh_user, 'Constructora Nueva')

    assert state['status'] == 'done'
    assert state['org_name'] == 'Constructora Nueva'
    assert '/compare/' in state['wow_link']
    from comparisons.models import Comparison

    comparison = Comparison.objects.get()
    assert comparison.status == 'done'
    assert comparison.summary['counts']['modified'] == 2


@pytest.mark.django_db
@pytest.mark.escenario('A1-F02')
def test_onboarding_is_idempotent(fresh_user):
    first = complete_onboarding(fresh_user, 'Mi Org')
    second = complete_onboarding(fresh_user, 'Mi Org')

    assert first['project'] == second['project']
    from projects.models import Project

    assert Project.objects.filter(is_sample=True).count() == 1


@pytest.mark.django_db
@pytest.mark.escenario('A1-F03')
def test_state_endpoint_reports_pending_then_done(client_as, fresh_user):
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(fresh_user)

    before = client.get('/api/me/onboarding/')
    assert before.data['status'] == 'pending'

    created = client.post('/api/me/onboarding/', {'org_name': 'Org Nueva'}, format='json')
    assert created.status_code == 201
    assert created.data['status'] == 'done'

    after = client.get('/api/me/onboarding/')
    assert after.data['status'] == 'done'
    assert after.data['wow_link'] == created.data['wow_link']


@pytest.mark.django_db
def test_anonymous_cannot_touch_onboarding(client_as):
    assert client_as('anonymous').get('/api/me/onboarding/').status_code == 401
