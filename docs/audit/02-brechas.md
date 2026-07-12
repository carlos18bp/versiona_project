# 02 — Brechas

> Cruce del inventario (`01-inventario.md`) contra los flujos A1–F3 del artefacto fundacional,
> el alcance resuelto por el operador (2026-07-12: F1 sin Wompi; **A3/E2/F2 se implementan**;
> idioma es/en funcional) y el kit de enriquecimiento de la misión. Los escenarios citados se
> definen en `03-mapa-flujos.md`; la iteración destino sigue el roadmap aprobado (plan de
> misión, It1–It8).

**Iteración**: It0 · **Commit**: `527d61c` · **Fecha**: 2026-07-12

## 1. Definiciones de severidad

- **BLOQUEANTE**: el usuario final no puede completar el flujo (falta vista/endpoint/modelo),
  o se viola un invariante/promesa (I1–I15, S1–S6), o la prueba maestra M1 no puede pasar.
- **ENRIQUECE**: el flujo funcionaría, pero falta una pieza prometida por esta misión
  (estados de pantalla, previews, exports, avisos).
- **COSMÉTICA**: pulido de texto/visual/residuos sin impacto funcional.

## 2. Tabla maestra de brechas por flujo

Estado hoy: **los 19 flujos de producto en alcance carecen de TODO** (vista + endpoint +
modelo + pruebas). Se listan con su descomposición gruesa; el detalle por escenario vive en 03.

