# 00 — Vision

> Planning suite for **Versiona — "the Git of documents"**. This document defines the product
> objective, the measurable success criteria, the domain glossary that **governs every model,
> endpoint and component name**, and what v1 deliberately is NOT. Source of truth for the WHAT:
> the founding product artifact `versiona_saas_diseno.jsx` (tabs 01–06, user flows A1–F3).

## 1. Product objective

Versiona is a SaaS that brings the Git/GitHub workflow to the world that works in PDF: every
upload is an immutable **version**, every re-delivery produces an automatic **comparison** that
shows exactly what changed, reviewers leave **anchored observations** and approve with
cryptographically signed **seals**, and — the crown jewel (flow D5) — when a new version
arrives, only the approvals of the sections that actually changed are invalidated and only
those reviewers are notified. Nobody re-reads a document from scratch again, and nobody loses
track of which version is the approved one. Every design decision in this suite must answer
"does this bring the product closer to being the GitHub of documents?".

The two pains it kills (artifact tab 01): **(1)** re-reading everything on every round because
there is no reliable way to know what changed; **(2)** `final_v3_AHORA_SI.pdf` — the filename
as version control, with no answer to "which approvals still stand after this change?".

## 2. Measurable success criteria

| # | Criterion | Metric | Target | Flow |
|---|---|---|---|---|
| S1 | Activation ("first wow") | Time from sign-up to first real comparison viewed | < 5 min (p50), measured with server-side timestamps emitted by the onboarding wizard | A1 |
| S2 | North-star metric | Re-reading hours saved per week ≈ sections shown as "already reviewed by you" × average reading time per section | Tracked from MVP; grows week over week | D2 |
| S3 | Retention signal | % of projects with ≥ 3 versions (the full cycle lives in Versiona) | Tracked from MVP | C2/C3 |
| S4 | Jewel correctness | **False-preserve rate: 0** (a seal is never kept over a section whose content changed). False-invalidate is acceptable; false-preserve is never | 0, enforced by invariant I7 + property tests | D5 |
| S5 | Engine responsiveness | Comparison available after uploading a new version | < 60 s (p95) for native-text documents | C2/E1 |
| S6 | Selective-notification promise | Reviewers whose seals were preserved receive **zero** notifications on a re-delivery | 0 spurious notifications (asserted in the E2E queen test) | D5 |

## 3. Domain glossary (governs names of models, endpoints and components)

Code identifiers are English; the Spanish term from the founding artifact is kept in
parentheses. Any new model/endpoint/component MUST use these names.

