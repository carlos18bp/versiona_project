"""Bilingual template registry (kit 5 — es/en per recipient language)."""

import pytest

from notifications.models import NOTIFICATION_CATALOG, Notification
from notifications.services import notify
from notifications.templates import TEMPLATES, MissingTemplate, render


def test_every_catalog_event_has_both_language_templates():
    """The registry IS the catalog's copy: no event ships without es AND en."""
    for event_key in NOTIFICATION_CATALOG:
        if event_key == 'seal.preserved':
            continue  # never sent (S6) — no template by design
        assert event_key in TEMPLATES, f'{event_key} sin plantilla'
        assert set(TEMPLATES[event_key]) >= {'es', 'en'}, f'{event_key} sin ambos idiomas'
        for lang in ('es', 'en'):
            assert TEMPLATES[event_key][lang]['title']


def test_render_formats_context_in_the_requested_language():
    title_es, _ = render('review.requested', 'es',
                         {'requester': 'ana@x.co', 'document': 'Contrato', 'version': 2})
    title_en, _ = render('review.requested', 'en',
                         {'requester': 'ana@x.co', 'document': 'Contrato', 'version': 2})

    assert title_es == 'ana@x.co te asignó la revisión de "Contrato" v2'
    assert title_en == 'ana@x.co assigned you the review of "Contrato" v2'


def test_render_falls_back_to_spanish_for_unknown_language():
    title, _ = render('version.approved', 'fr', {'version': 1, 'document': 'X'})

    assert 'aprobada' in title


def test_render_tolerates_sparse_context():
    title, body = render('seal.invalidated', 'es', {'document': 'X'})

    assert '{version}' in title  # visible placeholder beats a crash
    assert '{sections}' in body


def test_unknown_event_raises_missing_template():
    with pytest.raises(MissingTemplate):
        render('evento.inventado', 'es', {})


@pytest.mark.django_db
@pytest.mark.escenario('NTF-F04')
def test_notify_renders_in_the_recipients_language(versiona_context, mailoutbox):
    context = versiona_context
    reviewer = context.users['reviewer']
    reviewer.language = 'en'
    reviewer.save(update_fields=['language'])

    notify(
        user=reviewer, event_key='review.requested', org=context.org,
        project=context.project,
        context={'requester': 'ana@x.co', 'document': 'Contrato', 'version': 3,
                 'message': 'focus on §3'},
    )

    notification = Notification.objects.get(user=reviewer)
    assert notification.title == 'ana@x.co assigned you the review of "Contrato" v3'
    assert mailoutbox[0].subject == notification.title


@pytest.mark.django_db
def test_notify_defaults_to_spanish(versiona_context):
    context = versiona_context
    editor = context.users['editor']  # language default 'es'

    notify(
        user=editor, event_key='version.approved', org=context.org,
        project=context.project,
        context={'version': 1, 'document': 'Contrato', 'qualifying': 1, 'required': 1},
    )

    assert 'quedó aprobada' in Notification.objects.get(user=editor).title
