# 04 — Matriz de trazabilidad escenario → pruebas

> Se crea como esqueleto en Fase 2 y se rellena AL CIERRE DE CADA iteración: la iteración que
> implementa un flujo agrega TODAS las filas de sus escenarios (de `03-mapa-flujos.md`) con sus
> celdas de prueba. Gate de cierre de misión: 0 escenarios sin fila, 0 filas sin prueba
> (salvo `n/a` justificado), 0 pruebas huérfanas (sin escenario).

**Iteración**: It0 · **Commit**: `527d61c` · **Fecha**: 2026-07-12 ·
**Escenarios totales (03)**: 258 · **Con fila aquí**: 11 (anexos U/H) · **VERDES**: 9 ·
**Pendientes por iteración**: 247

## 1. Reglas de cumplimiento

- **BLOQUEANTE ⇒ celda E2E obligatoria** (spec dedicado; M1 no sustituye).
- **ENRIQUECE/COSMÉTICA ⇒ mínimo** unit (BE o FE según capa) **+ integración**.
- **Clase P ⇒ integración parametrizada** (`pytest.param(id='<flujo>-p0X-<rol>')` con los 7
  actores); a E2E solo el ocultamiento UI representativo de la pantalla.
- Celdas: `archivo::test` · `n/a (razón)` · `—` (pendiente, válido solo si la iteración
  destino aún no llegó).
- Portadores del id: pytest `@pytest.mark.escenario("D5-F01")` (marker registrado en It1,
  H05) · RTL `it('[C1-L01] ...')` · Playwright título `'D5-F01 — ...'` + tag
  `@scenario:d5-f01`.
- Extracción mecánica: `grep -rn 'escenario("' backend/*/tests` ·
  `grep -rnE '\[[A-Z0-9]+-[FAEPLCX][0-9]{2}\]' frontend` · `grep -rn '@scenario:' frontend/e2e`.

## 2. Matriz por módulo

### Anexo U/H (heredados — únicos con cobertura hoy)

| Escenario | Sev | Unit BE | Unit FE | Integración | E2E | Estado |
|---|---|---|---|---|---|---|
| U1 sign-in form | BLOQ | — | `app/sign-in/__tests__/page.test.tsx` | `test_auth_endpoints.py::sign_in` | `auth.spec.ts` (form+redirect) | VERDE |
| U2 login inválido | BLOQ | — | ídem | `test_auth_endpoints.py::invalid` | `auth.spec.ts` | VERDE |
| U3 Google login | ENR | `test_auth_endpoints.py::google` | `authStore.test.ts` | ídem | n/a (OAuth externo; aceptado 03 §8) | VERDE |
| U4 sign-up form | BLOQ | `test_auth_endpoints.py::sign_up` | `app/sign-up/__tests__` | ídem | `auth.spec.ts` | VERDE |
| U5 sesión/refresh | BLOQ | `test_jwt_endpoints.py` | `lib/services/__tests__/http.test.ts` | ídem | (implícito en U8) | VERDE |
| U6 recuperación | BLOQ | `test_auth_endpoints.py::passcode` | `app/forgot-password/__tests__` | ídem | `auth.spec.ts` (forms) | VERDE |
| U7 admin handoff | ENR | `test_admin.py::login_as` | `app/admin-login/__tests__` | — | — | PENDIENTE (It1) |
| U8 sign-in sesión real | BLOQ | — | — | — | — (lo cierra H02) | PENDIENTE (It1) |
| U9 sign-out | ENR | — | `layout.test.tsx` (botón) | — | — | PENDIENTE (It1) |
| H1 landing | BLOQ | — | `app/__tests__/home.test.tsx` | — | `smoke.spec.ts` | VERDE |
| H2 ayuda /manual | COSM | — | — | — | — | PENDIENTE (It8) |

### Módulo A (38 escenarios) — filas se agregan en It6
`A1-*` (11) · `A2-*` (15) · `A3-*` (12). Estado: PENDIENTE (It6).

### Módulo B (42) — It1 (B1, B2 mínimo) · It5 (B2 completo, B3) · It6 (B4)
`B1-*` (8) · `B2-*` (11) · `B3-*` (11) · `B4-*` (12). Estado: PENDIENTE.

### Módulo C (45) — It1 (+C1-A02/D5-A03 OCR en It5)
`C1-*` (14) · `C2-*` (11) · `C3-*` (10) · `C4-*` (10). Estado: PENDIENTE (It1).

### Módulo D (58) — It3 (D4, D5) · It4 (D1, D2, D3)
`D1-*` (10) · `D2-*` (8) · `D3-*` (12) · `D4-*` (13) · `D5-*` (15). Estado: PENDIENTE.

### Módulo E (37) — It2 (E1) · It5 (E3) · It7 (E2, E4)
`E1-*` (10) · `E2-*` (8) · `E3-*` (10) · `E4-*` (9). Estado: PENDIENTE.

### Módulo F (26) — It7
`F1-*` (10) · `F2-*` (7) · `F3-*` (9). Estado: PENDIENTE (It7).

### M1 (máster) — It8
`M1-F01` (viaje de 16 pasos, 03 §7): E2E `e2e/master/master-journey.spec.ts`. Estado:
PENDIENTE (It8). Gate: verde 2 corridas consecutivas.

## 3. Cumplimiento de reglas (se recalcula por iteración)

| Regla | Valor actual | Gate al cierre |
|---|---|---|
| Escenarios BLOQUEANTES con E2E | 6/6 de los implementados (U/H) | 100% de los BLOQUEANTES |
| Escenarios sin prueba alguna | 247 (iteraciones no llegadas) | 0 |
| Pruebas huérfanas (sin escenario) | 0 conocidas (suites It0 mapean a U/H) | 0 |
| `test.skip` en el árbol | 0 | 0 (prohibido) |

## 4. Gates de cobertura vigentes vs objetivo

| Gate | Hoy | It1–It2 | It3–It4 | It5+ | Cierre |
|---|---|---|---|---|---|
| pytest `--cov-fail-under` | sin gate (83.3% medido) | 75 | 78 | **80** | 80 |
| Motor (`engine`, matching, comparison) + `invalidation_service` | — | 95 (It2) | 95 | 95 | 95 |
| Jest global | 50 (61.05% medido) | 50 | 55 | 55→60 | 60 |
| Jest rutas clave (`components/{review,compare,versions,onboarding}/**`) | — | — | 60 | 70 | **80** |
| Jest `lib/stores/**` · `lib/pdf/**`+`lib/compare/**` | — | 75 · 90 | 75 · 90 | 75 · 90 | 75 · 90 |
| Flow-coverage (reporter) | 6 covered / 20 missing | +flujos de la It | ídem | ídem | **0 missing / 0 partial** |

## 5. Método de extracción

Greps de §1 al cierre de cada iteración; los números de esta cabecera y de §3 se actualizan en
el mismo commit que cierra la iteración. (Candidato futuro: `scripts/audit/trace-matrix.py`.)
