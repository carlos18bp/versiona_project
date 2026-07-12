# 06 — Test Design (before the code)

> Complete test strategy per level (backend unit, frontend unit, API integration, E2E), the
> traceability matrix flow → tests, the PDF fixtures that must be fabricated (with a documented
> truth table so engine results can be asserted **exactly**), and the coverage thresholds.
> Per the mission, tests are designed BEFORE the code: every iteration in
> `09-roadmap-ejecucion.md` is done only when its rows in this document are green.

## 1. Base reused

- **Backend**: pytest + pytest-django + factory-boy + freezegun; test layout by layer
  (`tests/{models,services,views,commands,utils}`); DRF fixtures in `conftest.py`
  (`api_client`, `authenticated_client`, `admin_client`) — extended, not replaced; custom
  coverage reporter; `docs/TESTING_QUALITY_STANDARDS.md` rules (one behavior per test, no
  conjunctions in names, AAA, parametrize instead of conditionals, deterministic time via
  freezegun, mocks only at system boundaries) enforced by `scripts/test_quality_gate.py` in CI
  and pre-commit.
- **Frontend unit**: **Jest 30 + RTL stays** (explicit decision: the mission mentions
  "Vitest/Jest"; the template integrates Jest with `next/jest`, coverage summary scripts and
  CI — migrating to Vitest would cost the whole pipeline for no functional gain).
- **E2E**: Playwright + the template's flow-coverage convention: `e2e/flow-definitions.json`
  (source of truth), `@flow:/@module:/@priority:` tags (`e2e/helpers/flow-tags.ts`),
  `flow-coverage-reporter.mjs`, `docs/USER_FLOW_MAP.md`, per-module runners. The 34 e-commerce
  flows are replaced by the Versiona set (§5.3).

## 2. Backend unit tests (pytest)

| Proposed file | Verifies (case classes) |
|---|---|
| `tests/models/test_version_model.py` | **Immutability** (I2/I3): mutating file/hash/message after `ready` raises; DELETE always raises; `version_number` sequential per document with no gaps (I1, incl. a concurrency test); sha256 uniqueness per document (F6). |
| `tests/models/test_seal_model.py` | Seal bound to (version, reviewer, sections[]); append-only (I4); `unique(version, reviewer)`; illegal `SealValidityRecord` transitions rejected (only `pending → final`); validity chain function `seal_is_valid_at` (I11) over crafted chains. |
| `tests/models/test_observation_model.py` | Normalized bbox validation (0–1); state machine `open→answered→resolved→open` (I14); one anchor per version. |
| `tests/models/test_organization_model.py` · `test_project_model.py` · `test_membership_model.py` | Personal org auto-creation (A1); ≥1 owner guard (A2); effective-role resolution org→project (`03` §5); derived project state (B2). |
| `tests/models/test_project_config_model.py` | ProjectConfigVersion immutability; new row per edit (B3); version pinning (I8). |
| `tests/services/test_invalidation_service.py` | **D5 as a PURE FUNCTION** `resolve_seal_invalidation(seals_prev, changed_sections, mode) → {preserved[], invalidated[], pending[], notify[]}`, heavily `@pytest.mark.parametrize`d: no changes → all preserved with records; section of seal A changes → only A invalidated and only A notified; multi-section seal with 1 changed section → invalidated (partial record of intact ones); sealed section removed → invalidated; new section → no effect on prior seals; `covers_all` + any change → invalidated; `mode=coordinator` → output is a pending proposal (nothing applied); `mode=auto` → applied; determinism (same input ⇒ same output). **Property test: no input reaches `preserved` without body-hash equality (I7/S4).** |
| `tests/services/test_section_matching_service.py` | Matching (`05` §4): equal heading → match; renumbered (6 removed shifts 7→6) → match by title not number; added; removed; slightly edited heading (similarity band); ambiguity → new identity; parametrized against the fixture truth table (§6). |
| `tests/services/test_comparison_service.py` | Exact classification unchanged/modified/added/removed against `contrato_v1/v2`; highlight bboxes emitted; idempotent by pair (I15). |
| `tests/services/test_pdf_analysis_service.py` | Scenario detection native vs scanned; 8 sections indexed from `contrato_v1`; rejection of protected PDF and non-PDF (magic bytes); page-fallback on `sin_encabezados.pdf` (DP-09); normalized-text hashing stable across re-render. |
| `tests/services/test_check_engine.py` | E3: each check type (section_present, field_required, expected_value, page_count_range) with evidence `{page, reason}`; new check does not apply retroactively (I8). |
| `tests/services/test_approval_service.py` | All required seals valid → version approved + frozen (I5); rules evaluated from the pinned config; revoke pre-approval recomputes (DP-08). |
| `tests/services/test_billing_limits_service.py` | F1/I13: 2nd active project blocked on free; 3rd member blocked; >30-day versions `locked` not deleted (DP-04); file-size limit per plan (DP-11). |
| `tests/services/test_reanchor_service.py` | D3: anchor recomputed per new version; `orphaned` when the section retired; snippet-based re-anchor. |
| `tests/utils/test_pdf_hashes.py` · `test_signed_urls.py` · `test_seal_signature.py` | Stable sha256; signed URL TTL + non-guessable; Ed25519 canonical payload signs/verifies; tampered payload fails (I6/I9). |

