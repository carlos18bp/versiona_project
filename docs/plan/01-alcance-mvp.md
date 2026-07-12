# 01 — MVP Scope

> Exact list of the flows marked **MVP** in the founding artifact, each with acceptance
> criteria in Given / When / Then form. These criteria are the functional contract: the E2E
> suite (`06-pruebas.md`) implements one spec per flow, and each iteration of the roadmap
> (`09-roadmap-ejecucion.md`) is "done" only when its flows' criteria pass at all three test
> levels.

**MVP = 16 flows**: A1, A2, B1, B2, B3, C1, C2, C3, D1, D2, D3, D4, D5, E1, E3, F1.

Cross-references: data model & invariants (Ix) in `02`, endpoints in `03`, screens in `04`,
engine/D5 algorithm in `05`, pending decisions (DP-xx) consolidated in `09`.

## 1. Base reused

The template already ships sign-up/sign-in (email + Google), token refresh, password reset and
route guards on both sides — A1/A2 start from there instead of from zero. Everything
domain-specific (organizations, projects, versions, engine, seals, billing) is new.

## 2. MVP flows with acceptance criteria

### A1 — Sign-up and first wow moment (actor: new user)

Goal metric: first real comparison in **< 5 minutes** from sign-up (S1).

- **Given** a visitor on the landing page, **when** they create an account with email or
  Google, **then** an account is created, a personal Organization is auto-created and they are
  taken to the onboarding wizard.
- **Given** the onboarding wizard, **when** the user names their organization (or keeps the
  personal workspace), **then** the backend seeds a **sample project** containing one document
  with two versions (the committed PDF fixtures) as an async job, and the wizard shows its
  progress.
- **Given** the sample project is ready, **when** the user opens it, **then** they see a
  working comparison (side-by-side with highlighted changes) **without having uploaded
  anything**.
- **Given** the wizard's final step, **when** the user drags their own PDF, **then** flow C1
  runs on their real document and the elapsed sign-up → first-comparison time is recorded.

### A2 — Invite the team and assign roles (actor: owner / admin)

- **Given** an org or project admin, **when** they invite an email with a role
  (admin / editor / reviewer / viewer), **then** an Invitation with a single-use token is
  created, the plan's seat limit is enforced (I13) and an email is sent.
- **Given** a pending invitation, **when** the invitee accepts (creating an account if
  needed, with the email pre-filled), **then** the org/project memberships are created and the
  invitee lands **directly on the awaiting project**, not on an empty screen.
- **Given** an invited reviewer, **when** they open the project, **then** their capabilities
  match the role matrix in `03-backend.md` (e.g. a viewer cannot create observations).
- **Given** an admin, **when** they change or revoke a member's role, **then** the change
  applies immediately and is audit-logged; removing the last org owner is rejected.

### B1 — Create a project (actor: admin / editor)

- **Given** an org member with permission, **when** they submit name + description only,
  **then** the project is created in ≤ 30 seconds of user effort, the creator becomes project
  admin, and the project is ready to receive its first version (fine configuration is optional
  and deferred to B3).
- **Given** a free-plan org that already has 1 active project, **when** they try to create a
  second one, **then** creation is blocked with an upgrade prompt (F1, I13).

### B2 — List, search and filter projects (actor: all)

- **Given** a user with several projects, **when** they open the board, **then** each project
  card shows its state at a glance: in review / with observations / approved / draft.
- **Given** the board, **when** they filter by state or search by name, **then** results are
  scoped to projects where they are members (I12).
- **Given** indexed documents, **when** they search by **content**, **then** matches come from
  the engine's full-text index over section text (PostgreSQL FTS `spanish`) and link to the
  matching document.

### B3 — Edit project configuration (actor: admin)

- **Given** a project admin, **when** they edit the checklist (add/remove/prioritize checks),
  section owners or approval rules (required seals, `d5_mode`), **then** a NEW
  `ProjectConfigVersion` is created — configuration is never edited in place.
- **Given** existing document versions, **when** configuration changes, **then** those
  versions keep being evaluated against the config version **pinned at their creation**
  (I8): changes rule from the next version on, never retroactively. The UI states this
  explicitly.
- **Given** a non-admin member, **when** they open project settings, **then** access is
  denied (viewer/editor/reviewer see no settings mutation UI).

### C1 — Upload the first document (actor: editor)

- **Given** an empty project, **when** an editor drags a PDF onto the dropzone, **then** the
  two-step upload runs (`upload_intent` → presigned PUT → `complete`), the server validates
  magic bytes + parses the PDF + computes sha256 (I9), and version 1 is created.
- **Given** the created version, **when** the analysis job finishes, **then** the scenario was
  detected (native text vs scanned → OCR with confidence), sections are indexed with stable
  keys, the pinned checklist ran, and the version shows its traffic light. Detection is
  invisible to the user — they only see that it works.
- **Given** an encrypted, corrupted or non-PDF file, **when** upload completes, **then** it is
  rejected with an actionable message and no version is created.

