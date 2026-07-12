"""Integration matrix for project endpoints (flows B1/B2/B4 — docs/audit/03 §2).
Permission rows follow the P01–P04 grammar with the 7 audit actors."""

import pytest

from projects.models import Project, ProjectMembership


def org_projects_url(context):
    return f'/api/orgs/{context.org.public_id}/projects/'


def project_url(context, suffix=''):
    return f'/api/projects/{context.project.public_id}/{suffix}'


# ---------------------------------------------------------------------------
# B1 — create project
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.escenario('B1-F01')
def test_create_project_makes_creator_admin(client_as, versiona_context):
    client = client_as('editor')

    response = client.post(org_projects_url(versiona_context), {'name': 'Licencia 2026'})

    assert response.status_code == 201
    project = Project.objects.get(slug='licencia-2026')
    membership = ProjectMembership.objects.get(project=project, user=versiona_context.users['editor'])
    assert membership.role == ProjectMembership.Role.ADMIN


@pytest.mark.django_db
@pytest.mark.escenario('B1-E01')
def test_create_project_rejects_blank_name(client_as, versiona_context):
    response = client_as('editor').post(org_projects_url(versiona_context), {'name': '   '})

    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('owner', 201, id='b1-p01-owner'),
    pytest.param('admin', 201, id='b1-p01-admin'),
    pytest.param('editor', 201, id='b1-p01-editor'),
    pytest.param('reviewer', 201, id='b1-p01-reviewer'),
    pytest.param('viewer', 201, id='b1-p01-viewer'),
    pytest.param('non_member', 404, id='b1-p04-non-member'),
    pytest.param('anonymous', 401, id='b1-p03-anonymous'),
])
def test_create_project_permission_matrix(client_as, versiona_context, actor, expected):
    response = client_as(actor).post(
        org_projects_url(versiona_context), {'name': f'Proyecto {actor}'}
    )

    assert response.status_code == expected


# ---------------------------------------------------------------------------
# B2 — board (minimal: list + name search)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.escenario('B2-F01')
def test_board_lists_member_projects_with_role(client_as, versiona_context):
    response = client_as('viewer').get(org_projects_url(versiona_context))

    assert response.status_code == 200
    names = [row['name'] for row in response.data['results']]
    assert 'Torre Central' in names
    row = next(r for r in response.data['results'] if r['name'] == 'Torre Central')
    assert row['effective_role'] == 'viewer'


@pytest.mark.django_db
@pytest.mark.escenario('B2-A02')
def test_board_search_by_name(client_as, versiona_context):
    Project.objects.create(organization=versiona_context.org, name='Otro asunto', slug='otro')

    response = client_as('owner').get(org_projects_url(versiona_context) + '?q=torre')

    names = [row['name'] for row in response.data['results']]
    assert names == ['Torre Central']


@pytest.mark.django_db
@pytest.mark.escenario('B2-P04')
def test_org_member_without_project_membership_sees_empty_board(
    client_as, versiona_context, django_user_model
):
    from orgs.models import OrganizationMembership

    outsider = django_user_model.objects.create_user(email='out@versiona.test', password='x' * 8)
    OrganizationMembership.objects.create(
        organization=versiona_context.org, user=outsider,
        role=OrganizationMembership.Role.MEMBER,
    )
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=outsider)

    response = client.get(org_projects_url(versiona_context))

    assert response.status_code == 200
    assert response.data['results'] == []


# ---------------------------------------------------------------------------
# Project detail / edit / trash / archive (B4 + kit 2)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('owner', 200, id='b2-p01-owner'),
    pytest.param('viewer', 200, id='b2-p01-viewer'),
    pytest.param('non_member', 404, id='b2-p04-non-member'),
    pytest.param('anonymous', 401, id='b2-p03-anonymous'),
])
def test_project_detail_permission_matrix(client_as, versiona_context, actor, expected):
    response = client_as(actor).get(project_url(versiona_context))

    assert response.status_code == expected


@pytest.mark.django_db
@pytest.mark.escenario('B3-A02')
def test_admin_edits_project_metadata(client_as, versiona_context):
    response = client_as('admin').patch(
        project_url(versiona_context), {'description': 'Expediente curaduría 2'}, format='json'
    )

    assert response.status_code == 200
    versiona_context.project.refresh_from_db()
    assert versiona_context.project.description == 'Expediente curaduría 2'


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('admin', 204, id='b4-p01-admin'),
    pytest.param('editor', 403, id='b4-p02-editor'),
    pytest.param('anonymous', 401, id='b4-p03-anonymous'),
    pytest.param('non_member', 404, id='b4-p04-non-member'),
])
def test_trash_project_permission_matrix(client_as, versiona_context, actor, expected):
    response = client_as(actor).delete(
        project_url(versiona_context), {'confirm_name': 'Torre Central'}, format='json'
    )

    assert response.status_code == expected


@pytest.mark.django_db
@pytest.mark.escenario('B4-F02')
def test_trash_requires_exact_name_and_restore_recovers(client_as, versiona_context):
    admin = client_as('admin')

    wrong = admin.delete(project_url(versiona_context), {'confirm_name': 'torre'}, format='json')
    assert wrong.status_code == 400

    ok = admin.delete(
        project_url(versiona_context), {'confirm_name': 'Torre Central'}, format='json'
    )
    assert ok.status_code == 204

    restored = admin.post(project_url(versiona_context, 'restore/'))
    assert restored.status_code == 200
    versiona_context.project.refresh_from_db()
    assert not versiona_context.project.is_trashed


@pytest.mark.django_db
@pytest.mark.escenario('B4-F01')
def test_archive_and_unarchive_roundtrip(client_as, versiona_context):
    admin = client_as('admin')

    archived = admin.post(project_url(versiona_context, 'archive/'))
    assert archived.status_code == 200
    assert archived.data['status'] == 'archived'

    unarchived = admin.post(project_url(versiona_context, 'unarchive/'))
    assert unarchived.status_code == 200
    assert unarchived.data['status'] == 'active'


@pytest.mark.django_db
def test_my_orgs_lists_membership_role(client_as, versiona_context):
    response = client_as('owner').get('/api/orgs/')

    assert response.status_code == 200
    row = next(r for r in response.data['results'] if r['slug'] == 'acme-test')
    assert row['role'] == 'owner'


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('owner', 200, id='trash-p01-owner'),
    pytest.param('viewer', 403, id='trash-p02-viewer'),
    pytest.param('anonymous', 401, id='trash-p03-anonymous'),
    pytest.param('non_member', 404, id='trash-p04-non-member'),
])
def test_org_trash_permission_matrix(client_as, versiona_context, actor, expected):
    response = client_as(actor).get(f'/api/orgs/{versiona_context.org.public_id}/trash/')

    assert response.status_code == expected
