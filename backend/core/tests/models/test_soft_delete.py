"""Soft-delete mixin behavior (kit 3 — mechanism behind B4/C4)."""

import pytest
from django.utils import timezone
from freezegun import freeze_time

from orgs.models import Organization
from projects.models import Project


@pytest.fixture
def project(db):
    org = Organization.objects.create(name='Acme', slug='acme')
    return Project.objects.create(organization=org, name='Torre', slug='torre')


@pytest.mark.django_db
def test_soft_delete_hides_row_from_default_manager(project, django_user_model):
    user = django_user_model.objects.create_user(email='e@example.com', password='x' * 8)

    project.soft_delete(user)

    assert Project.objects.filter(pk=project.pk).count() == 0
    assert Project.all_objects.filter(pk=project.pk).count() == 1
    assert Project.all_objects.get(pk=project.pk).deleted_by == user


@pytest.mark.django_db
def test_restore_returns_row_to_default_manager(project):
    project.soft_delete()

    project.restore()

    assert Project.objects.filter(pk=project.pk).count() == 1
    assert project.deleted_at is None


@pytest.mark.django_db
def test_purge_after_derives_from_retention_setting(project, settings):
    settings.TRASH_RETENTION_DAYS = 30
    with freeze_time('2026-07-12 10:00:00'):
        project.soft_delete()

    assert project.purge_after == project.deleted_at + timezone.timedelta(days=30)


@pytest.mark.django_db
def test_purgeable_queryset_respects_grace_window(project, settings):
    settings.TRASH_RETENTION_DAYS = 30
    with freeze_time('2026-06-01 10:00:00'):
        project.soft_delete()

    with freeze_time('2026-06-20 10:00:00'):
        assert Project.all_objects.purgeable().count() == 0

    with freeze_time('2026-07-12 10:00:00'):
        assert Project.all_objects.purgeable().count() == 1


@pytest.mark.django_db
def test_trashed_project_slug_is_reusable(project):
    """Partial unique (T13): a new project may take the slug of a trashed one."""
    project.soft_delete()

    reborn = Project.objects.create(
        organization=project.organization, name='Torre', slug='torre'
    )

    assert reborn.pk != project.pk
