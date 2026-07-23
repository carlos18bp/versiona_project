"""D5-L01: the document loses ALL its sections (a headless re-delivery falls
back to page sections, so every previous stable key disappears). The
conservative bias (I7) must invalidate every seal — no path from "not
hash-equal" to preserved. The remaining requirements of the row (forced
coordinator confirmation, non-sealable structural red) are pinned as negative
verifications of what the code does today."""

from pathlib import Path

import pytest

from documents.models import DocumentVersion
from documents.services import storage_service, version_service
from reviews.models import Seal, SealValidityRecord
from reviews.services import seal_service

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
def total_section_loss(versiona_context):
    """v1 = contrato_v1 with a scoped seal and a covers_all seal; v2 = headless
    prose, which retires every section of v1."""
    context = versiona_context
    editor = context.users['editor']
    document = version_service.create_document(context.project, 'Sin secciones', editor)
    v1 = upload(document, 'contrato_v1.pdf', 'v1', editor)
    scoped = seal_service.create_seal(
        v1, context.users['reviewer'],
        section_keys=['objeto-del-contrato', 'definiciones'],
    )
    whole = seal_service.create_seal(v1, context.users['admin'], covers_all=True)
    v2 = upload(document, 'sin_encabezados.pdf', 'v2 sin encabezados', editor)
    return context, document, v1, v2, scoped, whole


@pytest.mark.django_db
@pytest.mark.escenario('D5-L01')
def test_the_new_version_keeps_none_of_the_previous_stable_keys(total_section_loss):
    _, document, v1, v2, _, _ = total_section_loss

    keys_v1 = set(
        v1.section_versions.values_list('section__stable_key', flat=True)
    )
    keys_v2 = set(
        v2.section_versions.values_list('section__stable_key', flat=True)
    )
    assert keys_v1.isdisjoint(keys_v2)


@pytest.mark.django_db
@pytest.mark.escenario('D5-L01')
def test_every_seal_is_invalidated_when_all_sections_disappear(total_section_loss):
    _, _, _, v2, _, _ = total_section_loss

    decisions = set(
        SealValidityRecord.objects.filter(to_document_version=v2)
        .values_list('decision', flat=True)
    )
    assert decisions == {SealValidityRecord.Decision.INVALIDATED}


@pytest.mark.django_db
@pytest.mark.escenario('D5-L01')
def test_the_scoped_seal_is_invalidated_because_its_sections_were_removed(total_section_loss):
    _, _, _, v2, scoped, _ = total_section_loss

    record = SealValidityRecord.objects.get(seal=scoped, to_document_version=v2)

    assert record.reason_code == 'section_removed'


@pytest.mark.django_db
@pytest.mark.escenario('D5-L01')
def test_the_covers_all_seal_is_invalidated_because_the_document_changed(total_section_loss):
    _, _, _, v2, _, whole = total_section_loss

    record = SealValidityRecord.objects.get(seal=whole, to_document_version=v2)

    assert record.reason_code == 'document_changed'


@pytest.mark.django_db
@pytest.mark.escenario('D5-L01')
def test_no_seal_of_the_previous_version_stays_valid_at_the_new_one(total_section_loss):
    _, _, _, v2, scoped, _ = total_section_loss

    assert seal_service.seal_is_valid_at(scoped, v2) is False


@pytest.mark.django_db
@pytest.mark.escenario('D5-L01')
def test_degraded_page_fallback_does_not_force_coordinator_confirmation(total_section_loss):
    """Negative verification: DP-09 asks for a forced coordinator plan when the
    analysis is degraded, but `degraded` is never persisted on the version and
    the forcing rule only looks at `source_scenario`."""
    _, _, _, v2, _, _ = total_section_loss

    assert v2.source_scenario == DocumentVersion.Scenario.TEXT_NATIVE


@pytest.mark.django_db
@pytest.mark.escenario('D5-L01')
def test_the_invalidation_plan_is_decided_in_auto_mode(total_section_loss):
    _, _, _, v2, scoped, _ = total_section_loss

    record = SealValidityRecord.objects.get(seal=scoped, to_document_version=v2)

    assert record.decided_mode == SealValidityRecord.Mode.AUTO


@pytest.mark.django_db
@pytest.mark.escenario('D5-L01')
def test_a_version_that_lost_every_section_can_still_be_sealed(total_section_loss):
    """Negative verification: the row demands a non-sealable structural red;
    no such guard exists, so a whole-document seal is accepted."""
    context, _, _, v2, _, _ = total_section_loss

    seal = seal_service.create_seal(v2, context.users['viewer'], covers_all=True)

    assert Seal.objects.filter(pk=seal.pk, document_version=v2).exists()
