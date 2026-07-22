"""E2 saved comparisons + F3 org audit + kit 4 project report."""

from pathlib import Path

import pytest

from comparisons.models import Comparison
from documents.services import storage_service, version_service

TESTDATA = Path(__file__).resolve().parents[3] / 'testdata' / 'pdfs'


@pytest.fixture(autouse=True)
def _test_env(settings, tmp_path):
    settings.DJANGO_ENV = 'test'
    settings.SEAL_SIGNING_KEY_PATH = str(tmp_path / 'seal_key.pem')


@pytest.fixture
def compared(versiona_context):
    editor = versiona_context.users['editor']
    document = version_service.create_document(versiona_context.project, 'Guardable', editor)
    for fixture, message in (('contrato_v1.pdf', 'v1'), ('contrato_v2.pdf', 'v2')):
        intent = version_service.create_upload_intent(document, editor)
        storage_service.put_bytes(
            intent.key, (TESTDATA / fixture).read_bytes(), 'application/pdf'
        )
        version_service.complete_upload(document, intent.upload_id, message, editor)
    return versiona_context, Comparison.objects.get(trigger=Comparison.Trigger.AUTO)


@pytest.mark.django_db
@pytest.mark.escenario('E2-F01')
def test_save_and_list_named_comparisons(client_as, compared):
    context, comparison = compared
    client = client_as('editor')

    created = client.post(
        f'/api/comparisons/{comparison.public_id}/save/',
        {'name': 'Entrega 1 vs 2'},
        format='json',
    )
    assert created.status_code == 201

    listing = client.get(
        f'/api/projects/{context.project.public_id}/saved_comparisons/'
    )
    assert listing.status_code == 200
    row = listing.data['results'][0]
    assert row['name'] == 'Entrega 1 vs 2'
    assert '/compare/' in row['link']
    assert row['summary'] == '2 modificadas, 1 eliminada, 1 agregada'


@pytest.mark.django_db
@pytest.mark.escenario('E2-E01')
def test_duplicate_name_is_rejected(client_as, compared):
    context, comparison = compared
    client = client_as('editor')
    client.post(f'/api/comparisons/{comparison.public_id}/save/',
                {'name': 'Única'}, format='json')

    duplicate = client.post(
        f'/api/comparisons/{comparison.public_id}/save/', {'name': 'Única'}, format='json'
    )

    assert duplicate.status_code == 409


@pytest.mark.django_db
@pytest.mark.escenario('E2-P02')
def test_viewer_cannot_save_but_can_list(client_as, compared):
    context, comparison = compared

    denied = client_as('viewer').post(
        f'/api/comparisons/{comparison.public_id}/save/', {'name': 'X'}, format='json'
    )
    listing = client_as('viewer').get(
        f'/api/projects/{context.project.public_id}/saved_comparisons/'
    )

    assert denied.status_code == 404
    assert listing.status_code == 200


@pytest.mark.django_db
@pytest.mark.escenario('F3-F01')
def test_org_audit_filters_and_is_admin_only(client_as, versiona_context, compared):
    url = f'/api/orgs/{versiona_context.org.public_id}/audit/'

    admin_view = client_as('owner').get(url + '?type=version.uploaded')
    member_view = client_as('viewer').get(url)

    assert admin_view.status_code == 200
    assert all(
        row['event_type'] == 'version.uploaded' for row in admin_view.data['results']
    )
    assert len(admin_view.data['results']) == 2  # v1 y v2 del fixture
    assert member_view.status_code == 404  # org members without admin: hidden


@pytest.mark.django_db
@pytest.mark.escenario('F3-F02')
def test_org_audit_exports_csv(client_as, versiona_context, compared):
    response = client_as('owner').get(
        f'/api/orgs/{versiona_context.org.public_id}/audit/?export=csv'
    )

    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/csv')
    body = response.content.decode()
    assert 'version.uploaded' in body
    assert 'fecha,evento,actor,payload' in body.splitlines()[0]


@pytest.mark.django_db
@pytest.mark.escenario('REP-F01')
def test_project_report_summarizes_documents(client_as, compared):
    context, _ = compared

    response = client_as('viewer').get(
        f'/api/projects/{context.project.public_id}/report/'
    )

    assert response.status_code == 200
    row = response.data['documents'][0]
    assert row['document'] == 'Guardable'
    assert row['latest_version'] == 2
    assert row['approved'] is False
    assert row['open_observations'] == 0


@pytest.mark.django_db
@pytest.mark.escenario('ACT-F03')
def test_activity_accepts_a_date_range(client_as, compared):
    context, _ = compared

    inside = client_as('viewer').get(
        f'/api/projects/{context.project.public_id}/activity/?from=2026-01-01&to=2026-12-31'
    )
    outside = client_as('viewer').get(
        f'/api/projects/{context.project.public_id}/activity/?from=2020-01-01&to=2020-12-31'
    )

    assert inside.data['results']
    assert outside.data['results'] == []
