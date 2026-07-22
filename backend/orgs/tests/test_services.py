"""Personal organization provisioning (flow A1 — base laid in It1)."""

import pytest

from orgs.models import Organization, OrganizationMembership
from orgs.services import ensure_personal_org


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        email='ana@example.com', password='x' * 8, first_name='Ana'
    )


@pytest.mark.django_db
def test_ensure_personal_org_creates_org_with_owner_membership(user):
    org = ensure_personal_org(user)

    assert org.kind == Organization.Kind.PERSONAL
    membership = OrganizationMembership.objects.get(organization=org, user=user)
    assert membership.role == OrganizationMembership.Role.OWNER


@pytest.mark.django_db
def test_ensure_personal_org_is_idempotent(user):
    first = ensure_personal_org(user)

    second = ensure_personal_org(user)

    assert first.pk == second.pk
    assert Organization.objects.count() == 1


@pytest.mark.django_db
def test_personal_org_slugs_never_collide(django_user_model):
    ana1 = django_user_model.objects.create_user(email='ana@a.com', password='x' * 8, first_name='Ana')
    ana2 = django_user_model.objects.create_user(email='ana@b.com', password='x' * 8, first_name='Ana')

    org1 = ensure_personal_org(ana1)
    org2 = ensure_personal_org(ana2)

    assert org1.slug != org2.slug


@pytest.mark.django_db
def test_sign_up_endpoint_provisions_personal_org(api_client, settings):
    settings.RECAPTCHA_SECRET_KEY = ''
    response = api_client.post(
        '/api/sign_up/',
        {'email': 'nuevo@example.com', 'password': 'segura123', 'first_name': 'Nuevo'},
        format='json',
    )

    assert response.status_code == 201
    assert OrganizationMembership.objects.filter(
        user__email='nuevo@example.com', role=OrganizationMembership.Role.OWNER
    ).exists()
