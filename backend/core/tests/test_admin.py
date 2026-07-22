"""StagingPhaseBanner admin actions: phase restarts and visibility toggles."""

from datetime import datetime, timezone as dt_timezone

import pytest
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from freezegun import freeze_time

from core.admin import StagingPhaseBannerAdmin
from core.admin_site import admin_site
from core.models import StagingPhaseBanner


def _request_with_messages():
    request = RequestFactory().get('/admin/')
    request.session = {}
    setattr(request, '_messages', FallbackStorage(request))
    return request


@pytest.fixture
def banner(db):
    instance, _ = StagingPhaseBanner.objects.get_or_create(pk=1)
    return instance


@pytest.mark.django_db
@freeze_time('2026-07-22 10:00:00')
def test_start_design_phase_action_restarts_the_countdown(banner):
    banner.current_phase = StagingPhaseBanner.PHASE_DEVELOPMENT
    banner.save()
    request = _request_with_messages()
    model_admin = StagingPhaseBannerAdmin(StagingPhaseBanner, admin_site)

    model_admin.start_design_phase(request, StagingPhaseBanner.objects.filter(pk=banner.pk))

    banner.refresh_from_db()
    assert banner.current_phase == StagingPhaseBanner.PHASE_DESIGN
    assert banner.started_at == datetime(2026, 7, 22, 10, 0, tzinfo=dt_timezone.utc)
    assert [str(m) for m in get_messages(request)] == ['Design phase started. Countdown reset.']


@pytest.mark.django_db
@freeze_time('2026-07-22 10:00:00')
def test_start_development_phase_action_restarts_the_countdown(banner):
    request = _request_with_messages()
    model_admin = StagingPhaseBannerAdmin(StagingPhaseBanner, admin_site)

    model_admin.start_development_phase(request, StagingPhaseBanner.objects.filter(pk=banner.pk))

    banner.refresh_from_db()
    assert banner.current_phase == StagingPhaseBanner.PHASE_DEVELOPMENT
    assert banner.started_at == datetime(2026, 7, 22, 10, 0, tzinfo=dt_timezone.utc)
    assert [str(m) for m in get_messages(request)] == ['Development phase started. Countdown reset.']


@pytest.mark.django_db
def test_show_banner_action_makes_the_banner_visible(banner):
    StagingPhaseBanner.objects.filter(pk=banner.pk).update(is_visible=False)
    request = _request_with_messages()
    model_admin = StagingPhaseBannerAdmin(StagingPhaseBanner, admin_site)

    model_admin.show_banner(request, StagingPhaseBanner.objects.filter(pk=banner.pk))

    banner.refresh_from_db()
    assert banner.is_visible is True
    assert [str(m) for m in get_messages(request)] == ['Banner shown.']


@pytest.mark.django_db
def test_hide_banner_action_hides_the_banner(banner):
    request = _request_with_messages()
    model_admin = StagingPhaseBannerAdmin(StagingPhaseBanner, admin_site)

    model_admin.hide_banner(request, StagingPhaseBanner.objects.filter(pk=banner.pk))

    banner.refresh_from_db()
    assert banner.is_visible is False
    assert [str(m) for m in get_messages(request)] == ['Banner hidden.']
