"""Notification center + preferences endpoints (kit 5)."""

import pytest

from notifications.models import Notification, NotificationPreference
from notifications.services import notify


@pytest.fixture
def inbox(versiona_context):
    context = versiona_context
    user = context.users['reviewer']
    for index in range(3):
        notify(
            user=user, event_key='seal.invalidated', org=context.org,
            project=context.project, title=f'Re-revisión {index}',
            body='Cambió lo que sellaste', link='/inbox',
        )
    return context, user


@pytest.mark.django_db
@pytest.mark.escenario('NTF-F01')
def test_my_notifications_lists_with_unread_count(client_as, inbox):
    response = client_as('reviewer').get('/api/me/notifications/')

    assert response.status_code == 200
    assert response.data['unread'] == 3
    assert len(response.data['results']) == 3


@pytest.mark.django_db
def test_notifications_are_scoped_to_the_requesting_user(client_as, inbox):
    response = client_as('editor').get('/api/me/notifications/')

    assert response.data['unread'] == 0
    assert response.data['results'] == []


@pytest.mark.django_db
@pytest.mark.escenario('NTF-F02')
def test_mark_one_and_all_as_read(client_as, inbox):
    context, user = inbox
    client = client_as('reviewer')
    first = Notification.objects.filter(user=user).first()

    single = client.post(f'/api/me/notifications/{first.public_id}/read/')
    assert single.status_code == 200
    assert single.data['read_at'] is not None

    bulk = client.post('/api/me/notifications/read_all/')
    assert bulk.data['marked'] == 2
    assert Notification.objects.filter(user=user, read_at__isnull=True).count() == 0


@pytest.mark.django_db
def test_reading_a_foreign_notification_is_404(client_as, inbox):
    context, user = inbox
    foreign = Notification.objects.filter(user=user).first()

    response = client_as('editor').post(f'/api/me/notifications/{foreign.public_id}/read/')

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.escenario('NTF-F03')
def test_preferences_merge_catalog_defaults_with_overrides(client_as, versiona_context):
    client = client_as('reviewer')

    response = client.get('/api/me/notification_preferences/')

    prefs = {p['event_key']: p for p in response.data['preferences']}
    # S6 by default: preserved is OFF on both channels.
    assert prefs['seal.preserved']['in_app'] is False
    assert prefs['seal.preserved']['email'] is False
    assert prefs['seal.invalidated']['mandatory_in_app'] is True


@pytest.mark.django_db
@pytest.mark.escenario('NTF-A01')
def test_user_can_opt_into_preserved_notifications(client_as, versiona_context):
    client = client_as('reviewer')

    response = client.patch(
        '/api/me/notification_preferences/',
        {'seal.preserved': {'in_app': True}},
        format='json',
    )

    assert response.status_code == 200
    prefs = {p['event_key']: p for p in response.data['preferences']}
    assert prefs['seal.preserved']['in_app'] is True
    assert NotificationPreference.objects.filter(
        user=versiona_context.users['reviewer'], event_key='seal.preserved'
    ).exists()


@pytest.mark.django_db
@pytest.mark.escenario('NTF-E01')
def test_mandatory_in_app_events_cannot_be_silenced(client_as, versiona_context):
    response = client_as('reviewer').patch(
        '/api/me/notification_preferences/',
        {'seal.invalidated': {'in_app': False}},
        format='json',
    )

    assert response.status_code == 400
    assert 'trabajo asignado' in response.data['error']


@pytest.mark.django_db
def test_anonymous_gets_401_on_the_center(client_as):
    assert client_as('anonymous').get('/api/me/notifications/').status_code == 401


@pytest.mark.django_db
def test_email_preference_controls_delivery(versiona_context, mailoutbox):
    """Catalog default sends email for seal.invalidated; opting out stops it."""
    context = versiona_context
    user = context.users['reviewer']
    notify(user=user, event_key='seal.invalidated', org=context.org,
           title='Con email', body='x')
    assert len(mailoutbox) == 1

    NotificationPreference.objects.create(
        user=user, event_key='seal.invalidated',
        channel=NotificationPreference.Channel.EMAIL, enabled=False,
    )
    notify(user=user, event_key='seal.invalidated', org=context.org,
           title='Sin email', body='x')

    assert len(mailoutbox) == 1  # unchanged: in-app only
    assert Notification.objects.filter(user=user).count() == 2
