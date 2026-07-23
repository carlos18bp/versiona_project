"""E4: the exportable certificate — fresh proof, not a copy of claims."""

from pathlib import Path

import pytest

from documents.services import storage_service, version_service
from documents.services.version_service import DomainError
from reviews.models import Certificate
from reviews.services import seal_service
from reviews.services.certificate_service import issue_certificate

TESTDATA = Path(__file__).resolve().parents[3] / 'testdata' / 'pdfs'


@pytest.fixture(autouse=True)
def _test_env(settings, tmp_path):
    settings.DJANGO_ENV = 'test'
    settings.SEAL_SIGNING_KEY_PATH = str(tmp_path / 'seal_key.pem')


@pytest.fixture
def approved_version(versiona_context):
    editor = versiona_context.users['editor']
    document = version_service.create_document(
        versiona_context.project, 'Certificable', editor
    )
    intent = version_service.create_upload_intent(document, editor)
    storage_service.put_bytes(
        intent.key, (TESTDATA / 'contrato_v1.pdf').read_bytes(), 'application/pdf'
    )
    version, _ = version_service.complete_upload(document, intent.upload_id, 'v1', editor)
    seal_service.create_seal(version, versiona_context.users['reviewer'], covers_all=True)
    version.refresh_from_db()
    assert version.is_approved
    return versiona_context, version


@pytest.mark.django_db
@pytest.mark.escenario('E4-F01')
def test_certificate_pdf_is_real_and_stored(approved_version):
    context, version = approved_version

    certificate = issue_certificate(version, context.users['admin'])

    pdf = storage_service.get_bytes(certificate.pdf_key)
    assert pdf.startswith(b'%PDF')
    assert certificate.serial.endswith('-0001')
    assert context.org.slug.upper()[:12] in certificate.serial


@pytest.mark.django_db
@pytest.mark.escenario('E4-F02')
def test_snapshot_carries_everything_for_offline_verification(approved_version):
    """T6: payloads + signatures + public key + hashes — self-contained."""
    from reviews.services import signing

    context, version = approved_version
    certificate = issue_certificate(version, context.users['admin'])
    snapshot = certificate.snapshot

    assert snapshot['version_sha256'] == version.sha256
    assert snapshot['public_key'] == signing.public_key_b64()
    seal_row = snapshot['seals'][0]
    assert seal_row['signature_valid_now'] is True
    # The snapshot alone verifies offline:
    assert signing.verify(
        seal_row['payload'], seal_row['signature'], snapshot['public_key']
    ) is True


@pytest.mark.django_db
@pytest.mark.escenario('E4-E01')
def test_unapproved_version_cannot_be_certified(versiona_context, document_with_versions):
    document, versions = document_with_versions(n_versions=1)

    with pytest.raises(DomainError) as exc:
        issue_certificate(versions[0], versiona_context.users['admin'])

    assert 'APROBADA' in str(exc.value)


@pytest.mark.django_db
@pytest.mark.escenario('E4-E02')
def test_tampered_signature_blocks_issuance(approved_version):
    """The re-verification is REAL: corrupt a stored signature and the
    certificate refuses to exist."""
    from reviews.models import Seal

    context, version = approved_version
    seal = Seal.objects.get(document_version=version)
    Seal.objects.filter(pk=seal.pk).update(signature='QUFBQQ==')

    with pytest.raises(DomainError) as exc:
        issue_certificate(version, context.users['admin'])

    assert 'no verifican' in str(exc.value)
    assert Certificate.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.escenario('E4-F03')
def test_serials_increment_per_org_and_year(approved_version):
    context, version = approved_version

    first = issue_certificate(version, context.users['admin'])
    second = issue_certificate(version, context.users['admin'])

    assert first.serial.endswith('-0001')
    assert second.serial.endswith('-0002')
    assert first.pdf_key != second.pdf_key  # never overwritten


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('admin', 201, id='e4-p01-admin'),
    pytest.param('reviewer', 404, id='e4-p02-reviewer-hidden'),
    pytest.param('anonymous', 401, id='e4-p03-anonymous'),
    pytest.param('non_member', 404, id='e4-p04-non-member'),
])
@pytest.mark.escenario('E4-P01')
def test_issue_permission_matrix(client_as, approved_version, actor, expected):
    _, version = approved_version

    response = client_as(actor).post(f'/api/versions/{version.public_id}/certificates/')

    assert response.status_code == expected


@pytest.fixture
def two_issuances(approved_version):
    context, version = approved_version
    first = issue_certificate(version, context.users['admin'])
    second = issue_certificate(version, context.users['admin'])
    return context, version, first, second


@pytest.mark.django_db
@pytest.mark.escenario('E4-A01')
def test_listing_returns_every_previous_issuance_newest_first(client_as, two_issuances):
    context, version, first, second = two_issuances

    response = client_as('viewer').get(f'/api/versions/{version.public_id}/certificates/')

    assert response.status_code == 200
    assert [row['serial'] for row in response.data['results']] == [
        second.serial, first.serial
    ]


@pytest.mark.django_db
@pytest.mark.escenario('E4-A01')
def test_listed_serials_follow_the_org_year_sequence_format(client_as, two_issuances):
    context, version, first, second = two_issuances
    prefix = f'{context.org.slug.upper()[:12]}-{first.created_at.year}'

    response = client_as('viewer').get(f'/api/versions/{version.public_id}/certificates/')

    assert [row['serial'] for row in response.data['results']] == [
        f'{prefix}-0002', f'{prefix}-0001'
    ]


@pytest.mark.django_db
@pytest.mark.escenario('E4-A01')
def test_listing_carries_the_issue_date_of_each_certificate(client_as, two_issuances):
    context, version, first, second = two_issuances

    response = client_as('viewer').get(f'/api/versions/{version.public_id}/certificates/')

    assert [row['created_at'] for row in response.data['results']] == [
        second.created_at, first.created_at
    ]


@pytest.mark.django_db
@pytest.mark.escenario('E4-A01')
def test_listing_names_the_issuer_of_each_certificate(client_as, two_issuances):
    context, version, first, second = two_issuances

    response = client_as('viewer').get(f'/api/versions/{version.public_id}/certificates/')

    assert {row['issued_by'] for row in response.data['results']} == {
        context.users['admin'].email
    }


@pytest.mark.django_db
@pytest.mark.escenario('E4-F04')
def test_download_endpoint_returns_signed_url_and_snapshot(client_as, approved_version):
    context, version = approved_version
    certificate = issue_certificate(version, context.users['admin'])

    response = client_as('viewer').get(
        f'/api/versions/{version.public_id}/certificates/{certificate.public_id}/download/'
    )

    assert response.status_code == 200
    assert 'X-Amz-Signature' in response.data['url']
    assert response.data['snapshot']['serial'] == certificate.serial
