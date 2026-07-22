# Tasks Plan — Versiona

> Memory Bank core file: backlog, progress and known issues. The authoritative roadmap is
> `docs/plan/09-roadmap-ejecucion.md` (vertical iterations, DoD, DP register); the closure
> audit lives in `docs/audit/05-cierre.md`.

## Iteration backlog (vertical — each ships flows end to end)

| It | Flows | Status |
|---|---|---|
| 0 — Bootstrap | infra + skeleton + purge + fixtures + CI | ✅ DONE 2026-07-12 |
| 1 — Document core | C1, C2, C3, B1 (+B2 minimal) | ✅ DONE 2026-07-12 |
| 2 — Comparison (star screen) | E1 | ✅ DONE 2026-07-12 |
| 3 — Seals + **D5 (jewel)** | D4, D5 | ✅ DONE 2026-07-12 |
| 4 — Collaborative review | D1, D2, D3 | ✅ DONE 2026-07-12 |
| 5 — Governance + OCR | B3, E3, B2, OCR (It5) | ✅ DONE 2026-07-12 |
| 6 — Onboarding wow + team + 2FA | A1, A2, A3 (TOTP) | ✅ DONE 2026-07-12 |
| 7 — Monetization + hardening | F1 limits, F2, F3, E2, E4 | ✅ DONE 2026-07-12 |
| 8 — Hardening + master journey | 16-step serial E2E | ✅ DONE 2026-07-12 |
| 9 — Freemium go-public prep | trial Pro 14d, landing/precios, /comparar público, CI verde | ✅ **DONE 2026-07-22** |

**MVP feature-complete**: 19 flows E2E green (`docs/audit/05-cierre.md` "MISIÓN
CUMPLIDA") + It9 public surfaces. Flow contract: `frontend/e2e/flow-definitions.json`
v2.2.0 (36 flows).

## It9 delivered (2026-07-22) — freemium à la iLovePDF

- **Trial**: every new personal org auto-starts a 14-day Pro trial
  (`billing.Subscription`); effective plan = console override > active trial > free,
  resolved lazily (`billing.services.effective_plan`); daily beat task
  `billing-trials-daily` flips expiries + sends T-3/expiry owner notices (idempotent).
- **Public API**: `GET /api/public/plans/` (AllowAny + anon throttle) and the anonymous
  comparator `POST/GET /api/public/comparisons/` (new bounded-context app
  `public_tools`: 10MB/100-page caps, no OCR → 422 upsell, ephemeral MinIO files deleted
  after processing, 24h TTL results + hourly purge, per-IP SimpleRateThrottles).
- **Frontend**: landing revamp (dual CTA → /comparar + trial signup, features grid, tech
  strip, pricing preview, FAQ, real public header/footer + LocaleToggle), /precios with
  live catalog + static fallback, /comparar + /comparar/[id] (shareable result),
  TrialBanner, reusable UpgradeDialog wired to the three 402 sites, sign-in i18n fixes,
  direct /projects redirect, /org/usage de-orphaned.
- **CI green**: tesseract/ghostscript in backend job, mailpit service + SMTP env in e2e
  job, b3 race fix, a11y networkidle removal, quality-gate parser fixes
  (test.use/slow, template titles, pytest.raises).

## Known issues (non-blocking)

1. **Pre-existing tsc error** in `frontend/lib/services/__tests__/http.test.ts`
   (mock typing) — `npx tsc --noEmit` fails on that file only.
2. **Pre-existing ESLint errors** in template files (auth pages, jest.setup, scripts) —
   ESLint is not a CI gate; clean up when touching those files.
3. Email verification exists as an unwired util (`accounts/utils/auth_utils.py`) —
   Etapa 2.
4. `UploadThrottle` (`documents/views.py:24`) is INERT — ScopedRateThrottle never
   resolves on FBVs. Fixing it would rate-limit the E2E suite in CI (20/hour); needs a
   deliberate design (higher rate + SimpleRateThrottle) before enabling.
5. DRF throttles count per-process (locmem cache) — back them with Redis before real
   traffic; verify nginx X-Forwarded-For/NUM_PROXIES at deploy time.
6. nginx `client_max_body_size` must admit ~25 MB on `/api/public/` (first
   Django-mediated upload surface) when deployment lands.

## Open pending decisions (operator-gated — the gap between "built" and "public")

1. **DP-21/DP-22**: production deployment (nginx/systemd/SSL for gunicorn+celery) +
   domain + production SMTP — deliberately deferred; required to launch.
2. **Wompi keys (DP-01)**: checkout leg unbuilt on purpose; upgrade beyond trial is by
   contact (hola@versiona.app). Trial + limits + pricing work without payments.
3. **DP-24**: Ed25519 signing-key custody + rotation of the dev key that leaked into
   git history (operator chose local rotation over history rewrite).
4. **A3 SSO**: deferred pending IdP.
