# 01 — Inventario de estado real

> Misión: auditoría de completitud + cierre de brechas. Este documento levanta el estado REAL
> del sistema (no el planeado). Se re-levanta al cierre de cada iteración con los comandos de
> §7.

**Iteración**: It0 (bootstrap) · **Commit**: `527d61c` · **Fecha**: 2026-07-12 ·
**Suites**: pytest 123/123 · jest 114/114 (17 suites) · playwright 13/13 ·
**Cobertura**: backend 83.3% combinada (sin gate) · jest 61.05% líneas / 89.49% ramas

## 1. Rutas frontend

| Ruta | Pantalla | Guard/acceso | Estado | Flujos | Fuente |
|---|---|---|---|---|---|
| `/` | Landing Versiona | público | **Implementada** | H1 (entrada A1) | `frontend/app/page.tsx` |
| `/sign-in` | Login (email/Google/captcha) | guest (proxy redirige si hay sesión) | **Implementada** | U1–U3 | `app/sign-in/page.tsx` |
| `/sign-up` | Registro | guest | **Implementada** | U4 (A1 parcial: NO crea org ni proyecto ejemplo) | `app/sign-up/page.tsx` |
| `/forgot-password` | Recuperación 2 pasos | guest | **Implementada** | U6 | `app/forgot-password/page.tsx` |
| `/admin-login` | Handoff impersonación Django admin | público (consume tokens por query) | **Implementada** | U7 | `app/admin-login/page.tsx` |
| `/dashboard` | Panel | `proxy.ts` + `useRequireAuth` | **Placeholder** ("tu tablero llega con It1") | — | `app/dashboard/page.tsx` |
| `/manual` | Ayuda interactiva (es/en) | auth (contenido) | **Implementada** | H2 | `app/manual/page.tsx` |
| Todas las demás rutas del producto (onboarding, projects, documents, compare, inbox, org, settings, trash, audit) | — | — | **No existen** | A1–F3 | — |

Notas: `proxy.ts` aún protege el prefijo `/backoffice` (ruta eliminada en It0 — residuo
cosmético). No hay `middleware.ts` (Next 16 usa `proxy.ts`).

## 2. Endpoints backend

Prefijo `/api/`. Permiso = clase DRF efectiva hoy (no hay roles de proyecto aún).

### 2.1 Auth (app `accounts`) — existentes

| Método | Ruta | Permiso | Flujo | Prueba integración |
|---|---|---|---|---|
| POST | `sign_up/` | AllowAny (+captcha) | U4/A1-parcial | `accounts/tests/views/test_auth_endpoints.py` |
| POST | `sign_in/` | AllowAny (+captcha) | U1/U2 | ídem |
| POST | `google_login/` | AllowAny | U3 | ídem |
| POST | `send_passcode/` · `verify_passcode_and_reset_password/` | AllowAny | U6 | ídem |
| POST | `update_password/` | IsAuthenticated | U6 | ídem |
| GET | `validate_token/` | IsAuthenticated | U5 | `test_jwt_endpoints.py` |
| POST | `token/` · `token/refresh/` | AllowAny (simplejwt) | U5 | ídem |
| GET | `google-captcha/site-key/` · POST `google-captcha/verify/` | AllowAny | U1 | `test_captcha_views.py` |

### 2.2 Plataforma (app `core` + proyecto) — existentes

| Método | Ruta | Permiso | Flujo | Prueba |
|---|---|---|---|---|
| GET | `health/` | AllowAny | — | (smoke webServer) |
| GET | `staging-banner/` | AllowAny | — | `core/tests/views/test_staging_banner.py` |
| — | `/admin/` (site custom `myadmin`) | staff | — | `accounts/tests/utils/test_admin.py` |

### 2.3 Dominio Versiona — **NO EXISTE NINGUNO**

Cero endpoints de orgs, projects, documents/versions/upload, sections, comparisons,
review-requests, seals/seal_plan, observations, checks, jobs, notifications, billing,
reports/certificates, trash, audit. Diseño completo en `docs/plan/03` §3 + deltas del kit.

## 3. Modelos por app

