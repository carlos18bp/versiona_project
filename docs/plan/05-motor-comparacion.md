# 05 — Analysis & Comparison Engine

> The engine pipeline (ingest → scenario detection → extraction → sectioning → comparison →
> the section/check/reviewer matrix that feeds **D5**), the precise definition and persistence
> of a "section" (what selective invalidation stands on), the full D5 algorithm, and the job
> contracts consumed through Celery queues. MVP scope: **native-text PDF (PyMuPDF) + OCR for
> scans**; every other scenario is listed as a future extension, not planned in detail.

## 1. Base reused

The template contributes the queue *infrastructure conventions* (Redis broker, periodic-task
patterns — migrated Huey→Celery per the fixed mission decision) and nothing engine-specific:
the pipeline, matching and D5 below are new. The `engine` Django app owns `EngineJob` and the
Celery tasks (`03-backend.md` §2) and imports nothing from `reviews`/`billing`, so it can be
extracted into a separate deployable ("engine as a service") without touching domain code.

## 2. Pipeline overview

```mermaid
flowchart LR
    U[Upload complete C1/C2] --> A[AnalysisJob]
    A --> A1[Scenario detection: native / scanned / mixed]
    A1 --> A2[Extraction: PyMuPDF text+layout, OCR w/ confidence]
    A2 --> A3[Sectioning: heading heuristics]
    A3 --> A4[Identity matching vs existing Sections]
    A4 --> A5[Persist SectionVersions + tsvector index B2]
    A5 --> A6[CheckRun E3, pinned config]
    A6 --> A7[Re-anchor open observations D3]
    A7 --> C[ComparisonJob auto vs previous ready version]
    C --> M[Section/check/reviewer matrix]
    M --> D[SealReviewJob D5]
    D --> N[Selective notifications]
```

The whole chain is serialized **per document** (Redis lock by `document_id`) — see edge case
F4.

## 3. What is a "section" (MVP definition — D5 depends on this)

A **section** is a block headed by a heading detected over the PyMuPDF layout, by priority:

1. **Explicit numbering**: `^\d+(\.\d+)*[.)]?\s` and keyword patterns
   (`Capítulo|Sección|Anexo|Artículo|Cláusula` + number).
2. **Typography**: font size ≥ the document's 85th percentile, or bold + short line
   (< 80 chars) + vertical gap.
3. **Embedded outline/TOC** of the PDF when present (highest-confidence signal).

Hierarchy capped at 2 levels (deeper levels fold into level 2). Content before the first
heading is an implicit `__preamble__` section.

**Fallback when no headings are detectable** (< 2 headings in > 3 pages): one section per page
(`stable_key` page-based, fragile identity) + an explicit **degraded-mode banner** + D5 forced
to coordinator mode (§6e). Rejecting the document would break A1/C1 with real-world ugly PDFs
(DP-09).

**Persisted per section × version** (`SectionVersion`, `02` §3.3):

- Normalized text: NFC, collapsed whitespace, de-hyphenated line breaks, repeated
  headers/footers and page numbers stripped.
- `body_hash` and `heading_hash` computed **over the normalized text** — the equality I7
  demands is thus immune to re-rendering/re-compression of the PDF.
- Page range, per-block **bboxes normalized 0–1 top-left** `{page, x0, y0, x1, y1}` (anchors
  for D3, highlights for E1), order index, level, per-section `ocr_confidence` (min of its
  blocks), char count.
- The full raw artifact (`sections.json`: words + positions) goes to S3 for fine word-diffs
  without bloating PostgreSQL.

## 4. Section identity & matching (runs inside ComparisonJob)

Identity lives in the `Section` row (stable across versions); matching decides which
`SectionVersion` of the new upload belongs to which `Section`:

```
for each extracted section sv_to of to_version:
  1. stable_key match: a Section of this document has the same stable_key
     (identical normalized heading)                       → SAME identity
  2. exact-content match: sv_to.body_hash equals the body_hash of an unmatched
     from_version section → SAME identity, relation=renamed
     (re-assign the SAME Section row; update title_current; lineage `renamed`)
  3. similarity candidates (trigram/token-set over heading + shingles over body):
       score ≥ 0.85 with a single unambiguous candidate    → SAME identity (modified)
       0.55 ≤ score < 0.85, or ≥2 candidates within Δ<0.1,
       or 1→N / N→1 containment (split/merge)              → AMBIGUOUS: create a NEW Section
                                                             + lineage split_from/merged_into/
                                                             removed+added; NEVER inherit identity
       score < 0.55                                        → ADDED (new Section)
from_version sections left unmatched                       → REMOVED (retired_in_version=to)
```

Reordering is irrelevant (identity ≠ position). The conservative bias lives in step 3:
**ambiguity breaks identity**, so seals over those sections fall by "removed" (I7). Every
decision is recorded as append-only `SectionLineage` (probative evidence).

**Per-section classification** (for sections whose identity survived):
`UNCHANGED` (equal body_hash AND heading equivalent after case/space normalization) ·
`RENAMED_ONLY` (equal body, different heading) · `MODIFIED` (different body) · `ADDED` ·
`REMOVED`.

