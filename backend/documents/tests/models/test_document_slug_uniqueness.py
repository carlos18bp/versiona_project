"""T14: (project, slug) is unique among ALIVE documents only.

Same shape as the project rule — see projects/tests/models/
test_project_slug_uniqueness.py for why the constraint is expressed as a
generated column on MySQL.
"""

import pytest
from django.db import IntegrityError, transaction

from documents.models import Document
from orgs.models import Organization
from projects.models import Project


@pytest.fixture
def project(db):
    org = Organization.objects.create(name='Acme', slug='acme')
    return Project.objects.create(organization=org, name='Torre', slug='torre')


@pytest.mark.django_db
def test_two_alive_documents_cannot_share_a_slug(project):
    Document.objects.create(project=project, title='Contrato', slug='contrato')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Document.objects.create(project=project, title='Contrato bis', slug='contrato')


@pytest.mark.django_db
def test_trashing_a_document_frees_its_slug(project):
    original = Document.objects.create(project=project, title='Contrato', slug='contrato')

    original.soft_delete()
    reused = Document.objects.create(project=project, title='Contrato nuevo', slug='contrato')

    assert reused.pk != original.pk
