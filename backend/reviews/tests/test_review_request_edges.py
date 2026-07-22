"""D1 request endpoint edges + service validations over engine-independent
fixtures (versions arrive analyzed from the shared context)."""

from uuid import uuid4

import pytest

from documents.models import DocumentVersion
from documents.services.version_service import DomainError
from reviews.models import ReviewRequest
from reviews.services import review_service


@pytest.fixture
def ready_version(document_with_versions):
    document, versions = document_with_versions(n_versions=1)
    return document, versions[0]


@pytest.fixture
def open_review(ready_version, versiona_context):
    _, version = ready_version
    return review_service.create_review_request(
        version, versiona_context.users['editor'],
        [versiona_context.users['reviewer'].pk],
        message='prioridad multas',
    )


@pytest.mark.django_db
@pytest.mark.escenario('D1-F01')
def test_reviews_list_returns_requests_with_assignments(
    client_as, ready_version, versiona_context, open_review
):
    _, version = ready_version

    response = client_as('viewer').get(f'/api/versions/{version.public_id}/reviews/')

    assert response.status_code == 200
    row = response.data['results'][0]
    assert row['status'] == 'open'
    assert row['assignments'][0]['reviewer_email'] == versiona_context.users['reviewer'].email


@pytest.mark.django_db
@pytest.mark.escenario('D1-E02')
def test_second_open_request_via_api_returns_conflict(
    client_as, ready_version, versiona_context, open_review
):
    _, version = ready_version

    response = client_as('editor').post(
        f'/api/versions/{version.public_id}/reviews/',
        {'reviewer_ids': [versiona_context.users['reviewer'].pk]},
        format='json',
    )

    assert response.status_code == 409
    assert response.data['error'] == 'Esta versión ya tiene una revisión abierta.'


@pytest.mark.django_db
@pytest.mark.escenario('D1-A02')
def test_requester_cancels_open_review_via_api(client_as, ready_version, open_review):
    _, version = ready_version

    response = client_as('editor').post(
        f'/api/versions/{version.public_id}/reviews/{open_review.public_id}/cancel/'
    )

    assert response.status_code == 200
    assert response.data['status'] == 'cancelled'
    open_review.refresh_from_db()
    assert open_review.closed_at is not None


@pytest.mark.django_db
@pytest.mark.escenario('D1-P04')
def test_cancel_unknown_review_returns_404(client_as, ready_version):
    _, version = ready_version

    response = client_as('editor').post(
        f'/api/versions/{version.public_id}/reviews/{uuid4()}/cancel/'
    )

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.escenario('D1-A02')
def test_cancel_already_closed_review_returns_conflict(
    client_as, ready_version, versiona_context, open_review
):
    _, version = ready_version
    review_service.cancel_review_request(open_review, versiona_context.users['editor'])

    response = client_as('editor').post(
        f'/api/versions/{version.public_id}/reviews/{open_review.public_id}/cancel/'
    )

    assert response.status_code == 409
    assert response.data['error'] == 'La solicitud ya está cerrada.'


@pytest.mark.django_db
@pytest.mark.escenario('D2-L01')
def test_review_context_endpoint_returns_empty_payload_without_seal(client_as, ready_version):
    _, version = ready_version

    response = client_as('reviewer').get(f'/api/versions/{version.public_id}/review_context/')

    assert response.status_code == 200
    assert response.data == {'my_last_sealed_version': None, 'changed': [], 'unchanged': []}


@pytest.mark.django_db
@pytest.mark.escenario('D1-E01')
def test_review_request_requires_analyzed_version(ready_version, versiona_context):
    _, version = ready_version
    DocumentVersion.all_objects.filter(pk=version.pk).update(
        analysis_status=DocumentVersion.AnalysisStatus.PENDING
    )
    version.refresh_from_db()

    with pytest.raises(DomainError) as excinfo:
        review_service.create_review_request(
            version, versiona_context.users['editor'],
            [versiona_context.users['reviewer'].pk],
        )

    assert excinfo.value.status_code == 409
    assert str(excinfo.value) == 'Solo se puede solicitar revisión de una versión analizada.'


@pytest.mark.django_db
@pytest.mark.escenario('D1-E01')
def test_review_request_on_trashed_version_is_rejected(ready_version, versiona_context):
    _, version = ready_version
    version.soft_delete(versiona_context.users['editor'])

    with pytest.raises(DomainError) as excinfo:
        review_service.create_review_request(
            version, versiona_context.users['editor'],
            [versiona_context.users['reviewer'].pk],
        )

    assert excinfo.value.status_code == 409
    assert str(excinfo.value) == 'La versión está en la papelera.'


@pytest.mark.django_db
@pytest.mark.escenario('D1-E01')
def test_review_request_without_reviewers_is_rejected(ready_version, versiona_context):
    _, version = ready_version

    with pytest.raises(DomainError) as excinfo:
        review_service.create_review_request(version, versiona_context.users['editor'], [])

    assert excinfo.value.status_code == 400
    assert str(excinfo.value) == 'Elige al menos un revisor.'


@pytest.mark.django_db
@pytest.mark.escenario('D1-E01')
def test_review_request_with_unknown_reviewer_is_rejected(ready_version, versiona_context):
    _, version = ready_version

    with pytest.raises(DomainError) as excinfo:
        review_service.create_review_request(
            version, versiona_context.users['editor'], [999999]
        )

    assert excinfo.value.status_code == 400
    assert str(excinfo.value) == 'Algún revisor no existe.'


@pytest.mark.django_db
@pytest.mark.escenario('D1-A02')
def test_non_requester_reviewer_cannot_cancel_review(versiona_context, open_review):
    with pytest.raises(DomainError) as excinfo:
        review_service.cancel_review_request(open_review, versiona_context.users['reviewer'])

    assert excinfo.value.status_code == 403
    assert str(excinfo.value) == 'Solo quien la abrió (o un admin) puede cancelarla.'


@pytest.mark.django_db
@pytest.mark.escenario('D1-A02')
def test_admin_who_did_not_request_can_cancel_review(versiona_context, open_review):
    review = review_service.cancel_review_request(open_review, versiona_context.users['admin'])

    assert review.status == ReviewRequest.Status.CANCELLED
