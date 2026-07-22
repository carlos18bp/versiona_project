"""Effective-role resolution (docs/plan/03 §5 — gap G24, invariant I12)."""

import pytest

from core.permissions import resolve_effective_role, resolve_org_role


@pytest.mark.django_db
def test_org_owner_is_implicit_project_admin(versiona_context):
    role = resolve_effective_role(versiona_context.users['owner'], versiona_context.project)

    assert role == 'admin'


@pytest.mark.django_db
@pytest.mark.parametrize('alias, expected', [
    ('admin', 'admin'),
    ('editor', 'editor'),
    ('reviewer', 'reviewer'),
    ('viewer', 'viewer'),
])
def test_project_membership_role_is_returned(versiona_context, alias, expected):
    role = resolve_effective_role(versiona_context.users[alias], versiona_context.project)

    assert role == expected


@pytest.mark.django_db
def test_foreign_org_user_has_no_effective_role(versiona_context):
    role = resolve_effective_role(versiona_context.users['non_member'], versiona_context.project)

    assert role is None


@pytest.mark.django_db
def test_org_member_without_project_membership_has_no_role(versiona_context, django_user_model):
    from orgs.models import OrganizationMembership

    outsider = django_user_model.objects.create_user(email='out@versiona.test', password='x' * 8)
    OrganizationMembership.objects.create(
        organization=versiona_context.org,
        user=outsider,
        role=OrganizationMembership.Role.MEMBER,
    )

    assert resolve_effective_role(outsider, versiona_context.project) is None


@pytest.mark.django_db
def test_anonymous_user_has_no_org_role(versiona_context):
    from django.contrib.auth.models import AnonymousUser

    assert resolve_org_role(AnonymousUser(), versiona_context.org) is None
