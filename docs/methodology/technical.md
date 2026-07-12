# Technical — Versiona

> Memory Bank core file. Infra detail: `docs/plan/07-infraestructura.md`; security:
> `docs/plan/08-seguridad.md`.

## Stack (verified versions)

| Layer | Tech |
|---|---|
| Backend | Python 3.12 · Django 6.0.5 · DRF 3.17 · simplejwt 5.5 (+token_blacklist) |
| Async | Celery 5.6 (Redis broker/results; queues default/engine_light/engine_heavy; static `CELERY_BEAT_SCHEDULE`; eager in dev/tests) |
| Data | PostgreSQL 16 + pgvector 0.6 + pg_trgm (extensions in template1 on this VPS + vendor-safe core migration 0001) |
| Files | MinIO (native systemd, bucket `versiona-media`) via django-storages S3; FileSystem fallback when no bucket configured |
| PDF engine | PyMuPDF 1.28 (+ reportlab for fixtures); OCR (ocrmypdf+tesseract) joins It4/It5 (DP-02) |
| Frontend | Next.js 16.2 (App Router) · React 19.2 · TS strict · Tailwind v4 (OKLCH tokens) · Zustand 5 · axios (401 refresh single-flight) |
| Testing | pytest(+django/cov/factory-boy/freezegun) · Jest 30 + RTL · Playwright 1.60 + flow-coverage reporter |
| Email dev | mailpit (SMTP :1025, REST API :8025 — E2E asserts selective D5 emails against it) |

## Dev environment (native — no Docker, DP-21)

- System services on this VPS: `postgresql`, `redis-server`, `minio.service`,
  `mailpit.service` (units in /etc/systemd/system; MinIO env in /etc/default/minio).
- Backend: `backend/venv`; `.env` holds DB/MinIO/mailpit config (gitignored).
- Commands: `venv/bin/python manage.py runserver` · `venv/bin/celery -A versiona_project
  worker|beat` · `npm run dev` · fixtures: `venv/bin/python testdata/generate_pdfs.py`.
- CI: GitHub Actions with pgvector+redis services; `makemigrations --check` anti-drift;
  Playwright browser cache. MinIO service joins CI in It1.

## Key constraints & decisions

- Docker/compose deferred (DP-21) — kept as blueprint in `docs/plan/07` §2.2.
- Payment gateway: **Wompi** behind a `PaymentGateway` adapter (DP-01, It7).
- `d5_mode` default **auto** (DP-03); free-plan retention locks access, never deletes (DP-04).
- Search: PostgreSQL FTS `spanish`; pgvector column dormant until V2 (DP-05).
- Coverage gates (docs/plan/06 §8): backend 75% global + 95% engine/invalidation from It1;
  Jest 50→55→60 progressive.