## 3. Frontend unit tests (Jest 30 + RTL)

| Spec (template pattern: `__tests__/` next to code) | Behaviors |
|---|---|
| `components/review/seals/__tests__/SealsPanel.test.tsx` | Renders the validity states (valid / invalidated–requires re-review / preserved-with-record / pending confirmation) with correct badges; the record shows origin version + date; seal CTA only for an assigned reviewer with pending scope; coordinator card shows Confirm/Reject only with a pending plan. |
| `components/compare/__tests__/SectionChangeList.test.tsx` | Click emits navigation with the section key; icon per change type; "hide unchanged" toggle. |
| `components/versions/__tests__/UploadDropzone.test.tsx` | Rejects non-PDF extension; rejects > max size; shows upload %; job phase transitions pending→running→done; failed shows reason + retry. |
| `components/review/checks/__tests__/ChecksTrafficLight.test.tsx` | Aggregate color; evidence link navigates to page. |
| `components/review/observations/__tests__/ObservationThread.test.tsx` | States; reply; reviewer/state filters. |
| `components/onboarding/__tests__/OnboardingWizard.test.tsx` | Step advance; cannot skip org naming; resumes persisted progress (A1). |
| `lib/stores/__tests__/jobStore.test.ts` | Polling with `jest.useFakeTimers()`: 2 s → backoff ×1.5 → cap 10 s; stops on done/failed; 5-min timeout. |
| `lib/stores/__tests__/{sealStore,compareStore,projectStore,orgStore}.test.ts` | Template store pattern: fetch/error/selectors. |
| `lib/pdf/__tests__/coords.test.ts` · `lib/compare/__tests__/sync.test.ts` | Pure functions bbox→CSS and section→offset mapping — target 100%. |

## 4. API integration tests (pytest)

New fixtures layered on the template's `conftest.py`: `org_factory`, `project_factory`,
`document_with_versions` (uses the PDF fixtures), and a parameterizable **`client_as(role)`**
(owner / admin / editor / reviewer / viewer / non-member / anonymous).

Pattern: one file per resource — `tests/views/test_<resource>_endpoints.py` — with a
`@pytest.mark.parametrize('role, expected', [...])` matrix asserting
**200/201 · 401 (anonymous) · 403 (insufficient role) · 404 (non-member or foreign object —
I12)** for every endpoint in `03-backend.md` §3. Celery runs `task_always_eager` here.

Named high-value cases: `POST seals` as viewer → 403; `seal_plan/confirm` as non-designated
reviewer → 403; upload `complete/` over an approved document's version → 409; 2nd project on
free plan → 402/409; `download/` of a `locked` version → 403 + upgrade hint; webhook with bad
signature → 400; foreign-org object by UUID → 404.

## 5. E2E (Playwright) — one spec per MVP flow

### 5.1 Auth solution (closes a template gap)

Playwright `globalSetup`: (1) run the deterministic seed (`create_fake_data --scenario=e2e`);
(2) log in **via API** (`POST /api/sign_in/`) for each role and persist `storageState`
(cookie-based tokens) into `e2e/.auth/{owner,admin,editor,reviewer,viewer}.json` (gitignored);
specs declare `test.use({ storageState: 'e2e/.auth/editor.json' })`. Helper
`e2e/helpers/auth.ts` for ad-hoc logins (A1 registers fresh, no storageState).

