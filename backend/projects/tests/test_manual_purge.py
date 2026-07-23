"""B4-A01 negative verification: the owner's early-purge endpoint (second
confirmation → physical delete + audit event) is NOT routed. Only the beat
task `purge_expired` deletes trashed rows, and only after the grace window."""

import uuid

import pytest
from django.urls import Resolver404, resolve
from freezegun import freeze_time

from documents.services import trash_service
from projects.models import Project


@pytest.fixture
def trashed_project(versiona_context):
    with freeze_time('2026-06-01'):
        trash_service.trash_project(
            versiona_context.project,
            versiona_context.project.name,
            versiona_context.users['owner'],
        )
    return versiona_context.project


@pytest.mark.django_db
@pytest.mark.escenario('B4-A01')
def test_project_purge_route_is_not_registered():
    with pytest.raises(Resolver404):
        resolve(f'/api/projects/{uuid.uuid4()}/purge/')


@pytest.mark.django_db
@pytest.mark.escenario('B4-A01')
def test_owner_purge_request_on_a_trashed_project_is_not_found(client_as, trashed_project):
    response = client_as('owner').post(
        f'/api/projects/{trashed_project.public_id}/purge/',
        {'confirm_name': trashed_project.name},
        format='json',
    )

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.escenario('B4-A01')
def test_trashed_project_survives_an_early_purge_attempt(client_as, trashed_project):
    client_as('owner').post(
        f'/api/projects/{trashed_project.public_id}/purge/',
        {'confirm_name': trashed_project.name},
        format='json',
    )

    assert Project.all_objects.filter(pk=trashed_project.pk).exists()


@pytest.mark.django_db
@pytest.mark.escenario('B4-A01')
def test_automatic_purge_skips_a_project_still_inside_the_grace_window(
    trashed_project, settings
):
    settings.TRASH_RETENTION_DAYS = 30

    with freeze_time('2026-06-10'):
        counts = trash_service.purge_expired()

    assert counts['projects'] == 0
