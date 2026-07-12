# Tasks Plan — Versiona

> Memory Bank core file: backlog, progress and known issues. The authoritative roadmap is
> `docs/plan/09-roadmap-ejecucion.md` (vertical iterations, DoD, DP register).

## Iteration backlog (vertical — each ships flows end to end)

| It | Flows | Status |
|---|---|---|
| 0 — Bootstrap | infra + skeleton + purge + fixtures + CI | ✅ **DONE 2026-07-12** |
| 1 — Document core | C1, C2, C3, B1 (+B2 minimal) | ⏭ next |
| 2 — Comparison (star screen) | E1 | pending |
| 3 — Seals + **D5 (jewel)** | D4, D5 | pending |
| 4 — Collaborative review | D1, D2, D3 (+OCR sub-delivery) | pending |
| 5 — Governance | B3, E3, B2 complete | pending |
| 6 — Onboarding wow + team | A1, A2 | pending |
| 7 — Monetization (Wompi) | F1 | pending |

DoD per iteration: `docs/plan/09` §4 (9 checks: PR, 3 green test levels, coverage,
flow-definitions `covered` + USER_FLOW_MAP sheets, clean migrate + `--check`, fake data,
no secrets, end-to-end demo, no template residue).

## It0 delivered (2026-07-12)

- Native services: PostgreSQL 16 + pgvector/pg_trgm (template1 + versiona DB), MinIO +
  `versiona-media`, mailpit; systemd units for MinIO/mailpit.
- Backend: package renamed to `versiona_project`; Huey→Celery (static beat, 4 inherited
  operational tasks); Postgres default engine; S3 storage when bucket configured; DRF
  pagination/throttle rates; token_blacklist fixed; monolith → `core` + `accounts` + 11
  skeleton apps; fresh migrations; **123 tests green**; ruff clean.
- Frontend: demo e-commerce purged; Versiona landing + rebranded header/footer/dashboard
  (Spanish-first, DP-17); `components/ui` kit (StatusBadge, EmptyState, Skeleton, Modal,
  Tabs, Toaster) with RTL tests; **114 tests green**, coverage threshold holds.
- Test assets: `testdata/` deterministic PDFs (byte-reproducible; D5 truth table).
- E2E: flow-definitions v2.0.0 (16 MVP + 5 auth + smoke), flow-tags v2, USER_FLOW_MAP v2.
- CI: pgvector/redis services, Postgres pytest, anti-drift migration check, Playwright
  cache; MySQL removed.
- Identity: CLAUDE.md/AGENTS.md/README rewritten; Memory Bank instantiated.

## Known issues (template debt, non-blocking)

1. **Pre-existing tsc error** in `frontend/lib/services/__tests__/http.test.ts`
   (mock typing) — `npx tsc --noEmit` fails; CI does not run tsc, `next build` may.
   Fix opportunistically in It1.
2. **Pre-existing ESLint errors** (29) in template files: auth pages (`no-explicit-any`,
   unescaped entities), `jest.setup.ts`, `e2e/fixtures.ts`, `scripts/*.cjs`
   (`no-require-imports`), setState-in-effect warnings in `ManualSearch`/`theme-toggle`.
   ESLint is not a CI gate today; clean up when touching those files.
3. Email verification exists as an unwired util (`accounts/utils/auth_utils.py`) —
   scheduled for Etapa 2 (see `docs/plan/01` §3).
4. `e2e/fixtures.ts` references seed users (`test@example.com`) that no seed creates yet —
   the storageState globalSetup of It1 will own seeding (docs/plan/06 §5.1).

## Open pending decisions

DP register with statuses lives in `docs/plan/09` §5 (resolved 2026-07-12: DP-01 Wompi,
DP-03 auto, DP-04 lock-never-delete, DP-14 full-MVP launch, DP-21 no Docker).
Still open highlights: DP-02 (OCR engine — recommended ocrmypdf+tesseract), DP-22 (domain +
production SMTP), DP-24 (Ed25519 key custody in production).
