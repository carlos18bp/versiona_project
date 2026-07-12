"""B3: versioned config, structural non-retroactivity (I8), owner approval."""

from pathlib import Path

import pytest

from checks.models import ChecklistTemplate
from documents.services import storage_service, version_service
from projects.models import ProjectConfigVersion
from projects.services import config_service
from reviews.services import seal_service

TESTDATA = Path(__file__).resolve().parents[3] / 'testdata' / 'pdfs'


@pytest.fixture(autouse=True)
def _test_env(settings, tmp_path):
    settings.DJANGO_ENV = 'test'
    settings.SEAL_SIGNING_KEY_PATH = str(tmp_path / 'seal_key.pem')


def upload(document, fixture, message, author):
    intent = version_service.create_upload_intent(document, author)
    storage_service.put_bytes(intent.key, (TESTDATA / fixture).read_bytes(), 'application/pdf')
    version, _ = version_service.complete_upload(document, intent.upload_id, message, author)
    return version


@pytest.mark.django_db
@pytest.mark.escenario('B3-F01')
def test_editing_config_creates_a_new_version(versiona_context):
    project = versiona_context.project
    admin = versiona_context.users['admin']
    original = ProjectConfigVersion.current_for(project)

    updated = config_service.update_config(
        project, admin, d5_mode='coordinator'
    )

    assert updated.number == original.number + 1
    assert updated.d5_mode == 'coordinator'
    # The original row is untouched (immutability by construction).
    original.refresh_from_db()
    assert original.d5_mode == 'auto'


@pytest.mark.django_db
@pytest.mark.escenario('B3-F02')
def test_i8_existing_versions_keep_their_pinned_config(versiona_context):
    """THE non-retroactivity proof: a version uploaded under config v1 keeps
    answering to v1 even after the project moves to v2."""
    context = versiona_context
    editor = context.users['editor']
    document = version_service.create_document(context.project, 'Pineado', editor)
    v1 = upload(document, 'contrato_v1.pdf', 'v1', editor)
    pinned_before = v1.config_version.number

    config_service.update_config(
        context.project, context.users['admin'],
        checklist=[{'key': 'nueva-regla', 'label': 'Nueva regla', 'type': 'required_text',
                    'param': 'inexistente', 'severity': 'fail'}],
    )

    v1.refresh_from_db()
    assert v1.config_version.number == pinned_before  # still the old config
    v2 = upload(document, 'contrato_v2.pdf', 'v2', editor)
    assert v2.config_version.number == pinned_before + 1  # new uploads pin the new one


@pytest.mark.django_db
@pytest.mark.escenario('B3-E01')
def test_checklist_validation_rejects_bad_items(versiona_context):
    project = versiona_context.project
    admin = versiona_context.users['admin']

    with pytest.raises(version_service.DomainError):
        config_service.update_config(project, admin, checklist=[{'key': ''}])
    with pytest.raises(version_service.DomainError):
        config_service.update_config(
            project, admin,
            checklist=[{'key': 'x', 'label': 'X', 'type': 'tipo-raro', 'param': 'y'}],
        )
    with pytest.raises(version_service.DomainError):
        config_service.update_config(
            project, admin,
            section_owners={'objeto': [999999]},  # not a member
        )


@pytest.mark.django_db
@pytest.mark.escenario('B3-F03')
def test_owner_based_approval_all_assigned(versiona_context):
    """'all_assigned': the version approves only when EVERY owned section is
    sealed by one of its owners."""
    context = versiona_context
    editor = context.users['editor']
    reviewer = context.users['reviewer']
    admin = context.users['admin']
    config_service.update_config(
        context.project, admin,
        approval_policy={'required': 'all_assigned'},
        section_owners={
            'objeto-del-contrato': [reviewer.pk],
            'obligaciones-del-contratista': [admin.pk],
        },
    )
    document = version_service.create_document(context.project, 'Con dueños', editor)
    version = upload(document, 'contrato_v1.pdf', 'v1', editor)

    seal_service.create_seal(version, reviewer, section_keys=['objeto-del-contrato'])
    version.refresh_from_db()
    assert version.is_approved is False  # admin's section still unsealed

    seal_service.create_seal(version, admin, section_keys=['obligaciones-del-contratista'])
    version.refresh_from_db()
    assert version.is_approved is True


@pytest.mark.django_db
@pytest.mark.escenario('B3-E02')
def test_owner_seal_by_a_non_owner_does_not_approve(versiona_context):
    context = versiona_context
    editor = context.users['editor']
    reviewer = context.users['reviewer']
    admin = context.users['admin']
    config_service.update_config(
        context.project, admin,
        approval_policy={'required': 'all_assigned'},
        section_owners={'objeto-del-contrato': [admin.pk]},  # owner: admin only
    )
    document = version_service.create_document(context.project, 'Dueño ajeno', editor)
    version = upload(document, 'contrato_v1.pdf', 'v1', editor)

    # The reviewer seals the owned section, but is NOT its owner.
    seal_service.create_seal(version, reviewer, section_keys=['objeto-del-contrato'])

    version.refresh_from_db()
    assert version.is_approved is False


@pytest.mark.django_db
@pytest.mark.escenario('B3-A01')
def test_template_copy_on_apply_is_a_snapshot(versiona_context):
    """Kit 2: applying copies the items; editing the template later never
    touches the project config (I8-friendly)."""
    context = versiona_context
    admin = context.users['admin']
    template = ChecklistTemplate.objects.create(
        organization=context.org, name='Contratos base',
        items=[{'key': 'confidencialidad', 'label': 'Cláusula de confidencialidad',
                'type': 'required_section', 'param': 'confidencialidad',
                'severity': 'fail'}],
    )

    config = config_service.apply_template(context.project, admin, template)

    assert config.checklist[0]['key'] == 'confidencialidad'
    template.items = []
    template.save(update_fields=['items'])
    config.refresh_from_db()
    assert config.checklist, 'la copia sobrevive a la edición de la plantilla'


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('admin', 201, id='b3-p01-admin'),
    pytest.param('editor', 404, id='b3-p02-editor-hidden'),
    pytest.param('anonymous', 401, id='b3-p03-anonymous'),
    pytest.param('non_member', 404, id='b3-p04-non-member'),
])
def test_update_config_permission_matrix(client_as, versiona_context, actor, expected):
    response = client_as(actor).post(
        f'/api/projects/{versiona_context.project.public_id}/config/',
        {'d5_mode': 'coordinator'},
        format='json',
    )

    assert response.status_code == expected


@pytest.mark.django_db
def test_config_is_hidden_from_non_admin_members(client_as, versiona_context):
    response = client_as('viewer').get(
        f'/api/projects/{versiona_context.project.public_id}/config/'
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_config_get_exposes_current_state(client_as, versiona_context):
    response = client_as('admin').get(
        f'/api/projects/{versiona_context.project.public_id}/config/'
    )

    assert response.status_code == 200
    assert response.data['number'] >= 1
    assert response.data['d5_mode'] in ('auto', 'coordinator')
    assert 'checklist' in response.data
