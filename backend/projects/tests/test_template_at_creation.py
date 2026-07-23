"""B1-A01 negative verification: creating a project does NOT accept an org
checklist template, so config v1 never carries copied checks. The only
implemented path is copy-on-apply, which lands on config v2 (kit 2)."""

import pytest

from checks.models import ChecklistTemplate
from projects.models import Project, ProjectConfigVersion


@pytest.fixture
def org_template(versiona_context):
    return ChecklistTemplate.objects.create(
        organization=versiona_context.org,
        name='Contratos base',
        items=[{'key': 'confidencialidad', 'label': 'Cláusula de confidencialidad',
                'type': 'required_section', 'param': 'confidencialidad',
                'severity': 'fail'}],
    )


@pytest.mark.django_db
@pytest.mark.escenario('B1-A01')
def test_project_creation_ignores_the_org_template_reference(
    client_as, versiona_context, org_template
):
    response = client_as('admin').post(
        f'/api/orgs/{versiona_context.org.public_id}/projects/',
        {'name': 'Con plantilla', 'template': str(org_template.public_id)},
        format='json',
    )

    assert response.status_code == 201
    created = Project.objects.get(public_id=response.data['public_id'])
    assert ProjectConfigVersion.current_for(created).checklist == []


@pytest.mark.django_db
@pytest.mark.escenario('B1-A01')
def test_created_project_starts_on_config_version_one_without_checks(
    client_as, versiona_context, org_template
):
    response = client_as('admin').post(
        f'/api/orgs/{versiona_context.org.public_id}/projects/',
        {'name': 'Sin checks', 'template': str(org_template.public_id)},
        format='json',
    )

    created = Project.objects.get(public_id=response.data['public_id'])
    assert ProjectConfigVersion.current_for(created).number == 1


@pytest.mark.django_db
@pytest.mark.escenario('B1-A01')
def test_applying_the_template_afterwards_lands_on_config_version_two(
    client_as, versiona_context, org_template
):
    created = client_as('admin').post(
        f'/api/orgs/{versiona_context.org.public_id}/projects/',
        {'name': 'Aplicada luego'},
        format='json',
    )
    project_id = created.data['public_id']

    response = client_as('admin').post(
        f'/api/projects/{project_id}/config/apply_template/',
        {'template': str(org_template.public_id)},
        format='json',
    )

    assert response.status_code == 201
    assert response.data['number'] == 2
