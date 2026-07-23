"""E3 check engine vs the contrato fixtures — evidence included."""

from pathlib import Path

import pytest

from checks.models import CheckRun
from checks.services import run_checks, summary_for
from documents.services import storage_service, version_service
from projects.services import config_service

TESTDATA = Path(__file__).resolve().parents[3] / 'testdata' / 'pdfs'

CHECKLIST = [
    {'key': 'tiene-confidencialidad', 'label': 'Cláusula de confidencialidad',
     'type': 'required_section', 'param': 'confidencialidad', 'severity': 'fail'},
    {'key': 'tiene-anticipo', 'label': 'Regula el anticipo',
     'type': 'required_text', 'param': r'anticipo', 'severity': 'fail'},
    {'key': 'tiene-poliza', 'label': 'Póliza de cumplimiento',
     'type': 'required_text', 'param': r'p[oó]liza de cumplimiento', 'severity': 'warn'},
    {'key': 'sin-dolares', 'label': 'Sin montos en dólares',
     'type': 'forbidden_text', 'param': r'USD', 'severity': 'warn'},
    {'key': 'tiene-interventoria', 'label': 'Menciona interventoría',
     'type': 'required_text', 'param': 'interventor', 'severity': 'warn'},
]


@pytest.fixture(autouse=True)
def _test_env(settings, tmp_path):
    settings.DJANGO_ENV = 'test'
    settings.SEAL_SIGNING_KEY_PATH = str(tmp_path / 'seal_key.pem')


@pytest.fixture
def checked_version(versiona_context):
    """Project with the checklist configured BEFORE uploading (I8 pins it)."""
    context = versiona_context
    config_service.update_config(
        context.project, context.users['admin'], checklist=CHECKLIST
    )
    editor = context.users['editor']
    document = version_service.create_document(context.project, 'Chequeado', editor)
    intent = version_service.create_upload_intent(document, editor)
    storage_service.put_bytes(
        intent.key, (TESTDATA / 'contrato_v1.pdf').read_bytes(), 'application/pdf'
    )
    version, _ = version_service.complete_upload(document, intent.upload_id, 'v1', editor)
    return context, version


@pytest.mark.django_db
@pytest.mark.escenario('E3-F01')
def test_checks_run_with_the_analysis_and_produce_the_truth_table(checked_version):
    _, version = checked_version

    run = CheckRun.objects.get(document_version=version)
    outcomes = {result.key: result.outcome for result in run.results.all()}
    # Truth table over the REAL fixture text: v1 regulates the anticipo and
    # mentions the interventoría; it never mentions a póliza nor USD amounts.
    assert outcomes == {
        'tiene-confidencialidad': 'pass',
        'tiene-anticipo': 'pass',
        'tiene-poliza': 'warn',
        'sin-dolares': 'pass',
        'tiene-interventoria': 'pass',
    }


@pytest.mark.django_db
@pytest.mark.escenario('E3-F02')
def test_pass_results_carry_evidence_with_section_and_snippet(checked_version):
    _, version = checked_version
    run = CheckRun.objects.get(document_version=version)

    anticipo = run.results.get(key='tiene-anticipo')

    assert anticipo.evidence['section'] == 'valor-y-forma-de-pago'
    assert 'anticipo' in anticipo.evidence['snippet'].lower()
    assert anticipo.evidence['page'] >= 1


@pytest.mark.django_db
@pytest.mark.escenario('E3-F03')
def test_summary_feeds_the_traffic_light(checked_version):
    _, version = checked_version

    assert summary_for(version) == {'pass': 4, 'warn': 1, 'fail': 0}


@pytest.mark.django_db
@pytest.mark.escenario('E3-A01')
def test_missing_required_section_fails_with_reason(versiona_context):
    context = versiona_context
    config_service.update_config(
        context.project, context.users['admin'],
        checklist=[{'key': 'garantias', 'label': 'Sección de garantías',
                    'type': 'required_section', 'param': 'garantias', 'severity': 'fail'}],
    )
    editor = context.users['editor']
    document = version_service.create_document(context.project, 'Sin garantías', editor)
    intent = version_service.create_upload_intent(document, editor)
    storage_service.put_bytes(
        intent.key, (TESTDATA / 'contrato_v1.pdf').read_bytes(), 'application/pdf'
    )
    version, _ = version_service.complete_upload(document, intent.upload_id, 'v1', editor)

    run = CheckRun.objects.get(document_version=version)
    result = run.results.get()
    assert result.outcome == 'fail'
    assert result.evidence['reason'] == 'section_missing'


@pytest.mark.django_db
@pytest.mark.escenario('E3-A02')
def test_run_checks_is_idempotent_per_version_and_config(checked_version):
    _, version = checked_version

    first = CheckRun.objects.get(document_version=version)
    second = run_checks(version)

    assert second.pk == first.pk
    assert CheckRun.objects.filter(document_version=version).count() == 1


@pytest.mark.django_db
@pytest.mark.escenario('E3-L01')
def test_empty_checklist_produces_no_run(versiona_context):
    context = versiona_context
    editor = context.users['editor']
    document = version_service.create_document(context.project, 'Sin checklist', editor)
    intent = version_service.create_upload_intent(document, editor)
    storage_service.put_bytes(
        intent.key, (TESTDATA / 'contrato_v1.pdf').read_bytes(), 'application/pdf'
    )
    version, _ = version_service.complete_upload(document, intent.upload_id, 'v1', editor)

    assert CheckRun.objects.filter(document_version=version).count() == 0
    assert summary_for(version) is None


@pytest.mark.django_db
@pytest.mark.escenario('E3-F04')
def test_checks_endpoint_returns_results_with_evidence(client_as, checked_version):
    _, version = checked_version

    response = client_as('viewer').get(f'/api/versions/{version.public_id}/checks/')

    assert response.status_code == 200
    assert response.data['summary'] == {'pass': 4, 'warn': 1, 'fail': 0}
    by_key = {row['key']: row for row in response.data['results']}
    assert by_key['tiene-anticipo']['evidence']['section'] == 'valor-y-forma-de-pago'


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('member-viewer', 200, id='e3-templates-p01-member'),
    pytest.param('anonymous', 401, id='e3-templates-p03-anonymous'),
])
@pytest.mark.escenario('E3-P01')
def test_templates_list_permission_matrix(client_as, versiona_context, actor, expected):
    alias = 'viewer' if actor == 'member-viewer' else actor
    response = client_as(alias).get(
        f'/api/orgs/{versiona_context.org.public_id}/checklist_templates/'
    )

    assert response.status_code == expected


@pytest.mark.django_db
def test_template_creation_requires_org_admin(client_as, versiona_context):
    url = f'/api/orgs/{versiona_context.org.public_id}/checklist_templates/'
    payload = {'name': 'Base', 'items': CHECKLIST[:1]}

    denied = client_as('viewer').post(url, payload, format='json')
    allowed = client_as('owner').post(url, payload, format='json')

    assert denied.status_code == 404
    assert allowed.status_code == 201
    assert allowed.data['items'][0]['key'] == 'tiene-confidencialidad'
