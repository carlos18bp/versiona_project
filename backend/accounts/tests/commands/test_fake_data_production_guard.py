"""The fake-data commands must refuse a production-grade database.

Regression for the 2026-08-02 finding: on the staging host the work clone IS the
deployment, `backend/.env` sets DJANGO_ENV=production, and the repo's own
documented E2E entrypoint ran `create_fake_data --scenario=e2e` against it with
no override. The guard used to live only in the fake-data-refresh skill, so
nothing stopped a harness — or a hand-typed command — from writing there.
"""

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.django_db
def test_create_fake_data_refuses_a_production_environment(settings):
    """Catches: the E2E harness seeding owner@versiona.test into a live database."""
    settings.IS_PRODUCTION = True

    with pytest.raises(CommandError) as exc:
        call_command('create_fake_data', '--scenario=e2e')

    assert 'refuses to run' in str(exc.value)


@pytest.mark.django_db
def test_delete_fake_data_refuses_a_production_environment(settings):
    """Catches: a hand-typed --confirm wiping the users of a live database."""
    settings.IS_PRODUCTION = True

    with pytest.raises(CommandError) as exc:
        call_command('delete_fake_data', '--confirm')

    assert 'refuses to run' in str(exc.value)


@pytest.mark.django_db
def test_create_fake_data_names_the_database_it_refused(settings):
    """The operator has to learn WHICH database was about to be written."""
    settings.IS_PRODUCTION = True

    with pytest.raises(CommandError) as exc:
        call_command('create_fake_data', '--scenario=e2e')

    assert settings.DATABASES['default']['NAME'] in str(exc.value)


@pytest.mark.django_db
def test_delete_fake_data_still_demands_confirm_outside_production(settings):
    """The pre-existing --confirm gate is not weakened by the new guard."""
    settings.IS_PRODUCTION = False

    with pytest.raises(CommandError) as exc:
        call_command('delete_fake_data')

    assert 'not confirmed' in str(exc.value)


@pytest.mark.django_db
def test_create_fake_data_runs_on_production_when_explicitly_allowed(settings):
    """A deliberate staging refresh stays possible — the fleet does this."""
    from django.contrib.auth import get_user_model

    settings.IS_PRODUCTION = True

    call_command('create_fake_data', '--scenario=e2e', '--allow-production')

    assert get_user_model().objects.filter(email='owner@versiona.test').exists()
