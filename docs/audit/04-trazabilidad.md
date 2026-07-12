# 04 — Matriz de trazabilidad escenario → pruebas

> Se crea como esqueleto en Fase 2 y se rellena AL CIERRE DE CADA iteración: la iteración que
> implementa un flujo agrega TODAS las filas de sus escenarios (de `03-mapa-flujos.md`) con sus
> celdas de prueba. Gate de cierre de misión: 0 escenarios sin fila, 0 filas sin prueba
> (salvo `n/a` justificado), 0 pruebas huérfanas (sin escenario).

**Iteración**: **It4** · **Fecha**: 2026-07-12 ·
**Escenarios totales (03)**: 258 · **Con fila aquí**: 11 (U/H) + 45 (B/C) + 9 (E1) + 28 (D4/D5/NTF) + 22 (D1/D2/D3/ACT/A11Y) ·
**VERDES**: 11 + 40 + 9 + 28 + 22 = **110** · **Pendientes**: 148

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
| U8 sign-in sesión real | BLOQ | — | `authStore.test.ts` | `test_auth_endpoints::sign_in` | `session.spec.ts::U8` | **VERDE** |
| U9 sign-out | ENR | — | `layout.test.tsx` | — | `session.spec.ts::U9` | **VERDE** |
| H1 landing | BLOQ | — | `app/__tests__/home.test.tsx` | — | `smoke.spec.ts` | VERDE |
| H2 ayuda /manual | COSM | — | — | — | — | PENDIENTE (It8) |

### Módulo A (38 escenarios) — filas se agregan en It6
`A1-*` (11) · `A2-*` (15) · `A3-*` (12). Estado: PENDIENTE (It6).

### Módulo B — It1 entregó B1 y B2 mínimo (B3 → It5; B4 UI → It6)

| Escenario | Sev | Unit BE | Unit FE | Integración | E2E | Estado |
|---|---|---|---|---|---|---|
| B1-F01 | BLOQ | `test_project_endpoints::test_create_project_makes_creator_admin` | `app/projects/__tests__` (board) | ✔ matriz P01–P04 | `b1-create-project.spec.ts::B1-F01` | **VERDE** |
| B1-E01 | ENR | — | `ProjectForm` (inline) | `test_create_project_rejects_blank_name` | `b1-create-project.spec.ts::B1-E01` | **VERDE** |
| B1-L01 | BLOQ | — | — | — | — | PENDIENTE (It7: límites de plan) |
| B1-P01..P04 | BLOQ | `test_permissions.py` | — | `test_create_project_permission_matrix` (7 actores) | n/a (regla anti-explosión) | **VERDE** |
| B2-F01 | BLOQ | — | `[B2-F01] renders project cards…` | `test_board_lists_member_projects_with_role` | `b1-create-project.spec.ts::B1-F01b` | **VERDE** |
| B2-A02 | BLOQ | — | — | `test_board_search_by_name` | ✔ (board search) | **VERDE** |
| B2-L01 | BLOQ | — | `[B2-L01] guided empty state` | — | — | **VERDE** |
| B2-A01/A03/A04, B2-L02 | BLOQ/ENR | — | — | — | — | PENDIENTE (It5) |
| B2-P01..P04 | BLOQ | `test_permissions.py` | — | `test_project_detail_permission_matrix` + `test_org_member_without_project_membership_sees_empty_board` | n/a | **VERDE** |
| B3-A02 | ENR | — | — | `test_admin_edits_project_metadata` | — | **VERDE** (resto de B3 → It5) |
| B3-* (F01–F03, A01, E01, L01, P) | BLOQ | — | — | — | — | PENDIENTE (It5) |
| B4-F01 | BLOQ | `test_trash_service::archive_makes_project_read_only_and_reversible` | — | `test_archive_and_unarchive_roundtrip` | — (UI It6) | **VERDE (backend)** |
| B4-F02/F03 | BLOQ | `test_trash_project_requires_exact_name_confirmation` | — | `test_trash_requires_exact_name_and_restore_recovers` | — (UI It6) | **VERDE (backend)** |
| B4-E01 (T4: sellos ⇒ solo archivar) | BLOQ | `test_project_with_approved_version_only_archivable` | — | ✔ | — | **VERDE (backend)** |
| B4-E02 | ENR | `test_project_restore_with_live_slug_collision_is_rejected` | — | — | — | **VERDE (backend)** |
| B4-A02 (purga 30d) | BLOQ | `test_purge_removes_expired_and_number_is_never_reused` | — | — | n/a (beat) | **VERDE** |
| B4-L01 (archivado read-only) | BLOQ | `test_version_service::test_archived_project_rejects_uploads` | — | ✔ | — | **VERDE (backend)** |
| B4-P01..P04 | BLOQ | — | — | `test_trash_project_permission_matrix` + `test_org_trash_permission_matrix` | — | **VERDE** |

