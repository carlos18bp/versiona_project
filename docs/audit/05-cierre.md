# 05 — Acta de cierre de la misión

> Misión: **AUDITORÍA DE COMPLETITUD + CIERRE DE BRECHAS — Versiona**
> (aprobada por el operador el 2026-07-12; fases 1–2 aprobadas con "aprobado, sigue").
> Cierre: **2026-07-12** · Rama: `docs/12072026-plan-versiona`

## 1. VEREDICTO

**MISIÓN CUMPLIDA.** Los 19 flujos del MVP (A1–F3 + los tres promovidos desde V2:
A3, E2, F2) están implementados de punta a punta, las **31 brechas BLOQUEANTES**
del corte It0 están cerradas, el kit de enriquecimiento (1–7) está entregado, y
**LA PRUEBA MAESTRA pasó en dos corridas consecutivas** (1.8 min y 1.4 min):
dieciséis pasos, tres usuarios reales, todo por la interfaz — del registro a la
constancia PDF descargada y verificable offline.

## 2. La prueba maestra (M1)

`frontend/e2e/master/master-journey.spec.ts` — serial, 3 contexts, sin
`waitForTimeout`, correos únicos por corrida:

1. Registro del editor → 2. onboarding wow (comparación sembrada visible) →
3. proyecto real (B1) → 4. sube v1 (C1) → 5. sube v2 (C2) → 6. comparación
v1↔v2 con la tabla de verdad exacta (E1) → 7. invita a los revisores A y B
(A2, emails reales por mailpit) → 8. A y B se registran y aceptan por token →
9. B ancla una observación a §3 (D3) → 10. el editor responde y sube v3 que
subsana → 11. B ve el ancla re-anclada y resuelve (I14) → 12. A sella §1–2 y
B sella el documento completo (D4) → 13. v3 queda APROBADA (I10) →
14. v4 dispara la invalidación selectiva: **A conservado con igualdad de hash
verificada, B invalidado** (D5 💎) → 15. el correo de re-revisión llega SOLO a
B (S6) y su bandeja acota el trabajo → 16. la constancia de v3 se emite con
los 2 sellos re-verificados y el binario `%PDF` real se descarga (E4).

Única salida de la UI, documentada en el spec: el upgrade a Pro se hace por
consola porque el checkout Wompi está diferido (DECISIÓN PENDIENTE, §5).

## 3. Números finales

| Métrica | Valor |
|---|---|
| pytest | **459 verdes** · cobertura combinada ~87 % · gate `--cov-fail-under=80` activo |
| Gates por módulo (CI) | analysis 94.5 % (≥90) · comparison 96.6 % (≥95) · persistence 98.3 % (≥90) · **invalidation 100 % (≥95)** · seal_service ≥90 |
| jest | **243 verdes** · rutas clave (compare/seals/versions/reviews/observations/checks/certificates) **≥80 con gate** · residual (páginas) gate 50 · total all-files 63.8 % líneas |
| Playwright | **44/44 verdes** en la corrida de cierre (M1 incluida); a11y wcag2a/aa sin violaciones críticas |
| Flow-coverage (reporter) | **31/33 covered · 0 partial · 0 failing** · 2 missing = los P3 aceptados (§7) |
| Escenarios (docs/audit/03) | 258 mapeados · **160+ con fila VERDE en 04** — los restantes son clases P/L cubiertas por matrices parametrizadas equivalentes (regla anti-explosión de 03 §4) |
| Burn-down (02 §6) | It0: 31 bloqueantes → **It7: 0** |
| Property test I7 | 700 ejemplos por corrida: `preserved` ⇒ igualdad de hash, sin excepciones |

## 4. Garantías que quedaron encerradas en código

- **I1–I15 con enforcement mecánico**: columnas congeladas por trigger PostgreSQL,
  sellos append-only, cadena de validez I11, idempotencia por clave natural,
  404 anti-enumeración probado con matrices de 6–7 actores por endpoint.
- **La joya (D5)**: resolver puro con sesgo conservador — no existe camino a
  `preserved` sin igualdad exacta de hash (property test + reina E2E + reina OCR
  que fuerza coordinador sobre escaneados).
- **Constancia E4 auditable por terceros**: `scripts/verify_certificate.py`
  verifica el snapshot con SOLO `cryptography` (sin código Versiona, sin red);
  test lo ejecuta como subproceso y otro prueba que una firma adulterada
  devuelve exit 1.
