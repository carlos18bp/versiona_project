"""A2: (project, email) is unique among PENDING invitations only.

PostgreSQL expressed this as a partial unique index. MySQL 8 has none, so the
condition lives in the generated column `email_pending`, NULL once the
invitation is accepted or revoked. These tests assert the outcome, so a future
engine change cannot drop the rule silently.
"""

from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from orgs.models import Invitation


def make_invitation(context, email='invitada@externa.co', **overrides):
    return Invitation.objects.create(
        organization=context.org,
        project=context.project,
        email=email,
        role='reviewer',
        token=overrides.pop('token', 'tok-' + email),
        invited_by=context.users['admin'],
        expires_at=timezone.now() + timedelta(days=7),
        **overrides,
    )


@pytest.mark.django_db
def test_two_pending_invitations_cannot_share_an_email(versiona_context):
    make_invitation(versiona_context, token='tok-primera')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            make_invitation(versiona_context, token='tok-segunda')


@pytest.mark.django_db
def test_revoking_an_invitation_frees_the_email(versiona_context):
    original = make_invitation(versiona_context, token='tok-primera')

    original.status = Invitation.Status.REVOKED
    original.save(update_fields=['status'])
    reissued = make_invitation(versiona_context, token='tok-segunda')

    assert reissued.pk != original.pk


@pytest.mark.django_db
def test_accepting_an_invitation_frees_the_email(versiona_context):
    original = make_invitation(versiona_context, token='tok-primera')

    original.status = Invitation.Status.ACCEPTED
    original.save(update_fields=['status'])
    reissued = make_invitation(versiona_context, token='tok-segunda')

    assert reissued.pk != original.pk
