# Active Context — Versiona

> Memory Bank core file: current focus, recent changes, next steps. Updated every session
> that changes project state.

**Last updated**: 2026-07-12

## Current focus

Iteration 0 (bootstrap) is **complete** on branch `docs/12072026-plan-versiona` (planning
suite + It0 implementation, per the fleet single-active-branch convention). The repo is a
working Versiona skeleton: native Postgres/Celery/MinIO stack, bounded-context apps, green
test suites on both sides, deterministic PDF fixtures, CI adapted.

## Next steps (Iteration 1 — document core: C1, C2, C3, B1)

Per `docs/plan/09` §3, in order:
1. Models + migrations: Organization/Membership (minimal for scoping), Project,
   Document, DocumentVersion, Section, SectionVersion, EngineJob (`docs/plan/02` §3).
2. Analysis pipeline v1 (native text): scenario detection → PyMuPDF extraction →
   sectioning → persist SectionVersions (asserted against `testdata/` truth table).
3. Endpoints: projects CRUD-lite, upload_intent/complete (presigned PUT to MinIO, DP-06),
   versions timeline, `jobs/{id}` polling, signed download (`docs/plan/03` §3).
4. Frontend: `/projects`, `/projects/new`, project view, VersionTimeline, UploadDropzone +
   jobStore, PdfViewer v1 (react-pdf — new dependency).
5. E2E: storageState globalSetup + seed scenario, specs `b1`, `c1`, `c2`, `c3`; coverage
   gates activate (backend 75% + engine 95%).

## Recent decisions to keep in mind

- Operator (2026-07-12): Wompi (DP-01), full-MVP launch cut (DP-14), `d5_mode=auto`
  (DP-03), lock-never-delete retention (DP-04), **no Docker — native runtime** (DP-21).
- Celery uses static beat schedule (no django-celery-beat/results apps).
- MinIO service must join CI when the first storage-backed tests land (It1).
- Deployment polish (nginx/domain/SSL/systemd units for gunicorn+celery) deliberately
  deferred until after the MVP implementation.
