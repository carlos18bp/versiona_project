"""
The D5 lifecycle over the REAL fixtures (integration — MinIO + engine +
comparison + resolver + notifications):

contrato_v1 → reviewer A seals §1–2, reviewer B seals §3 (multas) → editor
uploads contrato_v2 (changes §3 and §5, removes §6, adds one, renumbers 7/8)
⇒ A's seal is PRESERVED with evidence · B's seal is INVALIDATED · ONLY B is
notified (S6). This is the queen scenario at the API level.
"""

from pathlib import Path

import pytest

from documents.services import storage_service, version_service
from notifications.models import Notification
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
def sealed_v1(versiona_context):
    """Document with v1 analyzed and two seals: A over §1–2, B over §3."""
    context = versiona_context
    editor = context.users['editor']
    reviewer_a = context.users['reviewer']
    reviewer_b = context.users['admin']  # admin can also seal (effective role)
    document = version_service.create_document(context.project, 'Contrato sellado', editor)
    v1 = upload(document, 'contrato_v1.pdf', 'v1', editor)

    seal_a = seal_service.create_seal(
        v1, reviewer_a,
        section_keys=['objeto-del-contrato', 'definiciones'],
    )
    seal_b = seal_service.create_seal(
        v1, reviewer_b,
        section_keys=['obligaciones-del-contratista'],
    )
    return context, document, v1, seal_a, seal_b


@pytest.mark.django_db
@pytest.mark.escenario('D4-F01')
def test_seal_binds_the_exact_content_hashes(sealed_v1):
    _, _, v1, seal_a, _ = sealed_v1

    payload = seal_a.signed_payload
    assert payload['version_sha256'] == v1.sha256
    assert {s['stable_key'] for s in payload['sections']} == {
        'objeto-del-contrato', 'definiciones'
    }
    from reviews.services import signing

    assert signing.verify(payload, seal_a.signature) is True


@pytest.mark.django_db
@pytest.mark.escenario('D5-F01')
def test_new_version_preserves_a_and_invalidates_b_selectively(sealed_v1):
    context, document, v1, seal_a, seal_b = sealed_v1
    editor = context.users['editor']

    upload(document, 'contrato_v2.pdf', 'v2 con cambios', editor)

    record_a = SealValidityRecord.objects.get(seal=seal_a)
    record_b = SealValidityRecord.objects.get(seal=seal_b)
    # A sealed sections that did not change: PRESERVED with hash evidence.
    assert record_a.decision == SealValidityRecord.Decision.PRESERVED
    assert {v['stable_key'] for v in record_a.evidence['verified']} == {
        'objeto-del-contrato', 'definiciones'
    }
    # B sealed §3 (multas 2%→5%): INVALIDATED with the change as evidence.
    assert record_b.decision == SealValidityRecord.Decision.INVALIDATED
    assert record_b.reason_code == 'section_modified'
    changed = {c['stable_key'] for c in record_b.evidence['changed']}
    assert changed == {'obligaciones-del-contratista'}


@pytest.mark.django_db
@pytest.mark.escenario('D5-F05')
def test_only_the_invalidated_reviewer_is_notified(sealed_v1):
    context, document, _, seal_a, seal_b = sealed_v1
    editor = context.users['editor']

    upload(document, 'contrato_v2.pdf', 'v2', editor)

    # S6: B (invalidated) gets the re-review notification…
    assert Notification.objects.filter(
        user=seal_b.reviewer, event_key='seal.invalidated'
    ).count() == 1
    # …and A (preserved) hears NOTHING about it.
    assert not Notification.objects.filter(
        user=seal_a.reviewer, event_key__in=['seal.invalidated', 'seal.preserved']
    ).exists()


@pytest.mark.django_db
@pytest.mark.escenario('D5-A05')
def test_invalidation_is_idempotent_per_version_pair(sealed_v1):
    context, document, _, seal_a, seal_b = sealed_v1
    editor = context.users['editor']
    upload(document, 'contrato_v2.pdf', 'v2', editor)
    from comparisons.models import Comparison

    comparison = Comparison.objects.get(trigger=Comparison.Trigger.AUTO)

    seal_service.apply_invalidation(comparison)  # re-run (I15)

    assert SealValidityRecord.objects.filter(seal=seal_b).count() == 1
    assert Notification.objects.filter(
        user=seal_b.reviewer, event_key='seal.invalidated'
    ).count() == 1


@pytest.mark.django_db
@pytest.mark.escenario('D5-F06')
def test_validity_chain_i11_across_versions(sealed_v1):
    context, document, v1, seal_a, seal_b = sealed_v1
    editor = context.users['editor']

    v2 = upload(document, 'contrato_v2.pdf', 'v2', editor)

    assert seal_service.seal_is_valid_at(seal_a, v1) is True
    assert seal_service.seal_is_valid_at(seal_a, v2) is True  # preserved chain
    assert seal_service.seal_is_valid_at(seal_b, v1) is True  # valid where signed
    assert seal_service.seal_is_valid_at(seal_b, v2) is False  # chain cut


@pytest.mark.django_db
@pytest.mark.escenario('D4-A01')
@pytest.mark.escenario('D4-A02')
def test_seal_can_be_withdrawn_before_approval_but_not_after(sealed_v1):
    context, document, v1, seal_a, _ = sealed_v1
    from documents.models import DocumentVersion

    seal_service.revoke_seal(seal_a, seal_a.reviewer)
    assert Seal.objects.get(pk=seal_a.pk).revoked_at is not None

    # Approve the version → the remaining seal becomes immutable (I5).
    DocumentVersion.all_objects.filter(pk=v1.pk).update(is_approved=True)
    v1.refresh_from_db()
    remaining = Seal.objects.filter(document_version=v1, revoked_at__isnull=True).first()
    with pytest.raises(version_service.DomainError) as exc:
        seal_service.revoke_seal(remaining, remaining.reviewer)
    assert exc.value.status_code == 409


@pytest.mark.django_db
@pytest.mark.escenario('D4-F02')
def test_full_coverage_seal_approves_the_version_and_freezes_it(versiona_context):
    """I10 + I5: a covers_all seal under the MVP policy approves the version;
    approval freezes the draft (message no longer editable — I2b)."""
    context = versiona_context
    editor = context.users['editor']
    reviewer = context.users['reviewer']
    document = version_service.create_document(context.project, 'Aprobable', editor)
    v1 = upload(document, 'contrato_v1.pdf', 'v1', editor)

    seal_service.create_seal(v1, reviewer, covers_all=True)

    v1.refresh_from_db()
    assert v1.is_approved is True
    assert v1.is_draft is False
    with pytest.raises(version_service.DomainError):
        version_service.edit_message(v1, 'tarde: ya está aprobada', editor)
    # The author was told the version got approved.
    assert Notification.objects.filter(
        user=editor, event_key='version.approved'
    ).exists()


@pytest.mark.django_db
@pytest.mark.escenario('C4-E01')
def test_sealed_version_is_not_trash_eligible(sealed_v1):
    """I3 reinforced: a version with seals can never go to the trash."""
    context, document, v1, _, _ = sealed_v1
    from documents.services import trash_service

    with pytest.raises(version_service.DomainError):
        trash_service.trash_version(v1, context.users['editor'])
