"""
EmailTemplateRegistry (kit 5 — operator decision: es/en functional).

One entry per event, BOTH languages, rendered with str.format(**context).
The in-app title/body and the email share the same copy; the recipient's
`user.language` picks the variant. Adding an event here AND in
NOTIFICATION_CATALOG is the whole checklist for a new notification.
"""

TEMPLATES = {
    'seal.invalidated': {
        'es': {
            'title': 'Tu sello en "{document}" requiere re-revisión (v{version})',
            'body': 'Cambió lo que sellaste: {sections}. Tu re-revisión está acotada a esas secciones.',
        },
        'en': {
            'title': 'Your seal on "{document}" requires re-review (v{version})',
            'body': 'What you sealed changed: {sections}. Your re-review is scoped to those sections.',
        },
    },
    'seal.placed': {
        'es': {
            'title': '{reviewer} selló v{version} de "{document}"',
            'body': 'El sello cubre {coverage}.',
        },
        'en': {
            'title': '{reviewer} sealed v{version} of "{document}"',
            'body': 'The seal covers {coverage}.',
        },
    },
    'version.approved': {
        'es': {
            'title': 'v{version} de "{document}" quedó aprobada',
            'body': '{qualifying} sello(s) válidos — regla: {required}.',
        },
        'en': {
            'title': 'v{version} of "{document}" was approved',
            'body': '{qualifying} valid seal(s) — rule: {required}.',
        },
    },
    'seal_plan.pending': {
        'es': {
            'title': 'Plan de invalidación por confirmar — "{document}" v{version}',
            'body': 'El análisis fue degradado o el proyecto está en modo coordinador: confirma qué sellos se conservan.',
        },
        'en': {
            'title': 'Invalidation plan awaiting confirmation — "{document}" v{version}',
            'body': 'The analysis was degraded or the project runs in coordinator mode: confirm which seals survive.',
        },
    },
    'review.requested': {
        'es': {
            'title': '{requester} te asignó la revisión de "{document}" v{version}',
            'body': '{message}',
        },
        'en': {
            'title': '{requester} assigned you the review of "{document}" v{version}',
            'body': '{message}',
        },
    },
    'review.completed': {
        'es': {
            'title': 'La revisión de "{document}" v{version} está completa',
            'body': 'Todos los revisores asignados sellaron la versión.',
        },
        'en': {
            'title': 'The review of "{document}" v{version} is complete',
            'body': 'Every assigned reviewer sealed the version.',
        },
    },
    'observation.created': {
        'es': {
            'title': '{author} dejó una observación en "{document}" ({section})',
            'body': '{excerpt}',
        },
        'en': {
            'title': '{author} left an observation on "{document}" ({section})',
            'body': '{excerpt}',
        },
    },
    'observation.replied': {
        'es': {
            'title': '{author} respondió tu observación en "{document}"',
            'body': '{excerpt}',
        },
        'en': {
            'title': '{author} replied to your observation on "{document}"',
            'body': '{excerpt}',
        },
    },
    'invitation.accepted': {
        'es': {
            'title': '{email} aceptó tu invitación a "{project}"',
            'body': 'Ya puede trabajar en el proyecto.',
        },
        'en': {
            'title': '{email} accepted your invitation to "{project}"',
            'body': 'They can now work on the project.',
        },
    },
    'observation.resolved': {
        'es': {
            'title': 'Tu observación en "{document}" fue resuelta',
            'body': 'Sección: {section}. Resuelta en v{version}.',
        },
        'en': {
            'title': 'Your observation on "{document}" was resolved',
            'body': 'Section: {section}. Resolved in v{version}.',
        },
    },
    'billing.trial_ending': {
        'es': {
            'title': 'Tu prueba Pro termina en {days} día(s)',
            'body': 'El {date} tu organización "{org}" vuelve al plan Gratis. '
                    'Nada se borra: el historial antiguo queda bloqueado hasta '
                    'que mejores tu plan.',
        },
        'en': {
            'title': 'Your Pro trial ends in {days} day(s)',
            'body': 'On {date} your organization "{org}" returns to the Free '
                    'plan. Nothing is deleted: old history stays locked until '
                    'you upgrade.',
        },
    },
    'billing.trial_ended': {
        'es': {
            'title': 'Tu prueba Pro terminó: volviste al plan Gratis',
            'body': 'Tu organización "{org}" está de nuevo en el plan Gratis. '
                    'Nada se borra: el historial antiguo queda bloqueado hasta '
                    'que mejores tu plan.',
        },
        'en': {
            'title': 'Your Pro trial ended: you are back on the Free plan',
            'body': 'Your organization "{org}" is on the Free plan again. '
                    'Nothing is deleted: old history stays locked until you '
                    'upgrade.',
        },
    },
}


class MissingTemplate(KeyError):
    pass


def render(event_key: str, language: str, context: dict | None) -> tuple[str, str]:
    """(title, body) in the requested language, falling back to Spanish."""
    try:
        entry = TEMPLATES[event_key]
    except KeyError as exc:
        raise MissingTemplate(
            f'Evento "{event_key}" sin plantilla: agrégalo a notifications/templates.py'
        ) from exc
    variant = entry.get(language) or entry['es']
    values = context or {}

    class _Safe(dict):
        def __missing__(self, key):  # tolerate sparse contexts
            return f'{{{key}}}'

    return (
        variant['title'].format_map(_Safe(values)),
        variant['body'].format_map(_Safe(values)),
    )
