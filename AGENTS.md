<!--
  AGENTS.md template — fleet base (Codex CLI)
  ============================================
  Fuente: workflows/.agents/base/AGENTS.md.tmpl en vps-ops-toolkit
  Sincronizado por: sync-codex-base.sh (Fase 3b) — pendiente
  Convencion: bloques delimitados por markers HTML (igual que CLAUDE.md).
  Per docs Codex CLI: AGENTS.md vive en la raiz del proyecto, los skills en
  .agents/skills/<name>/SKILL.md. .codex/ por-proyecto SOLO lleva config.toml.
-->
<!-- fleet-base:begin v=1 -->
# AGENTS.md — Base Django+React+Next (scaffold) (`base_django_react_next_feature`)

Este archivo es el equivalente Codex de `CLAUDE.md`. Mismo cuerpo de
instrucciones general, distinto frontmatter/estructura. Sincronizado desde
`vps-ops-toolkit/workflows/.agents/base/AGENTS.md.tmpl`.

## Convencion de lenguaje

- Documentacion, comentarios y mensajes de commit en **ingles**.
- Codigo, identificadores y nombres de variable en **ingles**.

## Skills por-proyecto

Los skills Codex de este proyecto viven en `.agents/skills/<name>/SKILL.md`.
**No** en `.codex/skills/` — esa ruta no es valida segun la docs oficial.
Cada skill tiene `SKILL.md` con frontmatter YAML (`name`, `description`) y
opcionalmente `agents/openai.yaml` adyacente con metadata Codex-especifica.

## Configuracion Codex per-proyecto

`.codex/config.toml` define modelo, sandbox y aprobacion para este proyecto.
Sincronizado desde `workflows/.codex/base/config.toml.tmpl`.

## Ecosistemas IA paralelos

Ver `CLAUDE.md` para la convencion completa. Los tres ecosistemas (Claude
Code, Codex, Windsurf) comparten el mismo cuerpo de instrucciones general.

<!-- fleet-base:end -->

<!-- project-specific:begin -->
## Versiona — project specifics

Versiona is "the Git of documents": version control, comparison and seal-based approval for
PDFs. The full identity, conventions and lessons live in `CLAUDE.md` (project-specific
section); the planning suite in `docs/plan/00…09` is the source of truth (flows A1…F1,
invariants I1–I15, roadmap It0–It7 with D5 as the crown jewel).

Key facts:
- Stack: Django 6 + DRF + Celery / Next.js 16 + React 19 / PostgreSQL 16 + pgvector / Redis /
  MinIO / mailpit. Native runtime — no Docker for now (DP-21).
- Backend apps: `core`, `accounts` + skeleton bounded contexts (`docs/plan/03` §2).
- Key commands: `backend/venv/bin/python backend/manage.py <cmd>` ·
  `cd frontend && npm test` · `npx playwright test <spec>` (max 2 files) ·
  `backend/venv/bin/python testdata/generate_pdfs.py` (fixtures — never edit PDFs by hand).

<!-- project-specific:end -->