### Módulo C — It1 completo (OCR de C1-A02 → It5)

| Escenario | Sev | Unit BE | Unit FE | Integración | E2E | Estado |
|---|---|---|---|---|---|---|
| C1-F01 | BLOQ | `test_analysis_pipeline::test_v1_indexes_the_eight_known_sections` | `[C1-F01-ui]` UploadDropzone | `test_upload_first_version_via_api_indexes_sections` | `c1-upload-first-document.spec.ts::C1-F01` | **VERDE** |
| C1-A01 (cancelar preview) | ENR | — | `[C1-A01]` | — | ✔ (mismo spec) | **VERDE** |
| C1-A03 (fallback sin encabezados) | BLOQ | `test_headless_pdf_falls_back_to_page_sections` | — | — | — | **VERDE** |
| C1-E01 (protegido) | BLOQ | `test_protected_pdf_is_rejected` | — | `test_protected_pdf_is_rejected_with_actionable_message` | `c1-…::C1-E01` (preview local) | **VERDE** |
| C1-E02 (corrupto) | BLOQ | `test_corrupt_file_is_rejected` | `[C1-E02-ui]` | `test_corrupt_file_is_rejected` | n/a (representativo E01) | **VERDE** |
| C1-E03 (tamaño) | BLOQ | — | UploadDropzone (max MB) | `test_oversized_upload_is_rejected` | n/a | **VERDE** |
| C1-E04 (análisis falla) | BLOQ | `engine/tasks::_fail` | `[C1-E04-ui]` | — | — | **VERDE** |
| C1-L01 (proyecto vacío) | BLOQ | — | — | — | ✔ (`b1` empty state) | **VERDE** |
| C1-A02 (escaneado/OCR) | BLOQ | `test_scanned_pdf_is_detected_and_degraded` | — | — | — | PARCIAL (detección sí; OCR → It5) |
| C1-P01..P04 | BLOQ | — | — | `test_create_document_permission_matrix` + `test_upload_intent_permission_matrix` | n/a | **VERDE** |
| C2-F01 | BLOQ | `test_second_version_matches_identity_and_retires_removed` | `[C2-F01-ui]` | ✔ | `c2-upload-new-version.spec.ts::C2-F01` | **VERDE** |
| C2-A01 (editar mensaje borrador) | ENR | `test_message_editable_while_draft_with_audit_trail` | `[C2-A01-ui]` VersionTimeline | `test_author_edits_draft_message` | ✔ (mismo spec) | **VERDE** |
| C2-E01 (binario idéntico) | BLOQ | `test_identical_binary_is_rejected` | — | `test_upload_identical_binary_returns_409` | ✔ (mismo spec) | **VERDE** |
| C2-E02 (mensaje congelado) | BLOQ | `test_message_frozen_once_approved` + `test_frozen_columns_reject_change_after_ready` | `[C2-E02-ui]` | `test_edit_message_permission_matrix` | — | **VERDE** |
| C2-C01 (ráfaga) | BLOQ | `test_version_number_is_unique_per_document` (I1 + select_for_update) | — | — | — | **VERDE** |
| C2-P01..P04 | BLOQ | — | — | ✔ matriz | n/a | **VERDE** |
| C3-F01 (timeline) | BLOQ | — | `[C3-F01]` VersionTimeline | `test_timeline_shows_versions_with_thumbs_and_tombstones` | `c3-version-history.spec.ts` | **VERDE** |
| C3-F02 (descarga firmada) | BLOQ | `test_signed_urls` | — | `test_download_returns_signed_url_and_audits` | ✔ (mismo spec) | **VERDE** |
| C3-L02 (locked plan free) | BLOQ | — | — | — | — | PENDIENTE (It7) |
| C3-P01..P04 | BLOQ | — | — | `test_version_detail_permission_matrix` | n/a | **VERDE** |
| C4-F01/F02 | BLOQ | `test_latest_draft_version_goes_to_trash` + `test_restore_returns_version_to_timeline` | `[C4-F01-ui]` + `[C4-F01-2p]` | `test_trash_and_restore_version_roundtrip` | `c4-delete-draft-version.spec.ts` | **VERDE** |
| C4-A01 (purga, tombstone I1) | BLOQ | `test_purge_removes_expired_and_number_is_never_reused` | — | — | — | **VERDE** |
| C4-E01 (sellada/aprobada) | BLOQ | `test_approved_version_is_never_trash_eligible` + `test_physical_delete_requires_trash_first` (trigger PG) | — | — | — | **VERDE** |
| C4-E02/E03 | BLOQ/ENR | `test_non_latest_version_cannot_be_trashed` + `test_restore_blocked_when_newer_version_exists` | — | — | — | **VERDE** |
| C4-P01..P04 | BLOQ | — | — | ✔ matriz | n/a | **VERDE** |

