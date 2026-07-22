# Versiona

> **The Git of documents** — version control, comparison and seal-based approval for the
> world that works in PDF. No more `final_v3_AHORA_SI.pdf`.

[![Django](https://img.shields.io/badge/Django-6.0-092E20?style=flat&logo=django)](https://www.djangoproject.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat&logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-4169E1?style=flat&logo=postgresql)](https://www.postgresql.org/)
[![Celery](https://img.shields.io/badge/Celery-5.6-37814A?style=flat&logo=celery)](https://docs.celeryq.dev/)

Every upload is an immutable **version**; every re-delivery produces an automatic
**comparison**; reviewers leave **anchored observations** and approve with Ed25519-signed
**seals**; and — the crown jewel (flow **D5**) — when a new version arrives, only the
approvals of the sections that actually changed are invalidated, and only those reviewers
are notified.

## Documentation map

| What | Where |
|---|---|
| Vision, glossary, what v1 is NOT | `docs/plan/00-vision.md` |
| MVP scope: 16 flows (A1…F1) with acceptance criteria | `docs/plan/01-alcance-mvp.md` |
| Data model + 15 domain invariants | `docs/plan/02-modelo-datos.md` |
| Backend apps, endpoints, roles | `docs/plan/03-backend.md` |
| Frontend screens, components, state | `docs/plan/04-frontend.md` |
| Comparison engine + D5 algorithm | `docs/plan/05-motor-comparacion.md` |
| Test design + traceability + PDF fixtures | `docs/plan/06-pruebas.md` |
| Infrastructure (native runtime; Docker deferred per DP-21) | `docs/plan/07-infraestructura.md` |
| Security: authz, hashes, seal signature, audit | `docs/plan/08-seguridad.md` |
| Execution roadmap (It0–It7) + pending decisions | `docs/plan/09-roadmap-ejecucion.md` |
| User flows ↔ E2E cross-reference | `docs/USER_FLOW_MAP.md` |
| Deterministic PDF fixtures + truth table | `testdata/README.md` |

## Stack

- **Backend**: Django 6 + DRF, Celery (Redis broker; queues `default` / `engine_light` /
  `engine_heavy`), PostgreSQL 16 + pgvector, MinIO (S3 object storage), PyMuPDF engine.
- **Frontend**: Next.js 16 (App Router) + React 19 + TypeScript + Tailwind v4 + Zustand.
- **Testing**: pytest · Jest + RTL · Playwright (flow-coverage convention).
- **Runtime**: native processes on the VPS (PostgreSQL/Redis/MinIO/mailpit as system
  services). Docker/compose is a deferred blueprint for the self-hosted plan (DP-21).

## Project structure

```
backend/
  versiona_project/   Django project (settings split, celery.py, operational tasks)
  core/               mixins (TimestampedModel, PublicIdModel/UUIDv7), admin site, staging banner
  accounts/           auth (User, PasswordCode, sign-in/up, Google OAuth, reset, impersonation)
  orgs/ projects/ documents/ reviews/ observations/ checks/
  comparisons/ engine/ notifications/ billing/ audit/     ← bounded contexts (skeletons)
frontend/
  app/                Next.js App Router (landing, auth, dashboard, help)
  components/         layout, staging gate, components/ui kit (Modal, Tabs, StatusBadge, …)
  lib/                stores (Zustand), services (axios + JWT refresh), i18n
  e2e/                Playwright specs + flow-definitions.json (v2.0.0)
testdata/             deterministic PDF fixtures + generator (the D5 truth table)
docs/plan/            the planning suite (source of truth)
```

## Quick start (development)

```bash
# Backend (native PostgreSQL/Redis/MinIO/mailpit must be running — docs/plan/07 §2.1)
cd backend
python3 -m venv venv && venv/bin/pip install -r requirements.txt
cp .env.example .env          # fill DB_PASSWORD / AWS_SECRET_ACCESS_KEY
venv/bin/python manage.py migrate
venv/bin/python manage.py runserver          # http://localhost:8000

# Celery (optional in dev — tasks run eager unless CELERY_TASK_ALWAYS_EAGER=0)
venv/bin/celery -A versiona_project worker -l info -Q default,engine_light,engine_heavy
venv/bin/celery -A versiona_project beat -l info

# Frontend
cd ../frontend
npm ci && npm run dev                        # http://localhost:3000

# Test fixtures (committed; regenerate only via the script)
backend/venv/bin/python testdata/generate_pdfs.py
```

## Testing

```bash
# Backend (always target files/dirs; never the blind full suite)
backend/venv/bin/python -m pytest backend/accounts/tests/views -v

# Frontend unit
cd frontend && npm test -- components/ui/__tests__/ui-kit.test.tsx

# E2E (max 2 files per invocation)
cd frontend && npx playwright test e2e/public/smoke.spec.ts e2e/auth/auth.spec.ts
```

Quality gates: `docs/TESTING_QUALITY_STANDARDS.md` + `scripts/test_quality_gate.py`
(pre-commit + CI). Coverage thresholds per `docs/plan/06-pruebas.md` §8.

## Status

**Iteration 0 (bootstrap) — done**: Postgres+pgvector/Celery/MinIO/mailpit provisioned and
wired, demo domain purged, bounded-context skeleton, deterministic fixtures, CI on Postgres
services, flow definitions v2. **Next: Iteration 1 — document core (C1, C2, C3, B1)** per
`docs/plan/09-roadmap-ejecucion.md`.
