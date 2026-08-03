"""T13: (organization, slug) is unique among ALIVE projects only.

PostgreSQL expressed this as a partial unique index. MySQL 8 has none, so the
condition lives in the generated column `slug_alive`, which is NULL for trashed
rows. These tests assert the outcome, not the mechanism — they would have caught
the silent constraint loss that a naive engine swap produces.
"""

import pytest
from django.db import IntegrityError, transaction

from orgs.models import Organization
from projects.models import Project


@pytest.fixture
def organization(db):
    return Organization.objects.create(name='Acme', slug='acme')


@pytest.mark.django_db
def test_two_alive_projects_cannot_share_a_slug(organization):
    Project.objects.create(organization=organization, name='Torre', slug='torre')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Project.objects.create(organization=organization, name='Torre bis', slug='torre')


@pytest.mark.django_db
def test_trashing_a_project_frees_its_slug(organization):
    original = Project.objects.create(organization=organization, name='Torre', slug='torre')

    original.soft_delete()
    reused = Project.objects.create(organization=organization, name='Torre nueva', slug='torre')

    assert reused.pk != original.pk


@pytest.mark.django_db
def test_the_same_slug_is_free_in_another_organization(organization):
    other = Organization.objects.create(name='Ajena', slug='ajena')
    Project.objects.create(organization=organization, name='Torre', slug='torre')

    elsewhere = Project.objects.create(organization=other, name='Torre', slug='torre')

    assert elsewhere.organization == other
