# User Flow Map

**Single source of truth for all user flows in the application.**

Use this document to understand each flow's steps, branching conditions, role restrictions,
and API contracts before writing or reviewing E2E tests. Flow ids map 1:1 to
`frontend/e2e/flow-definitions.json` (v2.0.0) and to the founding-artifact flow ids
(A1…F1) planned in `docs/plan/01-alcance-mvp.md`.

**Version:** 2.0.0
**Last Updated:** 2026-07-12

> Maintenance rule (docs/plan/09 DoD #4): each vertical iteration rewrites the sheets of the
> flows it ships and flips them from *Planned* to *Implemented*. Acceptance criteria live in
> `docs/plan/01-alcance-mvp.md`; this map records the concrete routes/endpoints as built.

---

## Table of Contents

1. [Module Index](#module-index)
2. [Home Module](#home-module)
3. [Auth Module](#auth-module)
4. [Planned Versiona Modules](#planned-versiona-modules)
5. [Cross-Reference](#cross-reference)

---

## Module Index

> **Status governance (2026-07-22)**: since It1 the authoritative status per flow is
> `frontend/e2e/flow-definitions.json` (v2.2.0, 36 flows) + the flow-coverage CI report;
> the audit trail lives in `docs/audit/`. Every flow below is **Implemented** and E2E
> covered unless its row says otherwise — the per-iteration "Planned (ItN)" labels are
> historical.

| Flow ID | Name | Module | Priority | Roles | Frontend Route | Status |
|---------|------|--------|----------|-------|----------------|--------|
| `home-loads` | Landing page loads | home | P1 | shared | `/` | Implemented |
| `auth-sign-in-form` | Sign-in form | auth | P2 | shared | `/sign-in` | Implemented |
| `auth-sign-up-form` | Sign-up form | auth | P1 | shared | `/sign-up` | Implemented |
| `auth-login-invalid` | Invalid credentials rejected | auth | P1 | shared | `/sign-in` | Implemented |
| `auth-protected-redirect` | Protected routes redirect | auth | P1 | guest | `/dashboard` | Implemented |
| `auth-forgot-password-form` | Password recovery | auth | P2 | shared | `/forgot-password` | Implemented |
| `auth-sign-in-success` | Sign-in happy path (real session) | auth | P1 | shared | `/sign-in` → `/projects` (direct, It9) | Implemented (It1) |
| `auth-sign-out` | Sign out ends the session | auth | P2 | user | header (Salir) | Implemented (It1) |
| `auth-admin-login-handoff` | Django admin impersonation handoff | auth | P3 | staff | `/admin-login` | Gap — unit-tested only |
| `help-manual-browse` | Browse the interactive help | home | P3 | shared | `/manual` | Gap — nice-to-have |
| `a1-onboarding-wow` | A1 Sign-up and first wow | onboarding | P1 | guest | `/onboarding` | Planned (It6) |
| `a2-invite-team` | A2 Invite team and roles | org | P1 | admin | `/org/settings`, `/invite/[token]` | Planned (It6) |
| `b1-create-project` | B1 Create a project | projects | P1 | editor | `/projects/new` | Planned (It1) |
| `b2-projects-board` | B2 Projects board | projects | P2 | viewer | `/projects` | Planned (It5; minimal list in It1) |
| `b3-project-settings` | B3 Project configuration | projects | P2 | admin | `/projects/[id]/settings` | Planned (It5) |
| `c1-upload-first` | C1 Upload first document | documents | P1 | editor | `/projects/[id]` | Planned (It1) |
| `c2-upload-version` | C2 Upload a new version | documents | P1 | editor | `/projects/[id]/documents/[docId]` | Planned (It1) |
| `c3-history` | C3 Version history | documents | P2 | viewer | `/projects/[id]/documents/[docId]` | Planned (It1) |
| `d1-request-review` | D1 Request a review | review | P1 | editor | version viewer + `/inbox` | Planned (It4) |
| `d2-assisted-review` | D2 Assisted review | review | P1 | reviewer | version viewer `?review=` | Planned (It4) |
| `d3-anchored-observations` | D3 Anchored observations | review | P1 | reviewer/editor | version viewer | Planned (It4) |
| `d4-seal-approve` | D4 Approve with a seal | review | P1 | reviewer | version viewer (Seals tab) | Planned (It3) |
| `d5-selective-invalidation` | D5 Selective invalidation | review | P1 | system/coordinator | seals panel + `/inbox` | Planned (It3) |
| `e1-compare` | E1 Compare two versions | compare | P1 | viewer | `.../compare/[base]/[target]` | Planned (It2) |
| `e3-configurable-checks` | E3 Configurable checks | compare | P2 | admin | settings + version viewer (Checks tab) | Planned (It5) |
| `f1-billing` | F1 Plan limits + upgrade path (contact) | billing | P2 | owner | 402 sites → UpgradeDialog → `/precios` | Implemented (It7/It9 — no online checkout) |
| `f2-usage-panel` | F2 Usage panel + warnings + trial line | billing | P2 | member | `/org/usage` (header "Plan y uso") | Implemented (It7/It9) |
| `c4-delete-draft` | C4 Delete a draft version | documents | P2 | editor | version timeline | Implemented (It1) |
| `b4-archive-delete` | B4 Archive/delete a project | projects | P2 | admin | project settings + `/org/trash` | Implemented (It1) |
| `a3-account-security` | A3 TOTP 2FA + sessions | auth | P2 | user | `/settings` (Seguridad) | Implemented (It6) |
| `e2-saved-comparisons` | E2 Saved comparisons | compare | P2 | viewer | compare view + project panel | Implemented (It7) |
| `e4-constancia` | E4 Exportable certificate | review | P2 | admin | version viewer (Constancias) | Implemented (It7) |
| `master-e2e-journey` | Master journey (16 steps, 3 users) | master | P1 | all | end-to-end | Implemented (It8) |
| `public-pricing` | Public pricing page | billing | P1 | guest | `/precios` | Implemented (It9) |
| `trial-visibility` | Trial banner + days left | billing | P2 | user | global banner + `/org/usage` | Implemented (It9) |
| `public-compare` | Anonymous public PDF comparison | public | P1 | guest | `/comparar` → `/comparar/[id]` | Implemented (It9) |
| `f3-org-audit` | F3 Org audit log + CSV export | org | P2 | owner/admin | `/org/audit` | Implemented (It7) — **spec gap registered 2026-07-22** |

---

## Home Module

### home-loads

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | shared |
| **Frontend route** | `/` |
| **API endpoints** | none (static landing) + `GET /api/staging-banner/` (global gate) |

**Preconditions:** none.

**Steps:** open the root URL → the headline "El Git de tus documentos" and the sign-up CTA
are visible.

**Spec:** `e2e/public/smoke.spec.ts` (`@flow:home-loads`).

---

## Auth Module

Auth pages are inherited from the template and already functional (JWT + Google + reCAPTCHA).

### auth-sign-in-form / auth-login-invalid

| Field | Value |
|-------|-------|
| **Priority** | P2 / P1 |
| **Roles** | shared |
| **Frontend route** | `/sign-in` |
| **API endpoints** | `POST /api/sign_in/`, `POST /api/google_login/`, `GET /api/google-captcha/site-key/` |

**Steps:** form renders email/password + Google button → invalid credentials show an inline
error and no session cookie is set → valid credentials redirect to `/dashboard`.

**Spec:** `e2e/auth/auth.spec.ts`.

### auth-sign-up-form

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | shared |
| **Frontend route** | `/sign-up` |
| **API endpoints** | `POST /api/sign_up/` |

**Steps:** form renders → mismatched passwords are rejected client-side → successful sign-up
returns tokens. From It6 on, sign-up also auto-creates the personal Organization and triggers
the A1 sample-project job (see `a1-onboarding-wow`).

**Spec:** `e2e/auth/auth.spec.ts`.

### auth-protected-redirect

| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Roles** | guest |
| **Frontend route** | `/dashboard` (guard: `proxy.ts`) |
| **API endpoints** | — |

**Steps:** anonymous visit to a protected route → redirect to `/sign-in?next=`.

**Spec:** `e2e/auth/auth.spec.ts`.

### auth-forgot-password-form

| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Roles** | shared |
| **Frontend route** | `/forgot-password` |
| **API endpoints** | `POST /api/send_passcode/`, `POST /api/verify_passcode_and_reset_password/` |

**Steps:** two-step form → request 6-digit code (valid 15 min) → verify code + set new
password.

**Spec:** `e2e/auth/auth.spec.ts`.

---

## Planned Versiona Modules

The 16 MVP flows (A1…F1) are specified with Given/When/Then acceptance criteria in
`docs/plan/01-alcance-mvp.md`, their screens in `docs/plan/04-frontend.md` §2, their API in
`docs/plan/03-backend.md` §3, and their E2E designs (including the D5 queen test) in
`docs/plan/06-pruebas.md` §5. Each sheet is written into this map by the iteration that ships
it (see the Module Index status column for the target iteration).

---

## Cross-Reference

| Artifact flow | flow-definitions id | Ships in | E2E spec (planned name) |
|---|---|---|---|
| A1 | `a1-onboarding-wow` | It6 | `e2e/app/a1-onboarding-first-wow.spec.ts` |
| A2 | `a2-invite-team` | It6 | `e2e/app/a2-invite-team.spec.ts` |
| B1 | `b1-create-project` | It1 | `e2e/app/b1-create-project.spec.ts` |
| B2 | `b2-projects-board` | It5 | `e2e/app/b2-projects-board.spec.ts` |
| B3 | `b3-project-settings` | It5 | `e2e/app/b3-project-settings.spec.ts` |
| C1 | `c1-upload-first` | It1 | `e2e/app/c1-upload-first-document.spec.ts` |
| C2 | `c2-upload-version` | It1 | `e2e/app/c2-upload-new-version.spec.ts` |
| C3 | `c3-history` | It1 | `e2e/app/c3-version-history.spec.ts` |
| D1 | `d1-request-review` | It4 | `e2e/app/d1-request-review.spec.ts` |
| D2 | `d2-assisted-review` | It4 | `e2e/app/d2-assisted-review.spec.ts` |
| D3 | `d3-anchored-observations` | It4 | `e2e/app/d3-anchored-observations.spec.ts` |
| D4 | `d4-seal-approve` | It3 | `e2e/app/d4-approve-with-seal.spec.ts` |
| D5 | `d5-selective-invalidation` | It3 | `e2e/app/d5-selective-invalidation.spec.ts` |
| E1 | `e1-compare` | It2 | `e2e/app/e1-compare-versions.spec.ts` |
| E3 | `e3-configurable-checks` | It5 | `e2e/app/e3-configurable-checks.spec.ts` |
| F1 | `f1-billing` | It7 | `e2e/app/f1-plan-and-billing.spec.ts` |
