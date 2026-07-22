"""It8 hardening: the OCR queen (D5-A03) and the EXTERNAL certificate verifier."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from documents.services import storage_service, version_service
from reviews.models import SealValidityRecord
from reviews.services import seal_service
from reviews.services.certificate_service import issue_certificate

TESTDATA = Path(__file__).resolve().parents[3] / 'testdata' / 'pdfs'
VERIFIER = Path(__file__).resolve().parents[3] / 'scripts' / 'verify_certificate.py'


@pytest.fixture(autouse=True)
def _test_env(settings, tmp_path):
    settings.DJANGO_ENV = 'test'
    settings.SEAL_SIGNING_KEY_PATH = str(tmp_path / 'seal_key.pem')


def upload(document, fixture, message, author):
    intent = version_service.create_upload_intent(document, author)
    storage_service.put_bytes(intent.key, (TESTDATA / fixture).read_bytes(), 'application/pdf')
    version, _ = version_service.complete_upload(document, intent.upload_id, message, author)
    return version


@pytest.mark.django_db
@pytest.mark.escenario('D5-A03')
def test_queen_over_a_scanned_document_forces_the_coordinator(versiona_context):
    """The OCR queen: a seal over a SCANNED v1 (source_scenario scanned_ocr)
    never resolves automatically — any next version leaves the decision to a
    human, no matter how clean the diff looks (DP-03/DP-09)."""
    context = versiona_context
    editor = context.users['editor']
    document = version_service.create_document(context.project, 'Escaneado sellado', editor)
    v1 = upload(document, 'escaneado_v1.pdf', 'v1 escaneada', editor)
    assert v1.source_scenario == 'scanned_ocr'

    # The OCR recovered real sections: seal one of them.
    seal = seal_service.create_seal(
        v1, context.users['reviewer'], section_keys=['objeto-del-contrato']
    )

    upload(document, 'contrato_v2.pdf', 'v2 nativa', editor)

    record = SealValidityRecord.objects.get(seal=seal)
    assert record.decision == SealValidityRecord.Decision.PENDING
    assert record.decided_mode == SealValidityRecord.Mode.COORDINATOR
    # The engine still PROPOSES with full evidence for the human.
    assert record.proposed_decision in (
        SealValidityRecord.Decision.PRESERVED, SealValidityRecord.Decision.INVALIDATED
    )


@pytest.mark.django_db
@pytest.mark.escenario('E4-F05')
def test_external_verifier_validates_a_real_certificate(versiona_context, tmp_path):
    """T6 made runnable: scripts/verify_certificate.py verifies the snapshot
    with NOTHING but `cryptography` — no Versiona imports, no server."""
    context = versiona_context
    editor = context.users['editor']
    document = version_service.create_document(context.project, 'Verificable', editor)
    version = upload(document, 'contrato_v1.pdf', 'v1', editor)
    seal_service.create_seal(version, context.users['reviewer'], covers_all=True)
    version.refresh_from_db()
    certificate = issue_certificate(version, context.users['admin'])

    snapshot_file = tmp_path / 'snapshot.json'
    snapshot_file.write_text(json.dumps(certificate.snapshot))

    result = subprocess.run(
        [sys.executable, str(VERIFIER), str(snapshot_file)],
        capture_output=True, text=True, timeout=60,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert 'TODAS LAS FIRMAS VERIFICAN' in result.stdout


@pytest.mark.django_db
@pytest.mark.escenario('E4-E03')
def test_external_verifier_rejects_a_tampered_snapshot(versiona_context, tmp_path):
    context = versiona_context
    editor = context.users['editor']
    document = version_service.create_document(context.project, 'Adulterado', editor)
    version = upload(document, 'contrato_v1.pdf', 'v1', editor)
    seal_service.create_seal(version, context.users['reviewer'], covers_all=True)
    version.refresh_from_db()
    certificate = issue_certificate(version, context.users['admin'])

    snapshot = certificate.snapshot
    snapshot['seals'][0]['payload']['version_sha256'] = '0' * 64  # tamper

    snapshot_file = tmp_path / 'tampered.json'
    snapshot_file.write_text(json.dumps(snapshot))

    result = subprocess.run(
        [sys.executable, str(VERIFIER), str(snapshot_file)],
        capture_output=True, text=True, timeout=60,
    )

    assert result.returncode == 1
    assert 'NO VERIFICAN' in result.stdout
