"""D1 review requests + D2 assisted context (integration over real fixtures)."""

from pathlib import Path

import pytest

from documents.services import storage_service, version_service
from notifications.models import Notification
from reviews.models import ReviewAssignment, ReviewRequest
from reviews.services import review_service, seal_service

TESTDATA = Path(__file__).resolve().parents[3] / 'testdata' / 'pdfs'


@pytest.fixture(autouse=True)
def _test_env(settings, tmp_path):
    settings.DJANGO_ENV = 'test'
    settings.SEAL_SIGNING_KEY_PATH = str(tmp_path / 'seal_key.pem')


def upload(document, fixture, message, author):
    intent = version_service.create_upload_intent(document, author)
    storage_service.put_bytes(intent.key, (TESTDATA / fixture).read_bytes(), 'application/pdf')
    version, _ = version_service.complete_upload(document, intent.upload_id, message, author)
    return version


@pytest.fixture
def analyzed_v1(versiona_context):
    editor = versiona_context.users['editor']
    document = version_service.create_document(versiona_context.project, 'Revisable', editor)
    return versiona_context, document, upload(document, 'contrato_v1.pdf', 'v1', editor)


@pytest.mark.django_db
@pytest.mark.escenario('D1-F01')
def test_request_assigns_reviewers_and_notifies_them(analyzed_v1):
    context, document, v1 = analyzed_v1
    editor = context.users['editor']
    reviewer = context.users['reviewer']

    review = review_service.create_review_request(
        v1, editor, [reviewer.pk], message='prioridad multas'
    )

    assert review.status == ReviewRequest.Status.OPEN
    assignment = review.assignments.get()
    assert assignment.reviewer == reviewer
    assert assignment.status == ReviewAssignment.Status.PENDING
    notification = Notification.objects.get(user=reviewer, event_key='review.requested')
    assert 'Revisable' in notification.title
    assert 'prioridad multas' in notification.body


@pytest.mark.django_db
@pytest.mark.escenario('D1-F02')
def test_open_request_freezes_the_draft_message(analyzed_v1):
    context, document, v1 = analyzed_v1
    editor = context.users['editor']
    review_service.create_review_request(v1, editor, [context.users['reviewer'].pk])

    v1.refresh_from_db()
    assert v1.is_draft is False  # I2b frontier
    with pytest.raises(version_service.DomainError):
        version_service.edit_message(v1, 'tarde', editor)


@pytest.mark.django_db
@pytest.mark.escenario('D1-F03')
def test_seal_completes_the_assignment_and_the_request(analyzed_v1):
    context, document, v1 = analyzed_v1
    editor = context.users['editor']
    reviewer = context.users['reviewer']
    review = review_service.create_review_request(v1, editor, [reviewer.pk])

    seal_service.create_seal(v1, reviewer, covers_all=True)

    review.refresh_from_db()
    assert review.status == ReviewRequest.Status.COMPLETED
    assert review.assignments.get().status == ReviewAssignment.Status.DONE
    assert Notification.objects.filter(
        user=editor, event_key='review.completed'
    ).exists()


@pytest.mark.django_db
@pytest.mark.escenario('D1-A02')
def test_new_version_supersedes_the_open_request(analyzed_v1):
    context, document, v1 = analyzed_v1
    editor = context.users['editor']
    review = review_service.create_review_request(v1, editor, [context.users['reviewer'].pk])

    upload(document, 'contrato_v2.pdf', 'v2', editor)

    review.refresh_from_db()
    assert review.status == ReviewRequest.Status.SUPERSEDED
    # The frozen message stays frozen even though the request closed? No: the
    # request is no longer open, and without seals v1 becomes draft again —
    # BUT its number is already superseded; editing history is not the point.
    # What matters: the reviewer inbox no longer lists it.
    assignments = ReviewAssignment.objects.filter(
        review_request=review, status=ReviewAssignment.Status.PENDING
    )
    assert assignments.exists()  # untouched rows, but the request is closed