### 5.2 Spec table

| Flow | Spec (`e2e/app/`) | Given / When / Then (summary) | Tags |
|---|---|---|---|
| A1 | `a1-onboarding-first-wow.spec.ts` | Guest signs up → names org → waits for sample-project job → **sees a comparison with highlighted changes without uploading anything** → uploads own PDF (fixture) → v1 with traffic light | `@flow:a1-onboarding-wow @module:onboarding @priority:P1` |
| A2 | `a2-invite-team.spec.ts` | Admin invites email+role reviewer → captures link via mailpit API → new context accepts → lands directly on the project with reviewer capabilities | `@flow:a2-invite-team` P1 |
| B1 | `b1-create-project.spec.ts` | Editor creates a project with name only → lands on empty project with dropzone | `@flow:b1-create-project` P1 |
| B2 | `b2-projects-board.spec.ts` | Seed with 3 projects in different states → correct badges, state filter, search by name and by content | `@flow:b2-projects-board` P2 |
| B3 | `b3-project-settings.spec.ts` | Admin edits checklist + section owners → saves → non-retroactivity notice; viewer sees no settings | `@flow:b3-project-settings` P2 |
| C1 | `c1-upload-first-document.spec.ts` | Drag&drop `contrato_v1.pdf` → job progresses → v1 with 8 indexed sections and traffic light | `@flow:c1-upload-first` P1 |
| C2 | `c2-upload-new-version.spec.ts` | Uploads `contrato_v2.pdf` with a message → within seconds PostUploadSummary: changed sections / checks / affected seals | `@flow:c2-upload-version` P1 |
| C3 | `c3-version-history.spec.ts` | Timeline with author/date/message → download responds 200 via signed URL → selects v1+v2 → lands on compare | `@flow:c3-history` P2 |
| D1 | `d1-request-review.spec.ts` | Editor requests review → reviewer auto-suggested from section owner → reviewer's inbox shows the assignment | `@flow:d1-request-review` P1 |
| D2 | `d2-assisted-review.spec.ts` | Reviewer opens from inbox → sees traffic light + change summary first → jumps to changed sections → unchanged-since-my-seal sections show "already reviewed by you" | `@flow:d2-assisted-review` P1 |
| D3 | `d3-anchored-observations.spec.ts` | Reviewer selects a zone → comments → editor replies → reviewer marks resolved; state filters | `@flow:d3-observations` P1 |
| D4 | `d4-approve-with-seal.spec.ts` | Reviewer seals in one click → panel shows placed/missing → second reviewer seals → version approved + frozen + badge | `@flow:d4-seal-approve` P1 |
| **D5** | `d5-selective-invalidation.spec.ts` | **Queen test — §5.4** | `@flow:d5-selective-invalidation` P1 |
| E1 | `e1-compare-versions.spec.ts` | Compares v1↔v2: side-by-side with highlights, section list matching the truth table **exactly**, summary; navigation across the three views | `@flow:e1-compare` P1 |
| E3 | `e3-configurable-checks.spec.ts` | Admin adds a check → next version runs it → traffic light with evidence (page+reason) navigable | `@flow:e3-checks` P2 |
| F1 | `f1-plan-and-billing.spec.ts` | Free org with 1 project tries a 2nd → limit modal → upgrade (gateway in test/mock mode) → creates 2nd project → invoice listed | `@flow:f1-billing` P2 |

### 5.3 Flow-coverage convention updates

`e2e/flow-definitions.json` bumps to **v2.0.0**: the 34 e-commerce flows are deleted; enter
the 16 MVP flows above + 4 kept auth flows (`auth-sign-in-form`, `auth-login-invalid`,
`auth-protected-redirect`, `auth-forgot-password-form`) = **20 flows**, same schema
`{name, module, roles, priority, description, expectedSpecs}` with modules
`onboarding | org | projects | documents | review | compare | billing | auth`.
`flow-tags.ts` is rewritten with the new constants (same triple-tag format).
`docs/USER_FLOW_MAP.md` is rewritten with the same verified structure (Module Index + one
sheet per flow with Preconditions/API endpoints) — updated **per iteration**, not big-bang.
The reporter and `scripts/e2e-module*.cjs` runners work unchanged.