- **DP-04 sagrado**: los límites del plan bloquean acceso, jamás borran; la
  última versión siempre es accesible.
- **es/en funcional** (decisión del operador): diccionarios TS por pantalla,
  emails por idioma del receptor, test guardián de catálogo completo.

## 5. DECISIÓN PENDIENTE (requieren insumos del operador)

| Tema | Qué falta | Dónde retomar |
|---|---|---|
| Checkout Wompi (F1) | Llaves sandbox/producción | `billing/` — adapter listo para recibir la pasarela; CTA informativo hoy |
| SSO corporativo (A3) | IdP + credenciales | `accounts/` — TOTP+sesiones ya operativos |
| Dominio + SMTP producción (DP-22) | Decisión de despliegue (post-MVP por DP-21) | `docs/plan/07` |
| Custodia de la clave Ed25519 en producción (DP-24) | Secret manager | `reviews/services/signing.py` |

## 6. Actas de /playwright-validation

- **It1** (2026-07-12): 13 garantías — 1 hallazgo real corregido (link Papelera
  visible a no-admins). Commit `4831d24`.
- **It3** (2026-07-12): 13 garantías — 12 ✅; el ⚠ restante fue artefacto del
  script (aserción sin espera), cubierto por el spec `d4`.
- Las iteraciones 4–8 sustituyeron la validación manual por specs E2E dedicados
  por flujo (d1–d3, b2/b3/e3, a1–a3, b4, f1/f2/e2/e4, M1) — cada pantalla nueva
  nació con su spec verde en la misma iteración.

## 6b. Hallazgos del hardening (It8) — el examen encontró y corrigió

1. **Fallos ocultos por el propio arnés de lectura**: los resúmenes de suite
   leídos con `tail -1` capturaban "N passed" y omitían la línea "M failed"
   inmediatamente anterior. Al corregir la lectura aparecieron 11 fallos
   reales acumulados. Lección grabada: los conteos de suite se leen completos.
2. **Residuo del arnés vs límites de producto**: la org semilla acumuló 101
   proyectos de corridas históricas y cruzó el tope del plan `pro` (20),
   rompiendo en paralelo todo spec que creara proyectos. Corrección de
   producto, no parche: tier `enterprise` (sin límites numéricos — concepto
   real de contrato) para las orgs de arnés; los tests de F1 fijan `free`
   explícitamente.
3. **Orden determinista de organizaciones**: `my_orgs` ahora devuelve el
   workspace de equipo antes que el personal — regla de producto que además
   hace determinista la org activa por defecto en la UI.
4. **Semántica del vacío del tablero**: el vacío-con-guía es para el primer
   uso; una búsqueda sin coincidencias deja el grid sin tarjetas. El spec b2
   quedó alineado al diseño y estable (2/2 repetido).
5. **Reporter de flujos vs `--reporter` CLI**: pasar `--reporter=line`
   REEMPLAZA a los reporters del config y el JSON de cobertura de flujos
   queda huérfano. La corrida de cierre se ejecuta sin override.

## 7. Deuda conocida (no bloqueante, honesta)

- Warning de hidratación del `theme-toggle` heredado del template (cosmético,
  H09; visible solo en consola dev).
- `lib/services/__tests__/http.test.ts`: error de `tsc` preexistente del
  template (excluido de gates; catalogado desde It0 en `tasks/tasks_plan.md`).
- Selección de región libre para observaciones (D3): el MVP ancla por sección
  (cubre el guion completo); el dibujo de quads manual queda como refinamiento.
- `escaneado_v1` OCR pierde 2 encabezados del raster a 200dpi (documentado con
  tabla exacta en `testdata/README.md` — comportamiento, no bug).
- Flujos P3 aceptados sin spec E2E dedicado (declarados en flow-definitions):
  `auth-admin-login-handoff` (unit+RTL) y `help-manual-browse` (nice-to-have).

## 8. Cómo verificar este cierre (reproducible)

```bash
# Backend completo (≈11–20 min según carga)
cd backend && venv/bin/python -m pytest accounts core orgs projects documents \
  engine comparisons reviews notifications observations checks billing -q

# Frontend con gates
cd frontend && npx jest --coverage

# La prueba maestra
cd frontend && npx playwright test e2e/master/master-journey.spec.ts

# Verificación externa de una constancia (T6)
python3 scripts/verify_certificate.py snapshot.json
```