@pytest.mark.django_db
@pytest.mark.escenario('D1-E01')
def test_reviewer_selection_is_validated(analyzed_v1):
    context, document, v1 = analyzed_v1
    editor = context.users['editor']

    with pytest.raises(version_service.DomainError) as viewer_error:
        review_service.create_review_request(v1, editor, [context.users['viewer'].pk])
    assert 'no puede revisar' in str(viewer_error.value)

    with pytest.raises(version_service.DomainError) as self_error:
        review_service.create_review_request(
            v1, context.users['admin'], [context.users['admin'].pk]
        )
    assert 'propia revisión' in str(self_error.value)


@pytest.mark.django_db
@pytest.mark.escenario('D1-E02')
def test_second_open_request_on_the_same_version_is_rejected(analyzed_v1):
    context, document, v1 = analyzed_v1
    editor = context.users['editor']
    review_service.create_review_request(v1, editor, [context.users['reviewer'].pk])

    with pytest.raises(version_service.DomainError) as exc:
        review_service.create_review_request(v1, editor, [context.users['admin'].pk])
    assert exc.value.status_code == 409


@pytest.mark.django_db
@pytest.mark.escenario('D2-F01')
def test_review_context_marks_changed_and_unchanged_since_my_seal(analyzed_v1):
    """The heart of D2: reviewer sealed §1-2 on v1; v2 changes §3/§5 — the
    context says exactly which sections deserve their attention."""
    context, document, v1 = analyzed_v1
    editor = context.users['editor']
    reviewer = context.users['reviewer']
    seal_service.create_seal(
        v1, reviewer, section_keys=['objeto-del-contrato', 'definiciones']
    )
    v2 = upload(document, 'contrato_v2.pdf', 'v2', editor)

    payload = review_service.review_context(v2, reviewer)

    assert payload['my_last_sealed_version'] == 1
    changed = {entry['stable_key'] for entry in payload['changed']}
    unchanged = {entry['stable_key'] for entry in payload['unchanged']}
    assert 'obligaciones-del-contratista' in changed
    assert 'proteccion-de-datos-personales' in changed  # added: new to me
    assert {'objeto-del-contrato', 'definiciones'} <= unchanged
    assert 'confidencialidad' in unchanged  # renumbered, body intact


@pytest.mark.django_db
@pytest.mark.escenario('D2-L01')
def test_review_context_is_empty_without_a_previous_seal(analyzed_v1):
    context, _, v1 = analyzed_v1

    payload = review_service.review_context(v1, context.users['reviewer'])

    assert payload == {'my_last_sealed_version': None, 'changed': [], 'unchanged': []}


@pytest.mark.django_db
@pytest.mark.escenario('D1-F04')
def test_inbox_lists_pending_assignments_via_api(client_as, analyzed_v1):
    context, document, v1 = analyzed_v1
    review_service.create_review_request(
        v1, context.users['editor'], [context.users['reviewer'].pk], message='urgente'
    )

    response = client_as('reviewer').get('/api/me/review_assignments/')

    assert response.status_code == 200
    assert len(response.data['results']) == 1
    row = response.data['results'][0]
    assert row['document_title'] == 'Revisable'
    assert row['requested_by'] == context.users['editor'].email
    assert row['message'] == 'urgente'


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('editor', 201, id='d1-p01-editor'),
    pytest.param('admin', 201, id='d1-p01-admin'),
    pytest.param('reviewer', 404, id='d1-p02-reviewer-hidden'),
    pytest.param('viewer', 404, id='d1-p02-viewer-hidden'),
    pytest.param('anonymous', 401, id='d1-p03-anonymous'),
    pytest.param('non_member', 404, id='d1-p04-non-member'),
])
def test_create_review_permission_matrix(client_as, analyzed_v1, actor, expected):
    context, document, v1 = analyzed_v1

    response = client_as(actor).post(
        f'/api/versions/{v1.public_id}/reviews/',
        {'reviewer_ids': [context.users['reviewer'].pk]},
        format='json',
    )

    assert response.status_code == expected


@pytest.mark.django_db
def test_members_endpoint_feeds_the_reviewer_picker(client_as, versiona_context):
    response = client_as('editor').get(
        f'/api/projects/{versiona_context.project.public_id}/members/'
    )

    assert response.status_code == 200
    roles = {row['email']: row['role'] for row in response.data['results']}
    assert roles[versiona_context.users['reviewer'].email] == 'reviewer'
