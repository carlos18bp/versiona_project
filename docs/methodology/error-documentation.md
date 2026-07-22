---
trigger: manual
description: Error documentation and known issues tracking. Reference when debugging, fixing bugs, or encountering recurring issues.
---

# Error Documentation — Versiona

This file tracks known errors, their context, and resolutions. When a reusable fix or correction is found during development, document it here to avoid repeating the same mistake.

---

## Format

```
### [ERROR-NNN] Short description
- **Date**: YYYY-MM-DD
- **Context**: Where/when this error occurs
- **Root Cause**: Why it happens
- **Resolution**: How to fix it
- **Files Affected**: List of files
```

---

## Known Issues

### [ERROR-005] UploadThrottle is inert (open, by design until redesigned)
- **Date**: 2026-07-22
- **Context**: `documents/views.py` upload endpoints appear rate-limited (20/hour) but are not.
- **Root Cause**: `ScopedRateThrottle` reads `view.throttle_scope`, which `@api_view` FBVs never set — `allow_request` returns True silently.
- **Resolution**: pending a deliberate design: switching to a `SimpleRateThrottle` subclass would immediately rate-limit the CI E2E suite (same IP, many uploads). Needs a higher rate + cache strategy first. Public endpoints already use the correct subclasses.
- **Files Affected**: `backend/documents/views.py:24`

---

## Resolved Issues

### [ERROR-001] Bare colon in a workflow step name killed the whole CI file
- **Date**: 2026-07-22
- **Context**: Push after adding the OCR apt step — GitHub reported "This run likely failed because of a workflow file issue"; zero jobs started.
- **Root Cause**: `name: Install OCR system deps (ocrmypdf: tesseract...)` — the unquoted `:` inside the step name is a YAML mapping separator.
- **Resolution**: reworded the name without a colon; validate locally with `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` before pushing workflow edits.
- **Files Affected**: `.github/workflows/ci.yml`

### [ERROR-002] Backend OCR suites red only in CI (ocrmypdf subprocess error)
- **Date**: 2026-07-22
- **Context**: 3 scanned-PDF tests (engine pipeline ×2, reviews hardening ×1) failed in CI, passed on the VPS.
- **Root Cause**: runners lacked the system binaries ocrmypdf shells out to (`tesseract`, `tesseract-spa` data, `ghostscript`); the VPS has them installed.
- **Resolution**: apt step in the backend-tests job only (E2E uses text-native fixtures and never triggers OCR). unpaper/pngquant/qpdf NOT needed for `optimize=0` + bundled libqpdf.
- **Files Affected**: `.github/workflows/ci.yml`, `backend/engine/services/ocr.py`

### [ERROR-003] Four E2E email flows died in CI on ECONNREFUSED :8025
- **Date**: 2026-07-22
- **Context**: a2-invite-team, d1-request-review, d5-selective-invalidation and the master journey — 100% failing in CI, green locally.
- **Root Cause**: no mailpit service container and no `DJANGO_EMAIL_*` env in the e2e job → Django fell back to console email and `e2e/helpers/mailpit.ts` fetches crashed.
- **Resolution**: `axllent/mailpit` service (ports 1025/8025, `/livez` healthcheck) + SMTP env block in the frontend-e2e-tests job.
- **Files Affected**: `.github/workflows/ci.yml`, `frontend/e2e/helpers/mailpit.ts`

### [ERROR-004] Quality gate reported ~26 phantom errors (parser bugs, not test bugs)
- **Date**: 2026-07-22
- **Context**: test-quality-gate red with "empty body"/"unnamed test"/duplicate-title errors across ~20 spec files.
- **Root Cause**: the jest AST parser classified `test.use/slow/setTimeout` as test declarations and rendered template-literal titles as empty; the backend analyzer didn't count `pytest.raises` as an assertion.
- **Resolution**: fixed the analyzers (NON_TEST_MEMBERS set; quasi-join titles with a `${…}` placeholder; `"raises"` in ASSERTION_PATTERNS). Audit the gate before mutating tests when it disagrees with reality.
- **Files Affected**: `frontend/scripts/ast-parser.cjs`, `scripts/quality/backend_analyzer.py`

### [ERROR-006] b3 spec raced the checklist render (deterministic CI failure)
- **Date**: 2026-07-22
- **Context**: `b3-e3-governance.spec.ts` failed 1/2 in CI (fresh seed), passed locally (persistent DB carried old checks).
- **Root Cause**: `count() - 1` read immediately after clicking `add-check` — React hadn't committed the new row, so index resolved to -1.
- **Resolution**: capture `initialCount` before the click, then `await expect(rows).toHaveCount(initialCount + 1)` and use `initialCount` as the index.
- **Files Affected**: `frontend/e2e/app/projects/b3-e3-governance.spec.ts`
