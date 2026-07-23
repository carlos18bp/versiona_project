# Management commands — fake data & E2E harness

## create_fake_data

```bash
# Default: N fake users, each with a personal org + 14-day Pro trial (Versiona rules)
python manage.py create_fake_data            # 10 users (--users default)
python manage.py create_fake_data 50         # positional number_of_records
python manage.py create_fake_data --users 25

# Deterministic E2E scenario (idempotent — safe to re-run):
#   owner/admin/editor/reviewer/viewer@versiona.test (pw secreta123),
#   org acme-e2e (plan=enterprise console override), project torre-e2e,
#   trial@versiona.test with a live personal-org trial.
python manage.py create_fake_data --scenario=e2e
```

The default path delegates to `create_users`, which provisions each user through
`orgs.services.ensure_personal_org` — the same code path real signups use — so
every fake user gets a personal Organization and a trialing `billing.Subscription`.
Fake users are NEVER staff/superuser. Dev password: `secreta123`.

## delete_fake_data

```bash
python manage.py delete_fake_data --confirm
```

Deletes every non-superuser User, then every Organization left without members
(cascades projects/documents/versions in the DB). Superusers survive. MinIO
objects of cascaded documents are acceptable dev debris. Never runs in
production (the `fake-data-refresh` skill gates on `DJANGO_ENV`).

**Full refresh** (delete + create + E2E re-seed) — use the `fake-data-refresh`
skill; afterwards re-seed the harness: `create_fake_data --scenario=e2e`.

## e2e_tokens

Prints simplejwt access/refresh tokens (JSON) for the five E2E actors — used by
the Playwright globalSetup. Requires the `--scenario=e2e` seed to exist.
