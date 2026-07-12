"""Notification delivery (kit 5): in-app always + email per preference."""

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import NOTIFICATION_CATALOG, Notification, NotificationPreference


def _wants(user, event_key: str, channel: str) -> bool:
    catalog = NOTIFICATION_CATALOG.get(event_key, {})
    if channel == 'in_app' and catalog.get('mandatory_in_app'):
        return True
    pref = NotificationPreference.objects.filter(
        user=user, event_key=event_key, channel=channel
    ).first()
    if pref is not None:
        return pref.enabled
    return bool(catalog.get(f'default_{channel}', False))


def notify(*, user, event_key: str, org, project=None, title: str, body: str = '',
           link: str = '', payload: dict | None = None) -> Notification | None:
    """Returns the in-app notification (None when the user opted out and the
    event is not mandatory). Email is sent only when the preference allows it —
    this is where S6 lives: `seal.preserved` defaults to OFF on both channels,
    so a reviewer whose seal survived is never disturbed."""
    wants_in_app = _wants(user, event_key, 'in_app')
    wants_email = _wants(user, event_key, 'email')
    if not wants_in_app and not wants_email:
        return None

    notification = None
    if wants_in_app:
        notification = Notification.objects.create(
            user=user,
            org_id_ref=org.pk,
            project_id_ref=project.pk if project else None,
            event_key=event_key,
            title=title,
            body=body,
            link=link,
            payload=payload or {},
        )

    if wants_email:
        try:
            send_mail(
                subject=title,
                message=f'{body}\n\n{settings.FRONTEND_URL}{link}' if link else body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            if notification:
                notification.email_sent_at = timezone.now()
                notification.save(update_fields=['email_sent_at', 'updated_at'])
        except Exception:  # email must never break the domain transaction
            pass

    return notification