## 5. Comparison output (E1, C2, D2)

`ComparisonJob(from, to)` produces (cached by unique pair — I15):

- `SectionDiff` rows per section (change_type, similarity, diff artifact key).
- Word-level diff artifacts per changed section in S3 (consumed by the star screen's
  side-by-side highlights and by D5 evidence).
- `summary` JSONB: counts per change type + affected seals + check delta — the exact payload
  behind `PostUploadSummary` (C2) and the `ChangeSummary` view (E1).

## 6. The D5 algorithm — selective seal invalidation (full specification)

**(a) Inputs**: `to_version` (just analyzed, `ready`, number N); `from_version` = latest
version with `analysis_status=ready` and number < N (normally N−1; edge F5);
`Comparison(from, to)` completed; `S` = seals valid at `from_version` per I11;
`config = to_version.config_version` (d5_mode, coordinators — pinned, I8).

**(b) Matching** — §4 above (produces the classification + lineage).

**(c) Section/check/reviewer matrix** — the crossing that makes D5 selective: for every seal,
its covered sections' classification; for every changed section, its owner(s) and check
results. This matrix is also what the coordinator screen renders.

**(d) Decision matrix per seal** (for each seal s ∈ S, at `to_version`):

| State of s's covered sections | `d5_mode=auto` | `d5_mode=coordinator` | Record content |
|---|---|---|---|
| All UNCHANGED | `preserved` | `preserved` (automatic, no queue) | Validity record: `{verified: [{stable_key, hash_from, hash_to}], method: "body_hash_equal", comparison_id, checked_at}` |
| Some RENAMED_ONLY (rest unchanged) | `invalidated` (reason `renamed_section`) | `pending_confirmation` (proposed=`preserved`, labeled "only the title changed") | Evidence: heading before/after + equal body hashes |
| Some MODIFIED or REMOVED | `invalidated` | `pending_confirmation` (proposed=`invalidated`; confirming invalidation is one click; overriding to preserved requires viewing the evidence and is audited) | Evidence: `{changed: [{stable_key, change_type, similarity, diff_artifact_key}]}` |
| Ambiguous matching touched the scope | `invalidated` (reason `ambiguous_match`) | `pending_confirmation` (proposed=`invalidated`) | Evidence: candidates + scores |
| `covers_all` and ANY change (incl. ADDED) | `invalidated` (reason `document_changed`) | `pending_confirmation` | A whole-document seal covers the whole: a new section alters the whole |
| `covers_all` and ZERO diffs (e.g. re-compressed PDF, same text) | `preserved` | `preserved` | Record: all hashes equal |

The default branch is **invalidate** — no code path reaches `preserved` without hash equality
(I7; property-tested).

**(e) Auto vs coordinator**: `auto` ⇒ records are final immediately and approval recomputes at
once. `coordinator` ⇒ records are `pending_confirmation` with a proposed decision; the version
enters "invalidation plan pending" (blocks approval and new seals; observing and comparing stay
allowed); the coordinator confirms/adjusts row by row or "apply all proposed"; every decision
records `decided_by` + AuditEvent. **Both modes produce identical validity records — only who
decides the gray zone changes.** Safety override: if `to_version.ocr_confidence < 0.75` or the
per-page fallback is active, coordinator mode is forced regardless of config.

**(f) Selective notification (the promise, S6)**: group final `invalidated` records by
reviewer → ONE notification per affected reviewer (email + inbox) containing: their fallen
seals, the changed sections with links to the exact diffs, and a re-review CTA (creates/updates
a `ReviewAssignment` scoped to only their affected sections). Reviewers whose seals were all
`preserved`: **zero notifications**. The coordinator gets one only in coordinator mode (pending
plan). If no sealed section changed, nobody is notified except the uploader (C2 confirmation).

**(g) Edge cases**:

