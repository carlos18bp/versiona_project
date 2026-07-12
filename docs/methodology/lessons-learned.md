---
trigger: manual
description: Project intelligence and lessons learned. Reference for project-specific patterns, preferences, and key insights discovered during development.
---

# Lessons Learned — Versiona

This file captures important patterns, preferences, and project intelligence that help work
more effectively with this codebase. Updated as new insights are discovered. The canonical
copy of the architecture/style lessons lives in `CLAUDE.md` (project-specific section);
this file records the *discovered-the-hard-way* items.

---

## 1. Iteration 0 findings (2026-07-12)

### pgvector 0.6 (Ubuntu 24.04 apt) is NOT a trusted extension
- `CREATE EXTENSION vector` fails for non-superusers, so pytest-created test databases
  cannot run the core migration as the app user.
- Fix on this VPS: extensions pre-created in `template1` (every new DB inherits them);
  the vendor-safe migration stays for CI, where the service-container user is superuser.

### Celery replaces Huey with less surface than planned
- Static `settings.CELERY_BEAT_SCHEDULE` + Redis result backend cover everything the
  template's Huey setup did — the django-celery-beat/results apps were skipped on purpose
  (fewer Django 6 compatibility risks). Huey's `task.call_local()` in tests becomes a plain
  function call.

### Deterministic PDFs need two switches
- reportlab: `canvas.Canvas(..., invariant=1)` fixes dates/producer.
- PyMuPDF: `doc.save(..., no_new_id=True)` — without it every save mints a random /ID and
  byte-reproducibility breaks (caught by double-run sha256 comparison).

### The template's CLAUDE.md described a different project
- Its "content app / EmailTemplateRegistry / MySQL 8" section did not match the actual code
  (`base_feature_app`, plain f-string emails). Trust exploration over inherited docs; the
  identity section is now Versiona's real state.

### git mv + Edit tool interplay
- After `git mv`, files must be re-read at the new path before editing; global seds run
  after a read also invalidate it. Sequence renames → seds → reads → edits to avoid churn.

## 2. Product guardrails (never relearn these)

- D5 conservative bias (I7): no code path may preserve a seal without exact normalized
  body-hash equality. False-invalidate is acceptable; false-preserve never (S4).
- Versions/seals are append-only (I2–I4); "delete" features (C4/B4) are V2 and still never
  touch sealed history.
- The `testdata/` truth table is a contract: engine/E2E assertions must match it exactly,
  and any change to it requires regenerating fixtures via the script in the same PR.
