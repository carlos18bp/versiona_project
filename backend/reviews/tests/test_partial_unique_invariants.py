"""I4 + D1 at the database layer: one ACTIVE seal per (version, reviewer), and
one OPEN request per version.

Both were partial unique indexes on PostgreSQL. MySQL 8 has none, and Django
skips a conditional UniqueConstraint there WITHOUT failing — `migrate` would
have gone green with I4 unenforced. The condition now lives in the generated
columns `Seal.document_version_active` and
`ReviewRequest.document_version_open`, and these tests are what proves it.
"""

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from reviews.models import ReviewRequest, Seal


def make_seal(version, reviewer, **overrides):
    return Seal.objects.create(
        document_version=version,
        reviewer=reviewer,
        covers_all=True,
        signed_payload={'v': 1},
        signature='c2lnbmF0dXJl',
        key_id='deadbeefdeadbeef',
        **overrides,
    )


@pytest.mark.django_db
def test_a_reviewer_cannot_hold_two_active_seals_on_one_version(
    versiona_context, document_with_versions
):
    """I4: the seal is the act of review, and it happens once."""
    _, versions = document_with_versions()
    reviewer = versiona_context.users['reviewer']
    make_seal(versions[0], reviewer)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_seal(versions[0], reviewer)


@pytest.mark.django_db
def test_revoking_a_seal_lets_the_reviewer_seal_again(
    versiona_context, document_with_versions
):
    """DP-08: withdrawing is an append event, and it reopens the slot."""
    _, versions = document_with_versions()
    reviewer = versiona_context.users['reviewer']
    original = make_seal(versions[0], reviewer)

    original.revoked_at = timezone.now()
    original.save(update_fields=['revoked_at'])
    resealed = make_seal(versions[0], reviewer)

    assert resealed.pk != original.pk


@pytest.mark.django_db
def test_two_reviewers_can_seal_the_same_version(versiona_context, document_with_versions):
    _, versions = document_with_versions()
    make_seal(versions[0], versiona_context.users['reviewer'])

    second = make_seal(versions[0], versiona_context.users['admin'])

    assert second.reviewer == versiona_context.users['admin']


@pytest.mark.django_db
def test_a_version_cannot_have_two_open_review_requests(
    versiona_context, document_with_versions
):
    _, versions = document_with_versions()
    requester = versiona_context.users['editor']
    ReviewRequest.objects.create(document_version=versions[0], requested_by=requester)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ReviewRequest.objects.create(document_version=versions[0], requested_by=requester)


@pytest.mark.django_db
def test_closing_a_request_lets_a_new_one_open(versiona_context, document_with_versions):
    _, versions = document_with_versions()
    requester = versiona_context.users['editor']
    original = ReviewRequest.objects.create(
        document_version=versions[0], requested_by=requester
    )

    original.status = ReviewRequest.Status.COMPLETED
    original.save(update_fields=['status'])
    reopened = ReviewRequest.objects.create(
        document_version=versions[0], requested_by=requester
    )

    assert reopened.pk != original.pk
