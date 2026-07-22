# Active Context — Versiona

> Memory Bank core file: current focus, recent changes, next steps. Updated every session
> that changes project state.

**Last updated**: 2026-07-22

## Current focus

**It9 (freemium go-public prep) shipped and the full product (It0–It9) merged to
`master` via PR #1.** The MVP is feature-complete AND market-shaped: iLovePDF-style
freemium with a 14-day Pro trial on signup, public landing + /precios, and the anonymous
comparator /comparar as the acquisition hook. CI is green end to end (backend, unit,
e2e with mailpit, quality gate).

## What a fresh session should know

- Plan state: `Organization.plan` (console override, always wins) +
  `billing.Subscription` (trial). Read plans ONLY through
  `billing.services.effective_plan` / `usage_report`.
- The ONLY AllowAny surfaces: auth, invitation_state, `GET /api/public/plans/`,
  `POST/GET /api/public/comparisons/` (app `public_tools`, ephemeral by design).
- Engine's `analyze_bytes(data, allow_ocr=True)`: the flag exists for the anonymous
  comparator; authed paths never pass it explicitly (byte-identical behavior).
- Frontend public routes: `/`, `/precios`, `/comparar[/:id]`, `/manual`, auth pages.
  `publicApi` (no interceptors) is the client for AllowAny endpoints.
- Flow contract: `frontend/e2e/flow-definitions.json` v2.2.0 — 36 flows; f1-billing is
  honestly scoped (no online checkout).

## Next steps (operator-gated — in order of launch impact)

1. Execute deferred deployment (DP-21): nginx + systemd (gunicorn/celery/beat) + SSL.
2. DP-22: domain + production SMTP (today only mailpit dev).
3. Rotate the Ed25519 dev signing key + secret-manager custody (DP-24) — before the
   first regulated customer.
4. Wompi keys → build the checkout leg over the existing trial/limits scaffolding (F1
   payment; webhook throttle scope already reserved).
5. Optional growth (It10 candidates): public certificate verification page
   (/verificar/<code> + QR — the trust/viral loop deferred from It9), SSO (A3),
   Redis-backed throttles, annual pricing.

## Recent decisions to keep in mind

- Trial: 14 days (settings.BILLING_TRIAL_DAYS), auto-start on personal-org creation
  ONLY (existing orgs never get one retroactively); expiry is lazy + daily beat
  `billing-trials-daily` (13:00 UTC ≈ 08:00 Bogotá) for notices.
- Anonymous comparator: files are EPHEMERAL (deleted in the task's finally + hourly
  purge), results expire in 24h; no OCR for anonymous users (422 upsell instead).
- Free limits unchanged (1 project / 2 members / 30-day history, DP-04 lock-never-
  delete) — no new metering this cycle by operator decision (2026-07-22).
- No fake trust signals on marketing surfaces (operator-aligned honesty rule).