### C2 — Upload a new version ("the commit") (actor: editor)

- **Given** a document with version N, **when** the editor uploads a re-delivery with a
  version message (e.g. "answers reviewer 2's observations"), **then** version N+1 is created
  immutably (I1, I2) and analysis + comparison against N run automatically.
- **Given** the analysis finished, **when** the editor views the post-upload summary, **then**
  within seconds (S5) they see: which sections changed, which checks changed color, and which
  seals are affected (input of D5).
- **Given** a binary identical to the current version (same sha256), **when** upload
  completes, **then** it is rejected as a duplicate (edge case F6).
- **Given** an analysis failure, **when** the editor opens the timeline, **then** the failed
  version shows a readable cause and a retry action; existing seals are untouched (D5 did not
  run) and the next successful version compares against the last analyzed one.

### C3 — Browse the history (actor: all)

- **Given** a document with versions, **when** any member opens it, **then** they see the
  timeline: every version with author, date, message, traffic light and (if any) the approved
  badge — visual proof the history is safe.
- **Given** the timeline, **when** they download any historical version, **then** they get the
  exact original binary through a signed URL with short TTL, and the download is audit-logged.
- **Given** the timeline, **when** they pick any two versions, **then** they jump to the
  comparison screen (E1).

### D1 — Request a review (actor: editor)