| # | Flujo | Qué falta | Tipo | Sev. | Escenarios (03) | It destino | Estado |
|---|---|---|---|---|---|---|---|
| G01 | A1 registro+wow | Org personal al registrarse; wizard onboarding; job proyecto-ejemplo (fixtures v1/v2); métrica <5 min | vista+endpoint+modelo+tarea | BLOQUEANTE | A1-* | It6 | Abierta |
| G02 | A2 invitar equipo | Invitation+memberships org/proyecto; emails con token; aceptar→aterrizar en proyecto; gestión de roles | vista+endpoint+modelo+notif | BLOQUEANTE | A2-* | It6 | Abierta |
| G03 | A3 seguridad de cuenta | 2FA TOTP (enrolar/challenge/códigos de respaldo); sesiones activas + revocación (token_blacklist ya instalado) | vista+endpoint+modelo | BLOQUEANTE | A3-* | It6 | Abierta |
| G04 | B1 crear proyecto | Project+ProjectMembership+ProjectConfigVersion; POST projects; pantalla /projects/new; límite de plan | vista+endpoint+modelo | BLOQUEANTE | B1-* | It1 | **Cerrada It1** |
| G05 | B2 tablero | Falta: filtro por estado y búsqueda por CONTENIDO (FTS) | vista+endpoint | BLOQUEANTE | B2-A01/A03 | It5 | **Parcial: lista+búsqueda por nombre entregadas en It1** |
| G06 | B3 config proyecto | ProjectConfigVersion UI (checklist/dueños/reglas/d5_mode); no-retroactividad I8 | vista+endpoint | BLOQUEANTE | B3-* | It5 | Abierta |
| G07 | B4 archivar/eliminar proyecto | Falta la UI (endpoints, papelera y reglas T4 ya operativos desde It1) | vista | BLOQUEANTE | B4-* | It6 | **Parcial: backend + papelera entregados en It1** |
| G08 | C1 subir primer documento | Document/DocumentVersion/Section/EngineJob; upload_intent+complete (presigned MinIO); AnalysisJob PyMuPDF; semáforo; **preview pre-subida (kit 1)** | vista+endpoint+modelo+tarea | BLOQUEANTE | C1-* | It1 | **Cerrada It1** |
| G09 | C2 nueva versión | Secuencia I1; comparación auto; PostUploadSummary; **edición de mensaje en borrador (kit 2, I2b)** | vista+endpoint+tarea | BLOQUEANTE | C2-* | It1 | **Cerrada It1** |
| G10 | C3 historial | Timeline con autor/fecha/mensaje/**miniaturas (kit 1)**; descarga firmada auditada; salto a comparar | vista+endpoint | BLOQUEANTE | C3-* | It1 | **Cerrada It1** |
| G11 | C4 eliminar versión borrador | Papelera de versión (última+borrador), restore, tombstone I1 | vista+endpoint+modelo | BLOQUEANTE | C4-* | It1 | **Cerrada It1** |
| G12 | D1 solicitar revisión | ReviewRequest/Assignment; selección manual de revisores (DP-A7); bandeja /inbox; notificación | vista+endpoint+modelo+notif | BLOQUEANTE | D1-* | It4 | Abierta |
| G13 | D2 revisar con asistencia | Semáforo+resumen primero; salto a cambios; "ya revisado por ti" | vista+endpoint | BLOQUEANTE | D2-* | It4 | Abierta |
| G14 | D3 observaciones ancladas | Observation+Anchor+Reply; selección de zona (bbox normalizada); re-anclaje entre versiones; estados I14 | vista+endpoint+modelo+tarea | BLOQUEANTE | D3-* | It4 | Abierta |
| G15 | D4 aprobar con sello | Seal+SealSection firmado Ed25519 (I6); congelamiento I5/I10; panel de sellos | vista+endpoint+modelo | BLOQUEANTE | D4-* | It3 | Abierta |
| G16 | D5 invalidación selectiva 💎 | SealValidityRecord+SectionLineage; invalidation_service puro (I7/I11); modos auto/coordinator; notificación selectiva S6 | vista+endpoint+modelo+tarea+notif | BLOQUEANTE | D5-* | It3 | Abierta |
| G17 | E1 comparar versiones ⭐ | Comparison/SectionDiff; matching; CompareView 3 vistas; highlights bbox | vista+endpoint+modelo+tarea | BLOQUEANTE | E1-* | It2 | **Cerrada It2** |
| G18 | E2 comparaciones guardadas | SavedComparison (nombre, autor); lista por proyecto; enlace interno | vista+endpoint+modelo | BLOQUEANTE | E2-* | It7 | Abierta |
| G19 | E3 checks configurables | CheckDefinition/Run/Result con evidencia; **ChecklistTemplate copy-on-apply (kit 2)** | vista+endpoint+modelo+tarea | BLOQUEANTE | E3-* | It5 | Abierta |
| G20 | E4 constancia exportable | Certificate append-only + PDF con firmas re-verificadas; **la prueba maestra M1 la exige** | vista+endpoint+modelo | BLOQUEANTE | E4-* | It7 | Abierta |
| G21 | F1 plan y límites | Plan/Subscription/limits I13; enforcement (proyectos/miembros/historial locked); CTA upgrade informativo (Wompi diferido) | vista+endpoint+modelo | BLOQUEANTE | F1-* | It7 | Abierta |
| G22 | F2 consumo y avisos | Panel de uso vs límites; avisos preventivos al 80% | vista+endpoint | BLOQUEANTE | F2-* | It7 | Abierta |
| G23 | F3 auditoría (base UI) | `/org/audit` filtrable + CSV sobre AuditEvent (el registro server-side nace con cada iteración) | vista+endpoint | BLOQUEANTE | F3-* | It7 | Abierta |
| G24 | Roles de proyecto | `User.role` legacy (customer/admin) ≠ matriz owner/admin/editor/reviewer/viewer; falta OrganizationMembership/ProjectMembership + decoradores `@require_project_role` + 404 anti-enumeración I12 | modelo+permisos | BLOQUEANTE (transversal) | todos los P## | It1 (base) → It6 (gestión UI) | **Cerrada It1** |
| G25 | Kit 4 reportes | Estado de proyecto, actividad por rango, CSV de listas | vista+endpoint | ENRIQUECE | F3/REP-* | It7 | Abierta |
| G26 | Kit 5 notificaciones | Centro in-app + campanita + NotificationPreference + EmailTemplateRegistry bilingüe | vista+endpoint+modelo | BLOQUEANTE (D1/D5 las requieren) | NTF-* | It3–It4 | Abierta |
| G27 | Kit 6 históricos | ActivityFeed por proyecto (AuditEvent whitelisted sin ip) | vista+endpoint | ENRIQUECE | ACT-* | It4 | Abierta |
| G28 | Kit 7 configuraciones | Faltan prefs de notificación (It3-4) y org settings General (It6) | vista+endpoint | BLOQUEANTE | SET-* | It3–It6 | **Parcial: perfil/idioma/zona horaria entregados en It1** |
| G29 | i18n es/en | Faltan: traducción de las páginas auth heredadas y emails por idioma | vista | ENRIQUECE | transversal | cada iteración | **Parcial: diccionarios es/en + preferencia funcional entregados en It1** |
| G30 | OCR escaneados | ocrmypdf+tesseract-spa nativos; confianza por sección; modo degradado + coordinador forzado | tarea+deps sistema | BLOQUEANTE (fixture escaneado con resultados exactos es obligatorio Fase 4) | C1-A02, D5-A03 | It5 | Abierta |

## 3. Brechas del kit/arnés de pruebas

| # | Elemento | Qué escenario/prueba lo exige | Sev. | It | Estado |
|---|---|---|---|---|---|
| H01 | **Worker Celery ausente en `playwright.config.ts`** (webServer solo levanta runserver+next) | Todo E2E con jobs (C1 en adelante, M1) | BLOQUEANTE | It1 | **Cerrada It1** |
| H02 | globalSetup: seed determinista + login API + storageState por rol (`e2e/.auth/*.json`) | Todos los specs autenticados; cierra el gap `auth-sign-in-success` | BLOQUEANTE | It1 | **Cerrada It1** |
| H03 | Helper mailpit (`waitForEmail`, `assertNoEmailFor` positivo-antes-de-negativo) | A2, D1, D3, D5-F01, M1 paso 13/15 | BLOQUEANTE | It1 | **Cerrada It1** |
| H04 | Fixtures `contrato_v3.pdf` y `contrato_v4.pdf` (+tablas de verdad v2→v3 y v3→v4; bytes v1/v2 intactos — DP-A9) | M1 pasos 9 y 13; D3-A04 | BLOQUEANTE | It1 | **Cerrada It1** |
| H05 | Marker pytest `escenario(id)` registrado + convención de ids en los 3 niveles | Trazabilidad 04 mecánica | ENRIQUECE | It1 | **Cerrada It1** |
| H06 | Gates de cobertura escalonados (pytest fail-under 75→78→80; jest rutas clave 60→70→80; motor 95) | Regla "80% backend y componentes clave" | ENRIQUECE | It1→It5 | Abierta |
| H07 | Service `minio` en CI (backend-tests y e2e) | Primeros tests de storage (upload_intent/complete) | BLOQUEANTE | It1 | **Cerrada It1** |
| H08 | `tsc --noEmit` roto (`lib/services/__tests__/http.test.ts`, herencia template) | `next build` de producción | ENRIQUECE | It1 | Abierta |
| H09 | 29 errores ESLint heredados (auth pages any/entities, scripts require, setState-in-effect) | Higiene; no gatea CI | COSMÉTICA | oportunista | Abierta |
| H10 | `proxy.ts` protege `/backoffice` inexistente | Residuo | COSMÉTICA | It1 | **Cerrada It1** |
| H11 | Flujo `master-e2e-journey` + `e4-constancia` + `a3/e2/f2` ausentes en flow-definitions (bump v2.1.0) | M1 y reporter | ENRIQUECE | It1 (registro) | **Cerrada It1** |
| H12 | `e2e/fixtures.ts` referencia usuarios (`test@example.com`) que ningún seed crea | H02 lo resuelve | BLOQUEANTE (parte de H02) | It1 | **Cerrada It1** |

## 4. Flujos fuera de alcance de esta misión

| Flujo/pieza | Exclusión | Verificación |
|---|---|---|
| SSO corporativo (parte de A3) | DECISIÓN PENDIENTE: requiere IdP/credenciales del operador (mismo trato que Wompi) | 03 §A3 escenario A3-X01 |
| Checkout Wompi (parte de F1) | Diferido a misión posterior con llaves sandbox (alcance resuelto #1) | 03 §F1 escenario F1-X01 |
| Planos/CAD/IA interpretativa, API pública, branches | Fuera por artefacto (V2/Futuro) | `docs/plan/00` §4 |

## 5. Brechas transversales de pantalla

El checklist obligatorio (vacío-con-guía / cargando / error+retry / éxito / confirmación 2
pasos / paginación+búsqueda / ocultamiento por rol / deshabilitado por estado de dominio) se
audita ficha por ficha en `03-mapa-flujos.md` §9. Estado inicial: las 7 pantallas existentes
cumplen parcialmente (auth tiene loading/error; landing estática; **ninguna lista con
paginación/búsqueda existe aún**); las ~12 pantallas restantes no existen. El patrón
fundacional (useListController/AsyncBoundary/DataTable/TypeToConfirmDialog/useCan) es brecha
BLOQUEANTE de It1 (todo lo posterior lo consume).

## 6. Burn-down

| Corte | BLOQUEANTES abiertas | ENRIQUECE | COSMÉTICAS | Cerradas en la iteración |
|---|---|---|---|---|
| It0 (línea base) | **31** | 6 | 3 | — |
| **It1 (cierre 2026-07-12)** | **16** (G01–G03, G06, G12–G23, G26, G30 · con G05/G07/G28 parciales) | 3 (G25, G27, H06, H08) | 1 (H09) | **15** (G04, G08–G11, G24, H01–H05, H07, H10–H12 + 3 parciales) |
| **It2 (cierre 2026-07-12)** | **15** | 3 | 1 | **1** (G17 ⭐ E1 completo: motor de diff, 3 vistas, highlights, caché por par) |
| It3..It8 | (se actualiza al cierre de cada iteración) | | | |

## 7. Preguntas abiertas (DECISIÓN PENDIENTE)

1. SSO corporativo A3: proveedor(es) IdP y tenant del operador.
2. Wompi: llaves sandbox/productivas (misión posterior).
3. Constancia E4: verificación online con QR (por ahora offline-only, T6).
4. Visibilidad de `version.downloaded` de terceros para no-admins (adoptado: solo admin, T12).
5. "80% frontend": interpretado como rutas clave a 80% + global jest 60 (DP-A5) — objetar si
   se quería 80 global.
