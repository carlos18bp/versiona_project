# 07 — Infrastructure

> Docker from day one: the development docker-compose (django, react, postgres+pgvector,
> redis, minio, Celery worker), CI (lint, tests, build on every push), and the migrations &
> seed-data strategy. This compose is the decision that lets the SaaS and the future
> self-hosted plan share one base.

## 1. Base reused

- CI skeleton: `.github/workflows/ci.yml` (4 jobs: backend pytest+coverage, frontend jest,
  Playwright E2E against a real backend, coverage-summary with sticky PR comment) and
  `test-quality-gate.yml` — both kept and adapted, not rewritten.
- Settings split base/dev/prod with `.env` (DB already env-driven) + `.env.example` files —
  extended with the new variables below.
- The template has **no Docker at all** (no Dockerfile, no compose; production runs
  gunicorn/systemd — `scripts/systemd/huey.service`): everything container-side is new.
- Operational periodic tasks (weekly DB+media backup via django-dbbackup, Silk cleanups)
  migrate from Huey to **Celery beat** unchanged.

## 2. Development docker-compose (`compose.yaml`, repo root — NEW)

Same base for the future self-hosted plan (a prod overlay swaps commands/images, not
topology).

| Service | Image / build | Ports | depends_on (healthcheck) | Volumes | Command |
|---|---|---|---|---|---|
| `db` | `pgvector/pgvector:pg16` | 5432 | — · health `pg_isready -U versiona` | `pgdata:/var/lib/postgresql/data` | default |
| `redis` | `redis:7-alpine` | 6379 | — · health `redis-cli ping` | — | default |
| `minio` | `minio/minio` | 9000 (S3) / 9001 (console) | — · health `curl -f :9000/minio/health/live` | `miniodata:/data` | `server /data --console-address ":9001"` |
| `minio-init` | `minio/mc` | — | minio (healthy); `restart: "no"` | — | `mc alias set local http://minio:9000 $U $P && mc mb --ignore-existing local/versiona-media` |
| `backend` | build `backend/Dockerfile` target `dev` | 8000 | db, redis, minio (healthy) | `./backend:/app` | `python manage.py runserver 0.0.0.0:8000` |
| `worker` | backend image | — | db, redis, minio | `./backend:/app` | `celery -A versiona_project worker -l info -Q default,engine_light` |
| `worker-heavy` | backend image | — | db, redis, minio | `./backend:/app` | `celery -A versiona_project worker -l info -Q engine_heavy --concurrency=2` (CPU/OCR-bound; queues per `05` §7 — in low-resource dev a single worker may take all three queues) |
| `beat` | backend image | — | redis | `./backend:/app` | `celery -A versiona_project beat -l info` (inherited periodic tasks) |
| `frontend` | build `frontend/Dockerfile` target `dev` | 3000 | backend | `./frontend:/app` + anonymous `/app/node_modules` | `npm run dev` |
| `mailpit` | `axllent/mailpit` | 8025 (UI+API) / 1025 (SMTP) | — | — | default — chosen over MailHog: maintained, and its REST API lets E2E assert the D1/D5 selective emails (`06` §5.4) |

**Dockerfiles to create** (multi-stage from day 1 because this is also the self-hosted base):

- `backend/Dockerfile`: `base` = python:3.12-slim + libpq + engine system deps (per DP-02:
  `ocrmypdf`, `tesseract-ocr`, `tesseract-ocr-spa`, ghostscript) → `dev` = +test requirements →
  `prod` = gunicorn entrypoint, collectstatic.
- `frontend/Dockerfile`: `dev` = node:22-alpine + `npm ci` + `next dev` → `prod` = standalone
  build.
- `.dockerignore` for both.

**New environment variables** (names; added to both `.env.example` files):
`POSTGRES_DB/USER/PASSWORD/HOST/PORT` (or `DATABASE_URL`) · `CELERY_BROKER_URL` ·
`CELERY_RESULT_BACKEND` · `AWS_S3_ENDPOINT_URL` · `AWS_ACCESS_KEY_ID` ·
`AWS_SECRET_ACCESS_KEY` · `AWS_STORAGE_BUCKET_NAME` · `MEDIA_SIGNED_URL_TTL_SECONDS` ·
`EMAIL_HOST=mailpit` / `EMAIL_PORT=1025` (dev) · `MAX_PDF_SIZE_MB` · `OCR_ENABLED` ·
`D5_DEFAULT_MODE` · `D5_OCR_CONFIDENCE_MIN` · `SEAL_SIGNING_KEY_PATH` · `BILLING_PROVIDER_*`
(when DP-01 lands). Existing `NEXT_PUBLIC_BACKEND_ORIGIN` points at the `backend` service
name inside compose.

