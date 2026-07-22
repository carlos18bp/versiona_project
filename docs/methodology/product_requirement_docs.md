# Product Requirement Document — Versiona

> Memory Bank core file. The authoritative, detailed PRD is the planning suite:
> `docs/plan/00-vision.md` (objective, glossary, success criteria) and
> `docs/plan/01-alcance-mvp.md` (the 16 MVP flows with acceptance criteria). This file is the
> quick-recall summary.

## Why this project exists

Versiona is "the Git of documents": a SaaS bringing the Git/GitHub workflow to the world that
works in PDF. It kills two pains: (1) re-reading whole documents on every review round
because nobody knows what changed, and (2) `final_v3_AHORA_SI.pdf` — filenames as version
control, with no answer to "which approvals still stand after this change?".

## Core requirements

- Immutable, linear **versions** per document (no branches in v1).
- Automatic **comparison** between any two versions, classified per stable **section**.
- **Anchored observations** with states that survive across versions.
- **Seals**: Ed25519-signed approvals bound to exact version + covered sections.
- **D5 — selective invalidation (crown jewel)**: a new version invalidates only the seals
  whose sections changed, preserves the rest WITH a validity record, and notifies only the
  affected reviewers. Conservative bias: never preserve without exact hash equality (I7).
- Deterministic **checks** with evidence (traffic light per version).
- Organizations, per-project roles (owner/admin/editor/reviewer/viewer), free plan limits +
  Wompi self-service upgrade (DP-01 resolved).

## Scope

- **MVP** = 16 flows: A1, A2, B1, B2, B3, C1, C2, C3, D1, D2, D3, D4, D5, E1, E3, F1
  (full public launch cut — DP-14 resolved). Engine MVP: native-text PDF + OCR for scans.
- **Go-public layer (It9, 2026-07-22)** — freemium à la iLovePDF: 14-day Pro trial
  auto-started on signup (no card; console override always wins), public landing +
  `/precios` (COP catalog, no online checkout yet — upgrade by contact), and the
  anonymous acquisition hook `/comparar` (two PDFs, no account, ephemeral files,
  scanned PDFs answered with an OCR upsell). 36 registered user flows total.
- **Not in v1**: branches, external legal e-signature, drawings/CAD, document editing,
  interpretive AI, public API/SSO, deleting history (see `docs/plan/00` §4).

## Success criteria (S1–S6, `docs/plan/00` §2)

Activation < 5 min to first real comparison · re-reading hours saved · projects with ≥3
versions · **zero false-preserves in D5** · comparison < 60 s p95 · zero notifications to
unaffected reviewers.