| App | Modelos migrados | Estado | Invariantes I1–I15 con prueba |
|---|---|---|---|
| `accounts` | User (email login; `role` legacy customer/admin — **NO es el modelo de roles org/proyecto del plan**), PasswordCode | Migrado (0001) | — (invariantes de dominio aún sin modelos) |
| `core` | StagingPhaseBanner (+mixins abstractos TimestampedModel/PublicIdModel-UUIDv7) | Migrado (0001 extensiones vector/pg_trgm + 0002) | — |
| `orgs, projects, documents, reviews, observations, checks, comparisons, engine, notifications, billing, audit` | **ninguno** (apps esqueleto) | Vacías | I1–I15: **0/15 implementadas** |

## 4. Tareas Celery

Broker/results Redis; colas declaradas `default, engine_light, engine_heavy`; eager fuera de
producción (`CELERY_TASK_ALWAYS_EAGER=1` en dev/tests).

| Tarea | Cola | Disparador | Estado | Prueba |
|---|---|---|---|---|
| `scheduled_backup` | default | beat dom 03:00 | Migrada de Huey, operativa | `accounts/tests/commands/test_tasks.py` |
| `silk_garbage_collection` | default | beat diario 04:00 | Operativa | ídem |
| `weekly_slow_queries_report` | default | beat lun 08:00 | Operativa | ídem |
| `silk_reports_cleanup` | default | beat mensual día 1 | Operativa | ídem |
| Pipeline del motor (analysis/comparison/seal_review/reanchor/check_run/thumbnail/purge_trashed) | engine_* / default | — | **No existe** | — |

## 5. Eventos de notificación

| Evento | Canal | Estado |
|---|---|---|
| Reset de contraseña (código 6 dígitos) | email transaccional (f-string + `send_mail`, vía mailpit en dev) | **Implementado** (fuera del futuro sistema de prefs: siempre se envía) |
| Catálogo del producto (`review.requested`, `observation.created/replied`, `seal.placed/invalidated/preserved-OFF`, `version.uploaded/approved`) + centro in-app + `NotificationPreference` + `EmailTemplateRegistry` | — | **No existe** |

## 6. Pruebas por nivel

| Nivel | Ubicación | Nº tests | Verdes | Rojas | Cobertura | Gate vigente |
|---|---|---|---|---|---|---|
| Unit+integración backend | `backend/{accounts,core}/tests` (views 41 · utils 48 · commands 14 · models+serializers+core 20) | **123** | 123 | 0 | **83.3%** combinada (stmts+branch) | **sin `--cov-fail-under`** |
| Unit frontend (Jest+RTL) | `frontend/**/__tests__` (17 suites) | **114** | 114 | 0 | líneas **61.05%** · ramas 89.49% · funciones 73.86% | global 50/50/50/50 |
| E2E (Playwright) | `e2e/public/smoke.spec.ts` (1) + `e2e/auth/auth.spec.ts` (12) | **13** | 13 | 0 | flow-coverage: 6 covered / 20 missing (26 flujos v2.0.0) | reporter informativo |
| Ausentes | Ningún test de dominio Versiona (invariantes, motor, permisos por rol de proyecto, mailpit, storageState, prueba maestra) | — | — | — | — | — |

Deudas de arnés conocidas (detalle en `02-brechas.md` §3): sin worker Celery en
`playwright.config.ts`, sin globalSetup/storageState, sin helper mailpit, marker pytest
`escenario` sin registrar, `tsc --noEmit` roto por `lib/services/__tests__/http.test.ts`
(herencia del template), 29 errores ESLint heredados.

## 7. Método de levantamiento (comandos read-only, reproducibles por iteración)

```bash
# Rutas frontend
find frontend/app -name page.tsx | sort ; grep -n "PROTECTED" frontend/proxy.ts
# Endpoints
grep -rn "path(" backend/{accounts,core}/urls* backend/versiona_project/urls.py
# Modelos migrados
backend/venv/bin/python backend/manage.py showmigrations | grep -v "(no migrations)"
# Tareas Celery y beat
grep -n "@shared_task" backend/versiona_project/tasks.py ; grep -n "CELERY_BEAT" backend/versiona_project/settings.py
# Suites y cobertura
backend/venv/bin/python -m pytest backend/accounts backend/core -q          # 123 passed · TOTAL combinado
cd frontend && npx jest --coverage --silent --coverageReporters=json-summary # coverage-summary.json
cd frontend && npx playwright test --list                                    # 13 tests
```