### 5.4 The queen test — D5 end to end (multi-user)

Three `browser.newContext()` with distinct storageStates. Asserts the truth table (§6)
**exactly**, plus the selective-notification promise via the mailpit REST API.

- **Given** (API-driven seed): project with `contrato_v1.pdf` analyzed (8 sections);
  reviewer A holds a valid seal over sections {1, 2}; reviewer B over {3, 7};
  `d5_mode=coordinator`; coordinator = admin.
- **When**: the Editor context uploads `contrato_v2.pdf` (modifies 3 and 5, removes 6, adds
  "Protección de Datos Personales") and waits for `job=done`.
- **Then**:
  1. PostUploadSummary: "2 modified, 1 removed, 1 added; 1 seal affected".
  2. Coordinator context: inbox shows the pending invalidation plan; opens it, sees
     per-section evidence (diff of section 3), confirms.
  3. Reviewer B context: inbox shows "requires re-review" citing section 3 (7 stayed intact,
     but the seal covered 3 → seal invalidated, with partial record of 7); mailpit holds an
     email **only for B**.
  4. Reviewer A context: empty inbox; the v2 SealsPanel shows their seal
     `preserved-with-record` (origin v1 + date + verified hashes); mailpit has **no** email
     for A (S6).
  5. Second test in the same spec repeats the scenario with `d5_mode=auto`: no coordinator
     step; records final immediately.

Flake control: API-driven setup (no UI seeding), mailpit polled via API, CI `retries: 2`
(template default), per-document job serialization guarantees ordering.

## 6. PDF fixtures to fabricate (critical)

**Tool**: `reportlab` (pure Python, deterministic — fixed metadata/dates so bytes are
reproducible). **Location**: `testdata/pdfs/` + generator `testdata/generate_pdfs.py` — one
source consumed by pytest, Playwright (`setInputFiles`) **and** `create_fake_data` (the A1
sample project uses the very same contrato v1/v2 → demo and tests can never drift).
**Policy**: commit the script AND the generated PDFs (identical bytes everywhere → exact hash
and count assertions; regeneration only via the script in a PR that updates this truth table;
~100–300 KB total).

`contrato_v1.pdf` — native text, ~4 pages, numbered Heading-1 sections, 2–3 deterministic
paragraphs each:
**1. OBJETO DEL CONTRATO · 2. DEFINICIONES · 3. OBLIGACIONES DEL CONTRATISTA ·
4. OBLIGACIONES DEL CONTRATANTE · 5. VALOR Y FORMA DE PAGO · 6. PLAZO DE EJECUCIÓN ·
7. CONFIDENCIALIDAD · 8. RESOLUCIÓN DE CONTROVERSIAS**

`contrato_v2.pdf` — **the truth table** (the exact contract for engine, D5 and E2E
assertions):

| v1 section | Change in v2 | Expected engine result | D5 effect on a covering seal |
|---|---|---|---|
| 1. Objeto | none | unchanged | preserved w/ record |
| 2. Definiciones | none | unchanged | preserved w/ record |
| 3. Obligaciones del contratista | paragraph 2 replaced (penalty 2% → 5%) | **modified** | **invalidated / re-review** |
| 4. Obligaciones del contratante | none | unchanged | preserved |
| 5. Valor y forma de pago | amount $100M → $120M | **modified** | invalidated |
| 6. Plazo de ejecución | **removed** | **removed** | invalidated |
| 7. Confidencialidad | same text, renumbered → 6 | unchanged (match by title, not number) | preserved |
| 8. Resolución de controversias | same text, renumbered → 7 | unchanged | preserved |
| — | **added** "8. PROTECCIÓN DE DATOS PERSONALES" | **added** | n/a (no prior seal) |

Edge fixtures: `escaneado_v1.pdf` (raster of v1 — render pages to images, rebuild PDF without
text layer; the OCR path, C1); `sin_encabezados.pdf` (headless prose → page-fallback, DP-09);
`protegido.pdf` (password → clean rejection); `corrupto.pdf` (bad magic bytes → rejection);
`grande_stub.pdf` (> size limit, generated inside the test, not committed).

## 7. Traceability matrix (flow → tests per level)

