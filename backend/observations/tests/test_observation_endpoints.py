"""D3 endpoint guards: replies and the I14 state machine over the API with
engine-independent fixtures (anchored flows live in test_observations.py)."""

from uuid import uuid4

import pytest

from observations.models import Observation, ObservationReply


@pytest.fixture
def doc_version(document_with_versions):
    document, versions = document_with_versions(n_versions=1)
    return document, versions[0]


@pytest.fixture
def open_observation(doc_version, versiona_context):
    document, version = doc_version
    return Observation.objects.create(
        document=document,
        created_on_version=version,
        author=versiona_context.users['reviewer'],
        body='La multa del 2% parece baja.',
    )


@pytest.mark.django_db
@pytest.mark.escenario('D3-A02')
def test_observations_list_filters_by_status(client_as, doc_version, versiona_context, open_observation):
    document, version = doc_version
    resolved = Observation.objects.create(
        document=document,
        created_on_version=version,
        author=versiona_context.users['reviewer'],
        body='Ya resuelta.',
        status=Observation.Status.RESOLVED,
    )

    response = client_as('viewer').get(
        f'/api/versions/{version.public_id}/observations/', {'status': 'resolved'}
    )

    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['public_id'] == str(resolved.public_id)


@pytest.mark.django_db
@pytest.mark.escenario('D3-E01')
def test_create_observation_on_unknown_section_returns_error(client_as, doc_version):
    _, version = doc_version

    response = client_as('reviewer').post(
        f'/api/versions/{version.public_id}/observations/',
        {'body': 'obs', 'section_key': 'no-existe'},
        format='json',
    )

    assert response.status_code == 400
    assert response.data['error'] == 'La sección "no-existe" no existe en esta versión.'


@pytest.mark.django_db
@pytest.mark.escenario('D3-F02')
def test_editor_reply_marks_thread_answered(client_as, open_observation):
    response = client_as('editor').post(
        f'/api/observations/{open_observation.public_id}/replies/',
        {'body': 'Lo subimos al 5%.'},
        format='json',
    )

    assert response.status_code == 201
    assert response.data['status'] == 'answered'
    assert ObservationReply.objects.filter(observation=open_observation).count() == 1


@pytest.mark.django_db
@pytest.mark.escenario('D3-P02')
def test_viewer_cannot_reply_to_observation(client_as, open_observation):
    response = client_as('viewer').post(
        f'/api/observations/{open_observation.public_id}/replies/',
        {'body': 'intento'},
        format='json',
    )

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.escenario('D3-P04')
def test_reply_to_unknown_observation_returns_404(client_as, versiona_context):
    response = client_as('editor').post(
        f'/api/observations/{uuid4()}/replies/', {'body': 'hola'}, format='json'
    )

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.escenario('D3-P04')
def test_reply_from_non_member_returns_404(client_as, open_observation):
    response = client_as('non_member').post(
        f'/api/observations/{open_observation.public_id}/replies/',
        {'body': 'ajeno'},
        format='json',
    )

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.escenario('D3-E01')
def test_reply_without_body_returns_validation_error(client_as, open_observation):
    response = client_as('editor').post(
        f'/api/observations/{open_observation.public_id}/replies/', {}, format='json'
    )

    assert response.status_code == 400
    assert response.data['error'] == 'La respuesta necesita un texto.'


@pytest.mark.django_db
@pytest.mark.escenario('D3-F02')
def test_author_resolves_answered_thread_via_api(client_as, doc_version, versiona_context):
    document, version = doc_version
    observation = Observation.objects.create(
        document=document,
        created_on_version=version,
        author=versiona_context.users['reviewer'],
        body='Pendiente de cierre.',
        status=Observation.Status.ANSWERED,
    )

    response = client_as('reviewer').post(
        f'/api/observations/{observation.public_id}/status/',
        {'status': 'resolved'},
        format='json',
    )

    assert response.status_code == 200
    assert response.data['status'] == 'resolved'
    assert response.data['resolved_in'] == 1


@pytest.mark.django_db
@pytest.mark.escenario('D3-P02')
def test_viewer_cannot_change_observation_status(client_as, open_observation):
    response = client_as('viewer').post(
        f'/api/observations/{open_observation.public_id}/status/',
        {'status': 'answered'},
        format='json',
    )

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.escenario('D3-E01')
def test_invalid_status_transition_returns_conflict(client_as, open_observation):
    response = client_as('reviewer').post(
        f'/api/observations/{open_observation.public_id}/status/',
        {'status': 'resolved'},
        format='json',
    )

    assert response.status_code == 409
    assert 'I14' in response.data['error']
