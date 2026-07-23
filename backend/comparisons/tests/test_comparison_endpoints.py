"""Comparison endpoints: cache, permissions matrix and error paths (E1)."""

from pathlib import Path

import pytest

from comparisons.models import Comparison
from documents.services import storage_service, version_service

TESTDATA = Path(__file__).resolve().parents[3] / 'testdata' / 'pdfs'


@pytest.fixture(autouse=True)
def _test_storage_prefix(settings):
    settings.DJANGO_ENV = 'test'


@pytest.fixture
def analyzed_document(versiona_context):
    """Document with v1 (contrato_v1) and v2 (contrato_v2) fully analyzed."""
    editor = versiona_context.users['editor']
    document = version_service.create_document(versiona_context.project, 'Contrato', editor)
    versions = []
    for fixture, message in (('contrato_v1.pdf', 'v1'), ('contrato_v2.pdf', 'v2')):
        intent = version_service.create_upload_intent(document, editor)
        storage_service.put_bytes(
            intent.key, (TESTDATA / fixture).read_bytes(), 'application/pdf'
        )
        version, _ = version_service.complete_upload(document, intent.upload_id, message, editor)
        versions.append(version)
    return document, versions


def compare_url(document):
    return f'/api/documents/{document.public_id}/comparisons/'


@pytest.mark.django_db
@pytest.mark.escenario('C2-F01')
def test_auto_comparison_runs_after_the_second_upload(analyzed_document):
    document, versions = analyzed_document

    auto = Comparison.objects.get(
        from_version=versions[0], to_version=versions[1], trigger=Comparison.Trigger.AUTO
    )

    assert auto.status == Comparison.Status.DONE
    counts = auto.summary['counts']
    # Truth table (testdata/README): 3 and 5 modified, 6 removed, new section
    # added; the rest (incl. the contract title block) unchanged.
    assert counts['modified'] == 2
    assert counts['removed'] == 1
    assert counts['added'] == 1
    assert counts['renamed_only'] == 0
    assert auto.summary['text'] == '2 modificadas, 1 eliminada, 1 agregada'


@pytest.mark.django_db
@pytest.mark.escenario('E1-F01')
def test_compare_two_versions_returns_the_truth_table(client_as, analyzed_document):
    document, versions = analyzed_document

    response = client_as('viewer').post(
        compare_url(document),
        {'from_version': str(versions[0].public_id), 'to_version': str(versions[1].public_id)},
        format='json',
    )

    assert response.status_code == 200  # already cached by the auto comparison
    changes = {row['stable_key']: row['change_type'] for row in response.data['section_changes']}
    assert changes['obligaciones-del-contratista'] == 'modified'
    assert changes['valor-y-forma-de-pago'] == 'modified'
    assert changes['plazo-de-ejecucion'] == 'removed'
    assert changes['proteccion-de-datos-personales'] == 'added'
    assert changes['confidencialidad'] == 'unchanged'
    assert response.data['has_changes'] is True


@pytest.mark.django_db
@pytest.mark.escenario('E1-A02')
def test_second_request_for_the_same_pair_is_served_from_cache(client_as, analyzed_document):
    document, versions = analyzed_document
    payload = {
        'from_version': str(versions[0].public_id), 'to_version': str(versions[1].public_id)
    }
    client = client_as('editor')
    first = client.post(compare_url(document), payload, format='json')

    second = client.post(compare_url(document), payload, format='json')

    assert first.data['public_id'] == second.data['public_id']
    assert Comparison.objects.filter(
        from_version=versions[0], to_version=versions[1]
    ).count() == 1


@pytest.mark.django_db
@pytest.mark.escenario('E1-F02')
def test_section_diff_endpoint_returns_word_level_ops(client_as, analyzed_document):
    document, versions = analyzed_document
    comparison = Comparison.objects.get(from_version=versions[0], to_version=versions[1])

    response = client_as('viewer').get(
        f'/api/comparisons/{comparison.public_id}/sections/obligaciones-del-contratista/diff/'
    )

    assert response.status_code == 200
    ops = {op['op'] for op in response.data['word_diff']}
    assert {'equal', 'insert', 'delete'} <= ops
    assert response.data['bboxes_to']


@pytest.mark.django_db
@pytest.mark.escenario('E1-E01')
def test_compare_with_the_same_version_twice_is_rejected(client_as, analyzed_document):
    document, versions = analyzed_document

    response = client_as('editor').post(
        compare_url(document),
        {'from_version': str(versions[0].public_id), 'to_version': str(versions[0].public_id)},
        format='json',
    )

    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.escenario('E1-E01')
def test_compare_against_a_failed_version_is_rejected(client_as, analyzed_document):
    from documents.models import DocumentVersion

    document, versions = analyzed_document
    DocumentVersion.all_objects.filter(pk=versions[1].pk).update(analysis_status='failed')

    response = client_as('editor').post(
        compare_url(document),
        {'from_version': str(versions[0].public_id), 'to_version': str(versions[1].public_id)},
        format='json',
    )

    assert response.status_code == 409


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('viewer', 200, id='e1-p01-viewer'),
    pytest.param('editor', 200, id='e1-p01-editor'),
    pytest.param('anonymous', 401, id='e1-p03-anonymous'),
    pytest.param('non_member', 404, id='e1-p04-non-member'),
])
@pytest.mark.escenario('E1-P01')
def test_compare_permission_matrix(client_as, analyzed_document, actor, expected):
    document, versions = analyzed_document

    response = client_as(actor).post(
        compare_url(document),
        {'from_version': str(versions[0].public_id), 'to_version': str(versions[1].public_id)},
        format='json',
    )

    assert response.status_code == expected


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('viewer', 200, id='e1-detail-p01-viewer'),
    pytest.param('anonymous', 401, id='e1-detail-p03-anonymous'),
    pytest.param('non_member', 404, id='e1-detail-p04-non-member'),
])
def test_comparison_detail_permission_matrix(client_as, analyzed_document, actor, expected):
    document, versions = analyzed_document
    comparison = Comparison.objects.get(from_version=versions[0], to_version=versions[1])

    response = client_as(actor).get(f'/api/comparisons/{comparison.public_id}/')

    assert response.status_code == expected
