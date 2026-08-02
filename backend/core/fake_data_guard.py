"""Production guard for the fake-data management commands.

Why this lives in code and not in a runbook: `delete_fake_data`'s docstring used
to say "production never runs this (the fake-data-refresh skill gates on
DJANGO_ENV)". That is a guard living in an external convention — it protects
nobody who runs the command by hand, and nobody who runs it from a harness that
never read the skill. Measured on 2026-08-02: on the staging host the work clone
IS the deployment, `backend/.env` sets `DJANGO_ENV=production`, and the repo's
own documented E2E entrypoint (`playwright.config.ts` -> `global-setup.ts`)
called `create_fake_data --scenario=e2e` with no override, which would seed
`owner@versiona.test` / `secreta123` straight into the live staging database.

Note that a fleet *staging* deployment also reports `IS_PRODUCTION` — the fleet
contract says staging is production-grade in every way except backups and
performance mail. Refusing on staging too is deliberate: staging is exactly
where an E2E harness is most likely to be pointed by accident. A deliberate
staging refresh stays possible through `--allow-production`, where the caller
states in the command line that it knows which database it is about to touch.
"""

from django.conf import settings
from django.core.management.base import CommandError

ALLOW_FLAG = '--allow-production'


def add_allow_production_argument(parser):
    """Register the opt-out on a fake-data command's parser."""
    parser.add_argument(
        ALLOW_FLAG,
        action='store_true',
        dest='allow_production',
        help=(
            'Run even though this environment reports IS_PRODUCTION. Required '
            'for a deliberate staging refresh; never pass it from a test harness.'
        ),
    )


def refuse_on_production(options, command_name):
    """Raise unless it is safe — or explicitly authorised — to write fake data.

    `options` is the management command's parsed options dict.
    """
    if not settings.IS_PRODUCTION:
        return
    if options.get('allow_production'):
        return
    raise CommandError(
        f'{command_name} refuses to run: DJANGO_ENV=production, so this points at a '
        f'production-grade database '
        f'(DJANGO_DB_NAME={settings.DATABASES["default"].get("NAME")!r}). '
        f'A test harness should point DJANGO_ENV and DJANGO_DB_NAME at a dev '
        f'database rather than bypass this. To act on this database on purpose, '
        f'pass {ALLOW_FLAG}.'
    )
