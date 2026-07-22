"""ProjectConfigVersion — versioned immutable config (I8 base, flow B3)."""

import pytest

from orgs.models import Organization
from projects.models import Project, ProjectConfigVersion


@pytest.fixture
def project(db):
    org = Organization.objects.create(name='Acme', slug='acme')
    return Project.objects.create(organization=org, name='Torre', slug='torre')


@pytest.mark.django_db
def test_current_for_creates_version_one_on_first_call(project):
    config = ProjectConfigVersion.current_for(project)

    assert config.number == 1
    assert config.d5_mode == ProjectConfigVersion.D5Mode.AUTO


@pytest.mark.django_db
def test_current_for_reuses_existing_latest(project):
    first = ProjectConfigVersion.current_for(project)
    ProjectConfigVersion.objects.create(project=project, number=2)

    current = ProjectConfigVersion.current_for(project)

    assert current.number == 2
    assert first.number == 1


@pytest.mark.django_db
def test_archived_project_reports_read_only(project):
    project.status = Project.Status.ARCHIVED
    project.save()

    assert project.is_read_only is True