## 3. CI (adaptation of `.github/workflows/ci.yml`)

Decision (DP-19): **GitHub Actions native `services:`**, not compose-in-CI — keeps the
existing pip/npm caches and ~1 min faster startup; compose remains the dev/staging runtime
(optional nightly `compose-smoke` job builds images and boots the stack).

| Job | Changes |
|---|---|
| `backend-tests` | Add services `postgres` (image `pgvector/pgvector:pg16`), `redis:7`, `minio` (with health-cmd). pytest moves from SQLite → **PostgreSQL** (FTS/JSONB tests require it). Drop `default-libmysqlclient-dev` (MySQL leaves). Celery `task_always_eager` for unit/integration. Coverage gates per `06` §8 (`--cov-fail-under=75` + module gate script). New step: `manage.py makemigrations --check --dry-run` (anti-drift). |
| `frontend-unit-tests` | Unchanged mechanics; `coverageThreshold` per `06` §8. |
| `frontend-e2e-tests` | Add the same services + steps `migrate` → `create_fake_data --scenario=e2e` → start a real Celery worker in the background (C1/C2/E1/D5 need real jobs) → Playwright webServer (Django + Next) as today. New cache: `~/.cache/ms-playwright` keyed by Playwright version. |
| `coverage-summary` | Unchanged (sticky PR comment). |
| `test-quality-gate.yml` | Unchanged. |

Lint stays as-is (ruff backend, eslint frontend) and runs on every push/PR to master.

## 4. Migrations strategy

- One migration chain per app starting at `0001`; **a merged migration is never edited**; no
  premature squashing.
- `core` migration `0001` enables the `vector` (pgvector) and `pg_trgm` extensions.
- CI runs `migrate` against real PostgreSQL from zero + the `--check` anti-drift step (§3).
- Data migrations only for seed-independent invariants (e.g. default `Plan` rows).

## 5. Seed data

- `create_fake_data` is **rewritten** for Versiona models with scenarios:
  `--scenario=demo|e2e|onboarding` — demo org + 5 users (one per role) + a project holding
  `testdata/pdfs/contrato_v1/v2` with seals/observations/review requests in representative
  states. `delete_fake_data` mirrors it (both keep the fleet skill `fake-data-refresh`
  working).
- The **same seed path** powers the A1 sample project (`orgs/{org}/sample-project/`): demo and
  tests consume identical fixtures, so the wow moment can never drift from what the tests
  assert (`06` §6).

## 6. Staging & production posture (pending)

The fleet convention today is gunicorn + systemd units on the VPS (no containers); this plan
introduces compose as the canonical dev runtime and the self-hosted base. Whether staging runs
on systemd (new `celery-worker.service`/`celery-beat.service` units replacing `huey.service`,
with native or containerized Postgres/MinIO/Redis) or on compose is an operator decision —
see DP-21. Production security headers already exist in `settings_prod.py` and stay.

## 7. Open questions (DECISIÓN PENDIENTE)

| ID | Question | Options / Recommendation |
|---|---|---|
| DP-21 | Staging/production runtime on the VPS: fleet systemd units vs docker-compose. | Operator call. If systemd: new Celery units replace `huey.service`; Postgres/MinIO/Redis native or as single containers. If compose: one runtime everywhere (matches the self-hosted story). Affects It0 and the deploy skills. |
| DP-22 | Domain + production SMTP provider. | Operator call; affects signed URLs, invitation links (A2) and email deliverability (D1/D5). |
| DP-23 | VPS sizing for OCR. | tesseract is CPU-bound; `worker-heavy` may need a dedicated queue/host at scale — measure in It4/It5 with the scanned fixture. |
| DP-19 | E2E in CI (services vs compose). | Resolved by recommendation in `06` §9 — native services. |
