"""A2: invitations — email, token, exact-email accept, landing, revoke."""

from datetime import timedelta

import pytest
from django.utils import timezone

from documents.services.version_service import DomainError
from orgs.invitations import accept_invitation, create_invitation, revoke_invitation
from orgs.models import Invitation, OrganizationMembership
from projects.models import ProjectMembership


@pytest.mark.django_db
@pytest.mark.escenario('A2-F01')
def test_invitation_sends_the_email_with_the_token_link(versiona_context, mailoutbox):
    context = versiona_context

    invitation = create_invitation(
        context.project, context.users['admin'],
        email='invitada@externa.co', role='reviewer',
    )

    assert invitation.status == Invitation.Status.PENDING
    assert len(mailoutbox) == 1
    assert 'invitada@externa.co' in mailoutbox[0].to
    assert f'/invite/{invitation.token}' in mailoutbox[0].body
    assert 'reviewer' in mailoutbox[0].body


@pytest.mark.django_db
@pytest.mark.escenario('A2-F02')
@pytest.mark.escenario('A2-A01')
def test_accepting_creates_memberships_and_lands_on_the_project(
    versiona_context, django_user_model
):
    context = versiona_context
    invitation = create_invitation(
        context.project, context.users['admin'],
        email='invitada@externa.co', role='editor',
    )
    invitee = django_user_model.objects.create_user(
        email='invitada@externa.co', password='secreta123'
    )

    result = accept_invitation(invitation.token, invitee)

    assert result['landing'] == f'/projects/{context.project.public_id}'
    assert OrganizationMembership.objects.filter(
        organization=context.org, user=invitee
    ).exists()
    membership = ProjectMembership.objects.get(project=context.project, user=invitee)
    assert membership.role == 'editor'
    invitation.refresh_from_db()
    assert invitation.status == Invitation.Status.ACCEPTED


@pytest.mark.django_db
@pytest.mark.escenario('A2-E01')
def test_accept_requires_the_exact_invited_email(versiona_context, django_user_model):
    context = versiona_context
    invitation = create_invitation(
        context.project, context.users['admin'],
        email='invitada@externa.co', role='viewer',
    )
    impostor = django_user_model.objects.create_user(
        email='otra@externa.co', password='secreta123'
    )

    with pytest.raises(DomainError) as exc:
        accept_invitation(invitation.token, impostor)

    assert exc.value.status_code == 403
    assert 'invitada@externa.co' in str(exc.value)


@pytest.mark.django_db
@pytest.mark.escenario('A2-E02')
@pytest.mark.escenario('A2-A03')
def test_expired_and_revoked_invitations_cannot_be_accepted(
    versiona_context, django_user_model
):
    context = versiona_context
    invitee = django_user_model.objects.create_user(
        email='invitada@externa.co', password='secreta123'
    )
    expired = create_invitation(
        context.project, context.users['admin'], email='invitada@externa.co', role='viewer'
    )
    Invitation.objects.filter(pk=expired.pk).update(
        expires_at=timezone.now() - timedelta(days=1)
    )
    with pytest.raises(DomainError) as expired_error:
        accept_invitation(expired.token, invitee)
    assert 'venció' in str(expired_error.value)

    Invitation.objects.filter(pk=expired.pk).update(
        expires_at=timezone.now() + timedelta(days=1)
    )
    expired.refresh_from_db()
    revoke_invitation(expired, context.users['admin'])
    with pytest.raises(DomainError) as revoked_error:
        accept_invitation(expired.token, invitee)
    assert 'revocada' in str(revoked_error.value)


@pytest.mark.django_db
@pytest.mark.escenario('A2-E03')
def test_duplicate_pending_or_existing_member_is_rejected(versiona_context):
    context = versiona_context
    create_invitation(
        context.project, context.users['admin'], email='dup@externa.co', role='viewer'
    )

    with pytest.raises(DomainError):
        create_invitation(
            context.project, context.users['admin'], email='dup@externa.co', role='editor'
        )
    with pytest.raises(DomainError) as member_error:
        create_invitation(
            context.project, context.users['admin'],
            email=context.users['editor'].email, role='viewer',
        )
    assert 'ya es miembro' in str(member_error.value)


@pytest.mark.django_db
@pytest.mark.escenario('A2-F03')
def test_public_state_endpoint_shows_the_landing_info(client_as, versiona_context):
    context = versiona_context
    invitation = create_invitation(
        context.project, context.users['admin'],
        email='invitada@externa.co', role='reviewer',
    )

    response = client_as('anonymous').get(f'/api/invitations/{invitation.token}/')

    assert response.status_code == 200
    assert response.data['project_name'] == 'Torre Central'
    assert response.data['role'] == 'reviewer'
    assert response.data['status'] == 'pending'


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('admin', 201, id='a2-p01-admin'),
    pytest.param('editor', 403, id='a2-p02-editor-denied'),
    pytest.param('anonymous', 401, id='a2-p03-anonymous'),
    pytest.param('non_member', 404, id='a2-p04-non-member'),
])
@pytest.mark.escenario('A2-P01')
@pytest.mark.escenario('A2-P02')
def test_invite_permission_matrix(client_as, versiona_context, actor, expected):
    response = client_as(actor).post(
        f'/api/projects/{versiona_context.project.public_id}/invitations/',
        {'email': 'x@externa.co', 'role': 'viewer'},
        format='json',
    )

    assert response.status_code == expected