| # | Case | Rule |
|---|---|---|
| F1 | `covers_all` seal | Matrix rows 5–6: any change invalidates; preserve only with zero diffs. |
| F2 | New section without an owner | Invalidates nothing (it was in no seal's scope). Approval evaluates the PINNED config (I8): if that config does not require it, it does not block; assigning an owner now rules from the next version (documented consequence of B3; "additive hotfix" alternative → DP-10). An E3 check may flag it yellow ("section without an owner"). |
| F3 | Document loses all sections (empty extraction) | Everything REMOVED ⇒ all seals invalidated; red traffic light "structure not recognized"; coordinator mode forced; version stays `ready` but unsealable until human review. |
| F4 | Two versions in quick succession (v(N+1) arrives while vN's plan is pending) | Per-document serialization (Redis lock + per-document queue key). vN's `pending_confirmation` records become `superseded` (append, no notification); for v(N+1)'s D5, seals with an undetermined chain count as NOT valid (conservative, I7); comparison runs against the last confirmed ready version. Notifications deduplicated by (reviewer, seal). |
| F5 | Previous version `failed` | `from_version` = last `ready`; the failed one never participates (it was never sealable, I10). |
| F6 | Identical binary re-uploaded (same sha256) | Rejected at `complete/` before creating a version ("identical to vN"); D5 does not run. |
| F7 | Seal by the author of the new version | No engine-level special rule in MVP (author/reviewer separation is policy: editors cannot seal, `03` §5); recorded in AuditEvent. |

## 7. Job contracts (consumed via Celery queues)

Broker: Redis. Results: `django-celery-results`. Periodic: `django-celery-beat` (inherits the
template's backup/cleanup tasks). Queues: `engine_heavy`, `engine_light`, `default` (domain).
States: `pending → running → done | failed`, mirrored in `DocumentVersion.analysis_status`;
idempotency via unique `EngineJob.idempotency_key` — a `done` job re-enqueued returns its
existing result; upserts are deterministic (I15).

| | **AnalysisJob** | **ComparisonJob** | **SealReviewJob (D5)** |
|---|---|---|---|
| Trigger | C1/C2: version created (upload completed) | Auto when analysis of vN finishes (vs previous ready), or E1 manual (any pair) | Auto when the auto-comparison of (last ready, vN) finishes |
| Input payload | `{job:"analysis", version_id, document_id, file_key, sha256, config_version_id, locale:"es"}` | `{job:"comparison", document_id, from_version_id, to_version_id, trigger:"auto\|manual"}` | `{job:"seal_review", document_id, to_version_id, from_version_id, comparison_id, d5_mode}` |
| Pipeline | scenario detection → extraction (PyMuPDF; OCR w/ confidence if scanned) → sectioning (§3) → identity matching steps 1–2 (§4) → persist SectionVersions + tsvector → CheckRun (pinned config, E3) → re-anchor open observations (D3) | load both versions' SectionVersions → full matching (§4) → classification → word-level diff per section (S3 artifacts) → summary | §6 c–f: matrix, records, notifications, approval recompute |
| Result (JSONB) | `{scenario, ocr_confidence?, page_count, sections:[{stable_key, section_id, heading, level, body_hash, pages:[a,b], order}], checks:{green,yellow,red}, reanchored:n, orphaned:n, duration_ms}` | `{comparison_id, sections:{unchanged:n, modified:[keys], added:[], removed:[], renamed_only:[], ambiguous:[]}, summary_text, duration_ms}` | `{plan:[{seal_id, decision\|proposed, reason_code}], notified_reviewers:[ids], approval:"approved\|blocked\|pending_confirmation"}` |
| Idempotency key | `analysis:v{version_id}` | `comparison:{from_id}:{to_id}` | `d5:v{to_version_id}` |
| Queue / priority | `engine_heavy` (low concurrency, CPU/OCR-bound); a new org's **first version jumps the queue** (A1 < 5 min) | `engine_light`; auto > manual | `default` (domain worker, transactional with the DB) |
| Timeout soft/hard | 10 / 15 min (OCR); native typically < 60 s | 3 / 5 min | 60 / 120 s |
| Retries | 3, exponential backoff 30 s → 5 min; parse errors are permanent (no retry) | 3 | 3 (all-or-nothing transaction) |

**Analysis failure during C2**: the version stays `analysis_status=failed`, visible in the
timeline with a readable cause + retry button (re-enqueues the same key); **valid seals are
untouched** (D5 never ran — they remain valid over the last ready version); the failed version
cannot be sealed or compared (I10); the next version compares against the last ready (F5).

## 8. MVP scope and future extensions

| Scenario | Status | Notes |
|---|---|---|
| Native-text PDF — side-by-side & per-section | **MVP** | PyMuPDF; the perfection target (artifact MVP rule). |
| Scanned PDF — OCR with confidence level | **MVP** | Per-word/section confidence persisted; < 0.75 forces coordinator mode (§6e). Engine per DP-02. |
| NL change summaries (AI) | V2 | Documented only; plugs in after `summary`. |
| Vector plans (geometric stroke comparison) | V2 | Not planned in detail here. |
| Scanned plans (changed-zone maps) | V2 | Idem. |
| CAD files (DXF, layer comparison) | Future | Idem. |
| Plan vision with AI | Future | Idem. |

These extensions slot in as new `source_scenario` values + new pipeline branches; the job
contract and the section/matrix abstractions above are scenario-agnostic on purpose.

## 9. Open questions (DECISIÓN PENDIENTE)

| ID | Question | Recommendation |
|---|---|---|
| DP-02 | OCR engine: Tesseract via `ocrmypdf` · PaddleOCR · cloud (Textract/Document AI). | **ocrmypdf + Tesseract (spa)**: self-hosted (aligns with the future self-hosted plan), no per-page cost, word-level confidence, outputs a text-layer PDF preserving bboxes (D3 anchors). Cloud as a V2 quality upgrade. |
| DP-09 | No detectable headings. | **Section-per-page fallback + degraded banner + D5 forced to coordinator** (rejecting breaks C1/A1 with real documents). |
| DP-10 | Strict non-retroactivity vs additive config hotfix (edge F2). | **Strict in MVP** (F2 consequence documented); additive hotfix as V2 if it hurts in real use. |
| — | OCR-confidence threshold for forcing coordinator mode (proposed 0.75). | Tune with the scanned fixture during It4/It5; keep as env `D5_OCR_CONFIDENCE_MIN`. |