| Flow | Backend unit | Frontend unit | API integration | E2E |
|---|---|---|---|---|
| A1 | `test_organization_model`, seed service | `OnboardingWizard.test` | `test_org_endpoints`, `test_sample_project_endpoint` | `a1-onboarding-first-wow` |
| A2 | `test_membership_model` | `InviteForm.test` | `test_invitation_endpoints` (role matrix) | `a2-invite-team` |
| B1 | `test_project_model` | `ProjectForm.test` | `test_project_endpoints` | `b1-create-project` |
| B2 | derived state in `test_project_model` | `ProjectsBoard.test`, `projectStore.test` | `test_project_search_endpoints` | `b2-projects-board` |
| B3 | `test_project_config_model`, `test_check_engine` (non-retroactive) | `SettingsTabs.test` | `test_project_settings_endpoints` | `b3-project-settings` |
| C1 | `test_pdf_analysis_service` | `UploadDropzone.test` | `test_document_upload_endpoints` | `c1-upload-first-document` |
| C2 | `test_version_model` (immutability/sequence) | `UploadDropzone`, `PostUploadSummary.test` | `test_version_endpoints` | `c2-upload-new-version` |
| C3 | section history in `test_section_matching_service` | `VersionTimeline.test` | `test_history_download_endpoints` (signed URL) | `c3-version-history` |
| D1 | owner-based assignment (review service) | `ReviewRequestPanel.test` | `test_review_request_endpoints` | `d1-request-review` |
| D2 | progress service | `ReviewContextBar.test` | `test_review_progress_endpoints` | `d2-assisted-review` |
| D3 | `test_observation_model`, `test_reanchor_service` | `ObservationThread.test`, `RegionSelector.test` | `test_observation_endpoints` | `d3-anchored-observations` |
| D4 | `test_seal_model`, `test_approval_service`, `test_seal_signature` | `SealsPanel.test` | `test_seal_endpoints` | `d4-approve-with-seal` |
| **D5** | ✔✔ `test_invalidation_service` (parametrized core + property test) | `SealCard` states, `InvalidationReviewCard.test` | `test_seal_plan_endpoints` | ✔✔ `d5-selective-invalidation` (queen) |
| E1 | `test_comparison_service`, `test_section_matching_service` | `SectionChangeList`, `sync.test`, `coords.test` | `test_comparison_endpoints` | `e1-compare-versions` |
| E3 | `test_check_engine` | `ChecksTrafficLight.test` | `test_checklist_endpoints` | `e3-configurable-checks` |
| F1 | `test_billing_limits_service` | `BillingPanel`, `UsageMeter.test` | `test_billing_endpoints`, webhook cases | `f1-plan-and-billing` |

## 8. Coverage thresholds (what is measured and gated)

| Layer | Template today | Proposed | Gate |
|---|---|---|---|
| Backend global (line+branch, pytest-cov) | reported, no gate | **75%** | `--cov-fail-under=75` in `pytest.ini` from It1 |
| Backend engine modules (analysis/matching/comparison) **and `invalidation_service`** | — | **95%** | new `scripts/ci/coverage-module-gate.py` reading the coverage JSON per module |
| Jest global | 50/50/50/50 | progressive **50 → 55 (It3) → 60 (It6)** | `coverageThreshold.global` |
| Jest `lib/stores/**` · `lib/pdf/**` + `lib/compare/**` | — | 75% · **90%** | per-path keys in `coverageThreshold` |
| E2E flow coverage | 34 demo flows | **20 Versiona flows `covered`** | existing `flow-coverage-reporter` + PR review |

Execution constraints (template rules kept): never run the full suite blindly — target files;
max ~20 tests per batch locally; E2E max 2 files per invocation; backend always under the
venv.

## 9. Open questions (DECISIÓN PENDIENTE)

| ID | Question | Recommendation |
|---|---|---|
| DP-19 | E2E in CI: GitHub Actions native services + host processes (as today) vs full docker-compose job. | **Native services** (keeps pip/npm caches, ~1 min faster startup); compose stays the dev/staging runtime + optional nightly compose-smoke job (see `07`). |
| DP-20 | Jest threshold jump. | Progressive (50→55→60); jumping straight to 60 would block It1 on template-inherited code. |
