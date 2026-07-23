"""F1 limits (I13, DP-04: lock never delete) + F2 usage warnings."""

from datetime import timedelta

import pytest
from django.utils import timezone


@pytest.fixture(autouse=True)
def _free_plan(versiona_context):
    """The shared context org is `pro` (it exercises every flow); the limit
    tests are exactly about `free`, so they flip it explicitly."""
    org = versiona_context.org
    org.plan = 'free'
    org.save(update_fields=['plan'])
    return org

from billing.services import (
    check_history_access,
    check_project_limit,
    usage_report,
)
from documents.services.version_service import DomainError


@pytest.mark.django_db
@pytest.mark.escenario('F1-L01')
@pytest.mark.escenario('B1-L01')
def test_free_plan_allows_one_active_project(versiona_context):
    """The seeded org already has Torre Central active ⇒ a second project on
    the free plan is rejected with the informative upgrade CTA (402)."""
    org = versiona_context.org

    with pytest.raises(DomainError) as exc:
        check_project_limit(org)

    assert exc.value.status_code == 402
    assert 'Mejora tu plan' in str(exc.value)


@pytest.mark.django_db
@pytest.mark.escenario('F1-L01')
def test_pro_plan_lifts_the_project_limit(versiona_context):
    org = versiona_context.org
    org.plan = 'pro'
    org.save(update_fields=['plan'])

    check_project_limit(org)  # no exception


@pytest.mark.django_db
@pytest.mark.escenario('F1-L02')
@pytest.mark.escenario('A2-L01')
def test_member_limit_blocks_new_invitations(versiona_context):
    """The seeded org has 7 members — way past free's 2 ⇒ inviting is blocked
    (existing members are NEVER removed: DP-04)."""
    from orgs.invitations import create_invitation

    with pytest.raises(DomainError) as exc:
        create_invitation(
            versiona_context.project, versiona_context.users['admin'],
            email='octava@externa.co', role='viewer',
        )

    assert exc.value.status_code == 402


@pytest.mark.django_db
@pytest.mark.escenario('C3-L02')
@pytest.mark.escenario('F1-L03')
def test_old_history_is_locked_not_deleted_on_free(versiona_context, document_with_versions):
    document, versions = document_with_versions(n_versions=2)
    from documents.models import DocumentVersion

    DocumentVersion.all_objects.filter(pk=versions[0].pk).update(
        created_at=timezone.now() - timedelta(days=45)
    )
    old = DocumentVersion.objects.get(pk=versions[0].pk)

    with pytest.raises(DomainError) as exc:
        check_history_access(old)

    assert exc.value.status_code == 402
    assert 'nada se borra' in str(exc.value)
    # The latest version is ALWAYS accessible regardless of age.
    DocumentVersion.all_objects.filter(pk=versions[1].pk).update(
        created_at=timezone.now() - timedelta(days=45)
    )
    check_history_access(DocumentVersion.objects.get(pk=versions[1].pk))


@pytest.mark.django_db
@pytest.mark.escenario('C3-L02')
def test_pro_plan_unlocks_history(versiona_context, document_with_versions):
    document, versions = document_with_versions(n_versions=2)
    org = versiona_context.org
    org.plan = 'pro'
    org.save(update_fields=['plan'])
    from documents.models import DocumentVersion

    DocumentVersion.all_objects.filter(pk=versions[0].pk).update(
        created_at=timezone.now() - timedelta(days=400)
    )

    check_history_access(DocumentVersion.objects.get(pk=versions[0].pk))


@pytest.mark.django_db
@pytest.mark.escenario('F2-F01')
@pytest.mark.escenario('F2-L01')
def test_usage_report_warns_at_capacity(versiona_context):
    report = usage_report(versiona_context.org)

    assert report['plan'] == 'free'
    assert report['usage']['active_projects'] == 1
    assert report['upgrade_available'] is True
    limits_flagged = {warning['limit'] for warning in report['warnings']}
    assert 'max_active_projects' in limits_flagged  # 1/1 = at capacity
    assert 'max_members' in limits_flagged  # 7/2
    at_capacity = {w['limit']: w['at_capacity'] for w in report['warnings']}
    assert at_capacity['max_members'] is True


@pytest.mark.django_db
@pytest.mark.escenario('F1-F01')
@pytest.mark.escenario('B1-L01')
def test_create_project_endpoint_returns_402_with_upgrade_flag(client_as, versiona_context):
    response = client_as('owner').post(
        f'/api/orgs/{versiona_context.org.public_id}/projects/',
        {'name': 'Segundo proyecto'},
        format='json',
    )

    assert response.status_code == 402
    assert response.data['upgrade'] is True


@pytest.mark.django_db
@pytest.mark.escenario('F2-F02')
@pytest.mark.escenario('F2-P01')
def test_usage_endpoint_visible_to_members_only(client_as, versiona_context):
    url = f'/api/orgs/{versiona_context.org.public_id}/usage/'

    member = client_as('viewer').get(url)
    outsider = client_as('non_member').get(url)

    assert member.status_code == 200
    assert member.data['limits']['max_members'] == 2
    assert outsider.status_code == 404