### Módulo D (58) — It3 (D4, D5) · It4 (D1, D2, D3)
`D1-*` (10) · `D2-*` (8) · `D3-*` (12) · `D4-*` (13) · `D5-*` (15). Estado: PENDIENTE.

### Módulo E — It2 entregó E1 (E3 → It5; E2/E4 → It7)

| Escenario | Sev | Unit BE | Unit FE | Integración | E2E | Estado |
|---|---|---|---|---|---|---|
| E1-F01 (3 vistas, tabla de verdad) | BLOQ | `test_comparison_engine::test_truth_table_*` (conteos exactos 2/1/1) | `[E1-F01]` SectionChangeList + `sync.test` + `coords.test` | `test_compare_two_versions_returns_the_truth_table` | `e1-compare-versions.spec.ts::E1-F01` | **VERDE** |
| E1-F02 (deep-link + navegación entre vistas) | BLOQ | — | `[E1-F02]` SectionChangeList | `test_section_diff_endpoint_returns_word_level_ops` | ✔ (mismo spec: `#sec-…`) | **VERDE** |
| E1-A01 (par no adyacente v1↔v3) | BLOQ | `test_comparison_of_non_adjacent_versions_accumulates_changes` | — | ✔ | — | **VERDE** |
| E1-A02 (caché por par) | ENR | — | — | `test_second_request_for_the_same_pair_is_served_from_cache` | — | **VERDE** |
| E1-E01 (versión fallida / misma versión) | BLOQ | — | — | `test_compare_against_a_failed_version_is_rejected` + `test_compare_with_the_same_version_twice_is_rejected` | — | **VERDE** |
| E1-L01 (sin cambios) | BLOQ | `test_identical_versions_report_no_changes` | CompareView (`no-changes`) | — | `e1-…::E1-L01` | **VERDE** |
| E1-P01..P04 | BLOQ | — | — | `test_compare_permission_matrix` + `test_comparison_detail_permission_matrix` | n/a | **VERDE** |
| D5-A01 (renumeración ⇒ identidad sobrevive) | BLOQ | `test_truth_table_renumbered_sections_are_not_changes` + `test_persistence::test_renamed_section_reuses_the_same_identity_row` | — | — | ✔ (E1 spec: confidencialidad no aparece como cambio) | **VERDE (base de D5)** |
| C3-A01 (saltar a comparar desde el timeline) | BLOQ | — | — | — | ✔ (E1 spec: selección de 2 versiones) | **VERDE** |
| E2-*, E3-*, E4-* | BLOQ | — | — | — | — | PENDIENTE (It5/It7) |

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