- **Given** an analyzed version, **when** the author opens a review request ("ready for
  review"), **then** reviewers are auto-suggested/assigned from the section owners of the
  pinned config, each with the scope of sections that concern them.
- **Given** assigned reviewers, **when** the request is created, **then** each one is notified
  (email, MVP) and the request appears in their inbox with **what concerns them** — the
  version, its changes, its checks and the conversation grouped in one thread.

### D2 — Review with assistance (actor: reviewer)

- **Given** a review request, **when** the reviewer opens it, **then** they see FIRST the
  checks traffic light and the change summary, before any page rendering.
- **Given** the change list, **when** they navigate, **then** they can jump directly to
  changed sections or to sections with red checks.
- **Given** a reviewer with a previous seal on this document, **when** they review a newer
  version, **then** every section unchanged since their last seal is marked **"already
  reviewed by you"** — this is where the product's promise (S2) is paid.

### D3 — Anchored observations (actor: reviewer)

- **Given** the version viewer, **when** a reviewer selects a zone of a page and comments,
  **then** an Observation anchored to that zone (page + normalized bbox) and to its Section is
  created in state `open`, and the author is notified.
- **Given** an open observation, **when** the author replies or uploads a version that fixes
  it, **then** the thread stays anchored to the zone/section: on each new version the anchor
  is re-computed (re-anchored to the section, or flagged `orphaned` if the section vanished) —
  observations survive across versions.
- **Given** the observations panel, **when** the user filters by reviewer or state
  (`open / answered / resolved`), **then** only matching threads are shown; state transitions
  follow the machine in I14.

### D4 — Approve with a seal (actor: reviewer)

- **Given** an assigned reviewer on the latest analyzed version, **when** they approve with
  one click, **then** a Seal is created recording who, when, the **exact version** (its
  sha256) and the sections it covers, signed with Ed25519 (I6); seals are append-only (I4).
- **Given** a version, **when** all seals required by the pinned approval policy are in place,
  **then** the version becomes the **approved version**: frozen, badged, and the single
  current approved version of the document (I5).
- **Given** a viewer or editor, **when** they attempt to seal, **then** the API returns
  403/404 per the role matrix; only the latest analyzed version can be sealed (I10).

### D5 — Re-delivery and selective invalidation (actor: system + coordinator) — THE JEWEL

- **Given** a document whose version N has seals, **when** version N+1 is uploaded and
  analyzed, **then** the engine crosses **which sections changed** against **which sections
  each seal covers** (the section/check/reviewer matrix from `05`).
- **Given** a seal whose covered sections are ALL unchanged (equal normalized `body_hash`,
  equivalent heading), **then** it is **preserved** and a `SealValidityRecord(preserved)` is
  written with the evidence of why it still stands (verified hashes, comparison id) — the
  validity record/constancia.
- **Given** a seal with at least one covered section modified/removed (or any ambiguous
  match, or a `covers_all` seal with any change), **then** it transitions to **requires
  re-review** (`invalidated` record with evidence of what changed) — never silently kept
  (conservative bias I7; success criterion S4: zero false-preserves).
- **Given** the invalidation outcome, **when** notifications go out, **then** ONLY the
  affected reviewers receive one grouped notification each, with links to the exact diffs of
  their sections and a re-review assignment scoped to them; preserved reviewers receive
  **nothing** (S6).
- **Given** `d5_mode=coordinator` in the pinned config (or forced by degraded/low-OCR mode),
  **when** the plan is computed, **then** records are created as `pending_confirmation` with a
  proposed decision and evidence; a coordinator (DP-07) confirms/adjusts row by row before
  anything applies; approval and new seals are blocked meanwhile. With `d5_mode=auto`, records
  are final immediately.

### E1 — Compare any two versions (actor: all) — the star screen

- **Given** a document history, **when** the user picks versions X and Y (any pair), **then**
  a Comparison is served from cache (unique per pair) or computed as a job with visible
  progress.
- **Given** a computed comparison, **when** the user opens it, **then** three views are
  available: **side-by-side** (synchronized by section, changes highlighted on the pages),
  **modified-sections list** (with direct access), and **summary**; navigation preserves the
  active section and each change deep-links to the exact spot in the document.
- **Given** two identical versions, **when** compared, **then** an explicit "no changes" state
  is shown (not an empty diff).

### E3 — Configure and run checks (actor: admin / system)

- **Given** a project admin, **when** they build the checklist (section present, required
  fields, expected values), **then** definitions are stored under a new config version (B3
  rules apply).
- **Given** a new version, **when** analysis runs, **then** the checks from the **pinned**
  config run automatically and produce a traffic light where every result carries evidence:
  on which page and why (green/yellow/red).
- **Given** a check result, **when** the user clicks its evidence, **then** the viewer jumps
  to the referenced page/zone. MVP checks are deterministic only; interpretive AI checks are
  V2.

### F1 — Choose a plan and pay (actor: owner)

- **Given** a new org, **when** it is created, **then** it starts on the Free plan with clear
  limits: 1 active project, 2 users, 30-day history access (limits live in `Plan.limits`,
  enforced at action time — I13; history restriction is access-only, never deletion — DP-04).
- **Given** a free org at a limit, **when** the owner hits it (second project, third user),
  **then** a self-service upgrade with card payment is offered (gateway per DP-01) and, on
  success, the limit is lifted immediately.
- **Given** a paying org, **when** the owner opens billing, **then** they can see plan,
  usage vs limits and download invoices.
- **Given** a gateway webhook event, **when** it arrives, **then** it is verified by
  signature, processed idempotently by event id, and reflected in the subscription state.

## 3. Explicitly out of the MVP (and when it enters)

Mapped to the artifact's construction stages (tab 06): Etapa 2 = "the full jewel"
hardening, Etapa 3 = "open the doors" (enterprise/API), Etapa 4 = intelligence.

| Flow / feature | Priority in artifact | Enters at |
|---|---|---|
| A3 — 2FA, session management, corporate SSO | V2 | 2FA/security: Etapa 2–3; SSO: Etapa 3 (first enterprise customers) |
| B4 — Archive & delete project (30-day grace, written confirmation) | V2 | Etapa 2 |
| C4 — Delete a draft version (never sealed ones) | V2 | Etapa 2 |
| E2 — Saved & shared comparisons (named comparison objects) | V2 | Etapa 2 |
| E4 — Exportable certificate (version history + seals + signatures PDF) | V2 | Etapa 2–3 (builds on Ed25519 seals + `seal_keys` endpoint shipped in MVP) |
| F2 — Usage & limits panel with proactive warnings | V2 | Etapa 2 |
| F3 — Full audit trail UI + export (who viewed/downloaded/approved) | V2 | Etapa 3 (the `AuditEvent` base ships in MVP — see `08`) |
| Approval ordering rules (how many seals, in what order) | V2 | Etapa 2 (MVP: required-seals set from section owners) |
| NL change summaries (AI), interpretive checks | V2/Future | Etapa 4 |
| Vector plans, scanned plans, CAD/DXF, plan vision | V2/Future | Etapa 3–4 (documented as engine extensions in `05`, not planned in detail) |
| Public API & webhooks, self-hosted plan | V2 | Etapa 3 (compose-first infra in `07` is the enabler) |
| Email verification at sign-up | — (template gap) | Etapa 2 (template ships the util unwired; not needed for the MVP wow) |

## 4. Open questions (DECISIÓN PENDIENTE)

| ID | Question | Options / Recommendation |
|---|---|---|
| DP-13 | **Flow count discrepancy**: the mission prompt says "19 user flows" but the artifact enumerates **23** (A:3, B:4, C:4, D:5, E:4, F:3). This suite follows the artifact (source of truth on the WHAT). | Confirm the artifact governs; if 4 flows were meant to be dropped, name them. |
| DP-14 | **Launch cut**: the artifact marks 16 flows as MVP (including D5, E3, OCR, F1), but its Etapa 1 (6–8 weeks) says "basic seals" and leaves "the full jewel" to Etapa 2. Is the first public release end-of-Etapa-1 (without full D5) or end of the full MVP roadmap (It0–It7 in `09`)? | Recommendation: treat "MVP" = the 16 flows (the artifact's own MVP rule demands the jewel working); use Etapa 1 as an internal milestone, not a public launch. |
| DP-01 | F1 payment gateway (blocks It7 detail design). | See `09` — Mercado Pago recommended behind a `PaymentGateway` adapter. |