| Term (code identifier) | Spanish (artifact) | Git analog | Precise definition |
|---|---|---|---|
| **Organization** | organización | — | Multi-tenant root: billing subject, member roster, plan limits. A "personal" workspace IS an organization of one (`kind=personal`, auto-created at sign-up, A1). |
| **Project** | proyecto | Repository | The living folder of one procedure/contract/delivery: its documents, its team (per-project roles) and its review rules. |
| **Document** | documento | File under version control | A logical document inside a project whose history is a linear sequence of versions. |
| **DocumentVersion** (version) | versión | Commit | One immutable upload of a document: author, date, message, sha256, file in object storage, sequential number. Never edited, never deleted once analyzed/sealed. |
| **Section** | sección | — | The stable unit of identity inside a document, detected by the engine (headings). Identity survives renames and reordering across versions; it is the unit seals, owners, observations and D5 operate on. |
| **SectionVersion** | contenido de sección por versión | Blob at a commit | The content of a Section at a specific version: normalized text, `body_hash`, page range, bounding boxes. |
| **Comparison** | comparación | Diff | The computed difference between any two versions of a document, classified per section (unchanged / modified / added / removed / renamed-only). |
| **ReviewRequest** | solicitud de revisión | Pull request | The author's "this version is ready, review it": groups the version, its changes, its checks and the conversation; assigns reviewers via section owners. |
| **Seal** | sello | Review + Approve | A reviewer's approval bound to an exact version + the sections it covers + the reviewer identity, signed with Ed25519. Append-only: a Seal row is never updated or deleted. |
| **SealValidityRecord** (validity record / certificate) | constancia | — | The append-only per-version record that says whether a seal is `preserved` (with evidence of WHY it still stands) or `invalidated` (with evidence of WHAT changed). A seal is valid at version N iff an unbroken chain of `preserved` records reaches N (invariant I11). |
| **Check / CheckDefinition / CheckResult** | check / semáforo | CI checks | A configurable, deterministic verification that runs on every new version (section present, required field, expected value), producing green/yellow/red **with evidence** (page + reason). |
| **Traffic light** (aggregate check status) | semáforo automático | Commit status badge | The aggregated check outcome shown on each version. |
| **Observation** (anchored observation) | observación anclada | Issue | A comment anchored to a zone of a page/section, with state `open → answered → resolved`; the thread survives across versions by re-anchoring to its Section. |
| **SectionOwnershipRule** (section owner) | dueños por sección | CODEOWNERS | The rule mapping sections to responsible reviewers. It is what makes selective invalidation and selective notification possible. |
| **Approved version** | versión aprobada | Tag / Release | The version that collected every required seal: frozen, official, the one that gets shared/filed/signed. At most one current approved version per document (I5). |
| **Selective invalidation** | invalidación selectiva | — | Flow D5: on a new version, cross changed sections × sections covered by each seal; preserve untouched seals **with a validity record**, invalidate affected ones, notify only affected reviewers. Conservative bias: when in doubt, invalidate (I7). |
| **Coordinator** | coordinador | — | Not a sixth role: the capability `can_confirm_seal_plan` (project admins + users designated in project config) to confirm a pending invalidation plan when `d5_mode=coordinator` (DP-07). |
| **Section history** | historial por sección | Blame | For any section: in which version it changed and who uploaded that version. |
| **EngineJob** | trabajo de análisis/comparación | CI run | An asynchronous unit of engine work (analysis, comparison, seal review) with states `pending → running → done/failed`, idempotent by natural key. |

## 4. What v1 is NOT

- **No branches.** A document's history is linear, like a real-world procedure. Branches are
  the part of Git that confuses non-technical users (deliberate artifact decision).
- **No external legally-certified e-signature** (no DocuSign/Adobe Sign integration). The Seal
  is an internal approval with cryptographic evidence (Ed25519 over the version hash); the
  exportable certificate is V2 (E4).
- **No drawings/plans.** No vector-plan comparison, no scanned-plan zone maps, no CAD/DXF
  (V2/Future per artifact tab 04). MVP engine scope: native-text PDF + OCR for scans, nothing
  else.
- **No document editing.** Versiona versions and reviews PDFs that are produced elsewhere; it
  is not an editor.
- **No interpretive AI.** Natural-language change summaries and AI checks are V2/Future; MVP
  checks are deterministic only (E3).
- **No public API/webhooks, no SSO, no full audit export** (V2: enterprise stage, artifact
  Etapa 3).
- **No deleting history.** Not even the free plan deletes versions (retention is an access
  restriction — DP-04); version deletion of unsealed drafts is V2 (C4).

## 5. Base reused (template `base_django_react_next_feature`)

This vision builds on the audited template (see `01`–`09` for per-area detail): complete
JWT+Google auth (backend and frontend), Django settings split, DRF + FBV/services conventions,
Zustand/Tailwind/Next 16 frontend base, mature test tooling (pytest/Jest/Playwright +
flow-coverage convention), CI with quality gate. The template's demo e-commerce domain is
removed; its Huey/MySQL/FileSystem storage are replaced by Celery/PostgreSQL/MinIO as fixed
decisions of the mission.

## 6. Open questions (DECISIÓN PENDIENTE)

None specific to the vision. Scope-level pending decisions (flow count discrepancy, launch
cut) live in `01-alcance-mvp.md`; the consolidated DP-01…DP-13 register lives in each affected
document and is summarized in `09-roadmap-ejecucion.md`.
