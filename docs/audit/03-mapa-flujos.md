# 03 — Mapa exhaustivo de flujos y escenarios

> **La regla de oro: si un escenario no está en este mapa, no existe.** Ninguna prueba nueva
> sin fila aquí; ningún escenario aquí sin fila en `04-trazabilidad.md`. Acceptance criteria
> come from `docs/plan/01-alcance-mvp.md`; this map expands them into every testable scenario.

**Iteración**: It0 · **Commit**: `527d61c` · **Fecha**: 2026-07-12 ·
**Escenarios mapeados**: **258** = 246 de producto (con P01–P04 expandidos: A 38 · B 42 ·
C 45 · D 58 · E 37 · F 26) + 11 heredados (U1–U9, H1–H2) + 1 máster (M1, atraviesa 16 pasos)

## 0. Leyenda y reglas

### 0.1 Gramática de ids

`<FlowId>-<Clase><##>` — ej. `D5-F01`, `C2-E03`, `A2-P02`, `D4-C01`.

| Clase | Significado | Nivel de prueba mínimo |
|---|---|---|
| `F##` | Camino feliz (criterios de plan/01) | **E2E siempre** + integración |
| `A##` | Camino alterno legítimo | unit + integración; E2E solo si BLOQUEANTE |
| `E##` | Error (entrada inválida, fallo de job, estado ilegal) | unit + integración; 1 representativo E2E por flujo |
| `P##` | Permisos | **integración parametrizada** (matriz 7 actores); a E2E solo ocultamiento UI representativo |
| `L##` | Estado límite (vacíos, única versión, sellada, locked, límites de plan) | unit/integración + RTL (estado de pantalla) |
| `C##` | Concurrencia | unit/integración transaccional; E2E solo `D4-C01` |
| `X##` | Exclusión de alcance (la UI no expone / endpoint ausente) | verificación negativa en integración |
| `T##` | Prueba/promoción temporal (trial Pro, It9) | integración + tarea beat; RTL para el aviso |
| `S##` | Reuso puro de servicio (superficie pública sin tenencia) | unit sobre funciones puras |

Anexos: `U1..U9` (auth heredado), `H1..H2` (landing/ayuda), `M1` (prueba maestra).
Módulos añadidos en It9 (§7.bis): `PC` (comparador público anónimo), `PR` (precios
públicos), `TR`/clase `T` (prueba Pro), más los anexos `MAN`/`ADM`/`HOME`/`A11Y`/`NTF`
y el anexo de infraestructura `FD` (fake data — no es producto).

### 0.2 Reglas anti-explosión (vinculantes)

1. **P = 4 escenarios fijos por flujo**: P01 permitido con rol mínimo · P02 denegado con el rol
   inmediato inferior (403) · P03 anónimo (401) · P04 no-miembro/objeto ajeno (**404**, I12).
   La matriz completa de 7 actores (owner, admin, editor, reviewer, viewer, no-miembro,
   anónimo) vive SOLO en integración parametrizada (`pytest.param(id='<flujo>-p0X-<rol>')`).
2. **Errores de archivo** (protegido/corrupto/tamaño/duplicado): unit+integración; a E2E solo
   `C1-E01`.
3. **Concurrencia**: unit/integración; a E2E solo `D4-C01` (promesa de producto).
4. **Estados de pantalla**: se verifican en RTL con factories de estado (§9); E2E no re-asevera
   vacío/cargando salvo que aparezcan en el camino feliz.
5. Un escenario = una fila = a lo sumo un test E2E dedicado. Los tests-viaje (M1) declaran sus
   `@scenario:` pero no sustituyen el E2E dedicado de un BLOQUEANTE.

### 0.3 Tags y títulos (contrato con el reporter)

- `@flow:` lleva **solo** ids existentes en `flow-definitions.json` (un id inventado contamina
  el flow-coverage-reporter). `@scenario:<id-minúsculas>` es adicional y el reporter lo ignora.
- Títulos de test comienzan con el id: `test('D5-F01 — ...')`, `it('[C1-L01] ...')`,
  `@pytest.mark.escenario("C2-E01")`.
- Prohibido `test.skip`: un flujo sin implementar se representa como `missing` (sin spec).

---

## 1. Módulo A · Cuenta y acceso

### A1 — Registro y primer momento wow · P1 · It6
Rutas: `/sign-up`, `/onboarding` · Endpoints: `sign_up/` (extendido), `orgs/{org}/sample-project/`, `jobs/{id}/` · Estado: **No implementado** (solo sign-up básico)

| ID | Clase | Escenario (GWT compacto) | Rol | Sev. |
|---|---|---|---|---|
| A1-F01 | F | Registro email → org personal auto → wizard → job siembra proyecto ejemplo (fixtures v1/v2) → ve comparación funcionando SIN subir nada | guest | BLOQ |
| A1-F02 | F | Paso final del wizard: sube su propio PDF → C1 corre sobre su documento real | owner | BLOQ |
| A1-A01 | A | Registro con Google → mismo wizard y siembra | guest | BLOQ |
| A1-A02 | A | Usuario salta el wizard → puede retomarlo después (progreso persistido) | owner | ENR |
| A1-A03 | A | Reintento de siembra fallida → job idempotente re-crea el proyecto ejemplo | owner | ENR |
| A1-E01 | E | Falla el job de siembra → wizard muestra error con reintento (no pantalla rota) | owner | BLOQ |
| A1-L01 | L | Métrica de activación: timestamps sign-up → primera comparación vista (S1 < 5 min) | sistema | ENR |
| A1-P01..P04 | P | Onboarding/sample-project: dueño de la org ✓ · miembro no-owner de otra org 403 · anónimo 401 · org ajena 404 | — | BLOQ |

### A2 — Invitar al equipo y asignar roles · P1 · It6
Rutas: `/org/settings` (Miembros), `/invite/[token]` · Endpoints: `orgs/{org}/invitations/`, `invitations/{token}/`, `invitations/accept/`, `projects/{proj}/members/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| A2-F01 | F | Admin invita email+rol reviewer → email con token (mailpit) → invitado crea cuenta con email prellenado → aterriza DIRECTO en el proyecto con capacidades de reviewer | admin→guest | BLOQ |
| A2-F02 | F | Cambiar rol de un miembro → capacidades cambian de inmediato (UI y API) | admin | BLOQ |
| A2-A01 | A | Invitado CON cuenta existente acepta logueado → membresía creada sin re-registro | user | BLOQ |
| A2-A02 | A | Reenviar invitación pendiente → nuevo email, mismo token válido | admin | ENR |
| A2-A03 | A | Revocar invitación → el token deja de servir (pantalla de token inválido) | admin | ENR |
| A2-A04 | A | Remover miembro → pierde acceso (404 en recursos del proyecto, I12) | admin | BLOQ |
| A2-E01 | E | Token expirado/inválido/revocado → pantalla dedicada con explicación | guest | BLOQ |
| A2-E02 | E | Invitar email que ya es miembro → 409 con aviso | admin | ENR |
| A2-E03 | E | Remover/degradar al ÚLTIMO owner de la org → bloqueado (guard ≥1 owner) | owner | BLOQ |
| A2-L01 | L | Plan free con 2 usuarios: 3ª invitación → 402 con CTA de plan (cruza F1-L02) | admin | BLOQ |
| A2-C01 | C | Doble aceptación del mismo token (dos pestañas) → segunda idempotente/409 limpio | guest | ENR |
| A2-P01..P04 | P | Invitar: admin ✓ · editor 403 · anónimo 401 · org ajena 404 | — | BLOQ |

### A3 — Seguridad de la cuenta (2FA + sesiones) · P2 · It6
Rutas: `/settings` (tab Seguridad) · Endpoints: `me/2fa/*`, `me/sessions/*` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| A3-F01 | F | Enrolar TOTP (QR + código de confirmación) → próximo login exige TOTP → entra | user | BLOQ |
| A3-F02 | F | Ver sesiones activas (dispositivo, fecha) y revocar una → su refresh token muere (blacklist) | user | BLOQ |
| A3-A01 | A | Generar códigos de respaldo; usar uno en login (consumible una vez) | user | ENR |
| A3-A02 | A | Deshabilitar 2FA con password + TOTP vigente | user | ENR |
| A3-E01 | E | TOTP incorrecto → error, sesión NO creada | guest | BLOQ |
| A3-E02 | E | Reuso de un código de respaldo ya consumido → rechazado | guest | ENR |
| A3-L01 | L | "Cerrar todas las sesiones" → incluye la actual (re-login) | user | ENR |
| A3-P01..P04 | P | Gestión 2FA/sesiones: solo el propio usuario (recurso ajeno 404) | — | BLOQ |
| A3-X01 | X | SSO corporativo NO expuesto — **DECISIÓN PENDIENTE** (IdP/credenciales del operador) | — | — |

---

## 2. Módulo B · Proyectos

### B1 — Crear un proyecto · P1 · It1
Rutas: `/projects/new` · Endpoints: `POST orgs/{org}/projects/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| B1-F01 | F | Nombre+descripción → creado en ≤30 s de esfuerzo; creador queda project admin; aterriza en proyecto vacío con dropzone-guía | editor org | BLOQ |
| B1-A01 | A | Crear aplicando plantilla de checklist org → config v1 con checks copiados (It5) | admin | ENR |
| B1-E01 | E | Nombre vacío / >límite → validación inline sin submit | editor | ENR |
| B1-L01 | L | Plan free con 1 proyecto activo → 402 + modal de límite con CTA (cruza F1-L01) | editor | BLOQ |
| B1-P01..P04 | P | Crear: org member ✓ · (no hay rol inferior en org: P02 = usuario de OTRA org 403/404) · anónimo 401 · org ajena 404 | — | BLOQ |

### B2 — Tablero de proyectos · P2 · It1 (mínimo) / It5 (completo)
Rutas: `/projects` · Endpoints: `GET orgs/{org}/projects/`, `GET search/documents/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| B2-F01 | F | Tablero con cards y estado derivado correcto (borrador/en revisión/con observaciones/aprobado) | viewer | BLOQ |
| B2-A01 | A | Filtro por estado | viewer | BLOQ (It5) |
| B2-A02 | A | Búsqueda por nombre | viewer | BLOQ (It5) |
| B2-A03 | A | Búsqueda por CONTENIDO (FTS spanish sobre secciones) → resultado enlaza al documento | viewer | BLOQ (It5) |
| B2-A04 | A | Filtro "archivados" muestra los read-only (B4) | viewer | ENR |
| B2-L01 | L | Sin proyectos → vacío con guía "crea tu primer proyecto" (CTA a B1) | member | BLOQ |
| B2-L02 | L | >25 proyectos → paginación | viewer | ENR |
| B2-P01..P04 | P | Solo proyectos donde soy miembro (scoping I12); anónimo 401; org ajena vacía/404 | — | BLOQ |

### B3 — Configuración del proyecto · P2 · It5
Rutas: `/projects/[id]/settings` · Endpoints: `GET/PUT projects/{proj}/config/`, `PATCH projects/{proj}/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| B3-F01 | F | Editar checklist → se crea NUEVA ProjectConfigVersion (nunca in-place); aviso "rige desde la próxima versión" | admin | BLOQ |
| B3-F02 | F | Editar dueños de sección (matcher stable_key/glob + revisor) | admin | BLOQ |
| B3-F03 | F | Editar reglas de aprobación + `d5_mode` (auto/coordinator) | admin | BLOQ |
| B3-A01 | A | Aplicar plantilla org → nueva config con items copiados (copy-on-apply, I8 intacto) | admin | ENR |
| B3-A02 | A | Editar metadatos nombre/descripción del proyecto (slug inmutable) | admin | ENR |
| B3-E01 | E | Matcher de dueño inválido / check con params malformados → validación 400 | admin | ENR |
| B3-L01 | L | No-retroactividad: la versión existente se sigue evaluando con SU config pineada (I8) | sistema | BLOQ |
| B3-P01..P04 | P | Config: admin ✓ · reviewer 403 · anónimo 401 · ajeno 404 (viewer además NO ve la UI de settings) | — | BLOQ |

### B4 — Archivar y eliminar proyecto · P2 · It6 (mecanismo papelera en It1)
Rutas: `/projects/[id]/settings` (Peligro), `/org/trash` · Endpoints: `DELETE projects/{proj}/`, `restore/`, `archive/`, `orgs/{org}/trash/`, `purge/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| B4-F01 | F | Archivar → read-only con badge (uploads/sellos deshabilitados), reversible sin gracia | admin | BLOQ |
| B4-F02 | F | Eliminar proyecto SIN sellos → TypeToConfirm (nombre exacto) → papelera con countdown 30 días | admin | BLOQ |
| B4-F03 | F | Restaurar desde papelera → vuelve intacto | admin | BLOQ |
| B4-A01 | A | Purga anticipada (owner, segunda confirmación) → borrado físico auditado | owner | ENR |
| B4-A02 | A | Purga automática a los 30 días (beat `purge_trashed`) | sistema | BLOQ |
| B4-E01 | E | Eliminar proyecto CON ≥1 sello → BLOQUEADO con explicación + CTA archivar (T4; "lo sellado es inmutable") | admin | BLOQ |
| B4-E02 | E | Restore con colisión de slug vivo → 409 "renombra el proyecto activo primero" | admin | ENR |
| B4-L01 | L | Proyecto archivado: toda mutación (subir, sellar, observar, config) deshabilitada UI + 409 API | todos | BLOQ |
| B4-P01..P04 | P | Eliminar: project admin ✓ · editor 403 · anónimo 401 · ajeno 404; purga: SOLO owner | — | BLOQ |

---

## 3. Módulo C · Documentos y versiones

### C1 — Subir el primer documento · P1 · It1 (OCR en It5)
Rutas: `/projects/[id]` (dropzone) · Endpoints: `POST projects/{proj}/documents/`, `upload_intent/`, `complete/`, `GET jobs/{id}/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| C1-F01 | F | Drag&drop `contrato_v1.pdf` → **preview local pre-subida** (páginas + mensaje) → confirmar → presigned PUT + complete → job de análisis → v1 con 8 secciones, semáforo y miniatura | editor | BLOQ |
| C1-A01 | A | Cancelar en el preview → cero red gastada (ni intent) | editor | ENR |
| C1-A02 | A | PDF **escaneado** → escenario `scanned_ocr`, secciones vía OCR con confianza por sección (It5) | editor | BLOQ |
| C1-A03 | A | PDF sin encabezados → fallback sección-por-página + banner de modo degradado (DP-09) | editor | BLOQ |
| C1-E01 | E | PDF protegido (`protegido.pdf`) → rechazo con mensaje accionable — **representativo E2E** | editor | BLOQ |
| C1-E02 | E | Corrupto/no-PDF (`corrupto.pdf`) → rechazo por magic bytes/parse | editor | BLOQ |
| C1-E03 | E | Archivo > tamaño del plan → rechazo en intent (content-length-range) y re-verificado en complete | editor | BLOQ |
| C1-E04 | E | Análisis falla → versión `failed` visible con causa legible + botón reintentar | editor | BLOQ |
| C1-L01 | L | Proyecto sin documentos → estado vacío con guía (dropzone protagonista) | editor | BLOQ |
| C1-C01 | C | Doble `complete/` del mismo upload (retry de red) → idempotente, una sola versión | editor | ENR |
| C1-P01..P04 | P | Subir: editor ✓ · reviewer 403 · anónimo 401 · proyecto ajeno 404 | — | BLOQ |

### C2 — Subir una nueva versión ("el commit") · P1 · It1
Rutas: `/projects/[id]/documents/[docId]` · Endpoints: `upload_intent/`, `complete/`, `PATCH versions/{ver}/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| C2-F01 | F | Sube `contrato_v2.pdf` con mensaje → análisis+comparación automáticos → PostUploadSummary EXACTO: "2 modificadas, 1 eliminada, 1 añadida" (tabla de verdad) | editor | BLOQ |
| C2-A01 | A | Editar mensaje/descripción MIENTRAS borrador (I2b) → AuditEvent before/after | editor autor | ENR |
| C2-E01 | E | Binario idéntico (mismo sha256) → rechazo "idéntica a vN" (F6) | editor | BLOQ |
| C2-E02 | E | Editar mensaje tras solicitud de revisión/sello/aprobación → congelado (UI sin lápiz + API 409) | editor | BLOQ |
| C2-L01 | L | Documento con UNA sola versión → comparar deshabilitado con explicación | viewer | BLOQ |
| C2-L02 | L | Subir sobre documento con versión aprobada → permitido; el puntero aprobado NO se mueve solo (D5 gobierna) | editor | BLOQ |
| C2-C01 | C | Dos uploads en ráfaga → serialización por documento (I1): números N+1/N+2 sin colisión | editor | BLOQ |
| C2-P01..P04 | P | editor ✓ · reviewer 403 · anónimo 401 · ajeno 404 | — | BLOQ |

### C3 — Navegar el historial · P2 · It1
Rutas: `/projects/[id]/documents/[docId]` · Endpoints: `GET documents/{doc}/versions/`, `GET versions/{ver}/download/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| C3-F01 | F | Timeline: cada versión con autor/fecha/mensaje/semáforo/**miniatura**/badge aprobada | viewer | BLOQ |
| C3-F02 | F | Descargar cualquier versión → 302 URL firmada TTL + AuditEvent | viewer | BLOQ |
| C3-A01 | A | Seleccionar dos versiones cualesquiera → salto a la comparación (E1) | viewer | BLOQ |
| C3-A02 | A | Historial por sección (blame): en qué versión cambió esta sección | viewer | ENR |
| C3-L01 | L | >25 versiones → paginación del timeline | viewer | ENR |
| C3-L02 | L | Versión `locked` por plan (>30 días, free) → visible con candado, descarga/comparación bloqueadas + CTA plan | viewer | BLOQ |
| C3-P01..P04 | P | Ver/descargar: viewer ✓ (todos los roles de proyecto) · no-miembro 404 · anónimo 401 | — | BLOQ |

### C4 — Eliminar una versión borrador · P2 · It1
Rutas: timeline + `/org/trash` · Endpoints: `DELETE versions/{ver}/`, `restore/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| C4-F01 | F | Eliminar la ÚLTIMA versión si es borrador → TypeToConfirm → papelera; timeline muestra tombstone "vN eliminada" | editor autor | BLOQ |
| C4-F02 | F | Restaurar desde papelera (si no existe versión posterior) → vuelve al timeline | editor autor | BLOQ |
| C4-A01 | A | Purga a los 30 días → número JAMÁS reutilizado (I1 tombstone); siguiente subida es N+1 | sistema | BLOQ |
| C4-E01 | E | Intentar eliminar versión con sello/aprobada → IMPOSIBLE (UI deshabilitada + API 409, I3) | admin | BLOQ |
| C4-E02 | E | Intentar eliminar una versión NO última → 409 | editor | BLOQ |
| C4-E03 | E | Restore con versión posterior ya subida → 409; el binario sigue descargable desde la papelera | editor | ENR |
| C4-P01..P04 | P | Eliminar: autor o admin ✓ · reviewer 403 · anónimo 401 · ajeno 404 | — | BLOQ |

---

## 4. Módulo D · Revisión y aprobación

### D1 — Solicitar revisión · P1 · It4
Rutas: version viewer + `/inbox` · Endpoints: `POST versions/{ver}/review_requests/`, `GET me/review_inbox/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| D1-F01 | F | Editor abre solicitud con selección MANUAL de revisores (DP-A7) → asignaciones creadas → notificación in-app+email → aparece en la bandeja de cada revisor con su scope | editor | BLOQ |
| D1-A01 | A | Config con dueños de sección → revisores AUTO-sugeridos con scope por secciones | editor | ENR |
| D1-A02 | A | Cancelar solicitud → asignaciones cerradas, revisores notificados | editor | ENR |
| D1-E01 | E | Solicitar sobre versión `failed` o en análisis → 409 | editor | BLOQ |
| D1-E02 | E | Solicitar habiendo ya una solicitud abierta → 409 (una activa por versión) | editor | ENR |
| D1-L01 | L | Bandeja vacía → "estás al día" | reviewer | ENR |
| D1-P01..P04 | P | Solicitar: editor ✓ · reviewer 403 · anónimo 401 · ajeno 404 | — | BLOQ |

### D2 — Revisar con asistencia · P1 · It4
Rutas: viewer con `?review=` · Endpoints: `GET review_requests/{id}/progress/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| D2-F01 | F | Revisor abre desde la bandeja → ve PRIMERO semáforo + resumen de cambios; "siguiente sección cambiada" navega el visor | reviewer | BLOQ |
| D2-F02 | F | Secciones sin cambio desde SU último sello → marcadas "ya revisado por ti" (S2) | reviewer | BLOQ |
| D2-A01 | A | Saltar directo a secciones con checks en rojo | reviewer | ENR |
| D2-L01 | L | Primera revisión del revisor (sin sello previo) → cero marcas "ya revisado" | reviewer | ENR |
| D2-P01..P04 | P | Progreso: revisor asignado ✓ · no asignado 403 · anónimo 401 · ajeno 404 | — | BLOQ |

### D3 — Observaciones ancladas · P1 · It4
Rutas: viewer (panel Observaciones) · Endpoints: `versions/{ver}/observations/`, `replies/`, `status/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| D3-F01 | F | Revisor selecciona zona de página (bbox) → comenta → estado `open` → autor notificado | reviewer | BLOQ |
| D3-F02 | F | Autor responde (`answered`) → revisor marca `resolved`; filtros por revisor/estado | editor/reviewer | BLOQ |
| D3-A01 | A | Reabrir observación resuelta → `open` de nuevo (I14 permite) | reviewer | ENR |
| D3-A02 | A | Filtrar hilo por revisor y por estado | viewer | BLOQ |
| D3-A03 | A | Nueva versión → observación RE-ANCLADA a su sección (anchor por versión) | sistema | BLOQ |
| D3-A04 | A | La sección desaparece en la versión nueva → anchor `orphaned` visible con aviso | sistema | BLOQ |
| D3-E01 | E | Transición ilegal (`open→resolved` sin pasar por responder si la máquina lo exige / estado inválido) → 400/409 (I14) | reviewer | ENR |
| D3-C01 | C | Dos respuestas simultáneas al hilo → ambas persisten ordenadas | ambos | ENR |
| D3-P01..P04 | P | Crear: reviewer/editor ✓ · **viewer 403 (sí lee)** · anónimo 401 · ajeno 404 | — | BLOQ |

### D4 — Aprobar con sello · P1 · It3
Rutas: viewer (tab Sellos) · Endpoints: `POST versions/{ver}/seals/`, `GET seals/{seal}/verify/`, `POST seals/{seal}/revoke/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| D4-F01 | F | Revisor asignado sella {secciones} en un clic → registra quién/cuándo/versión exacta/secciones + firma Ed25519 (I6); panel muestra puestos/faltantes | reviewer | BLOQ |
| D4-F02 | F | Último sello requerido → versión APROBADA y congelada; badge; puntero único por documento (I5) | reviewer | BLOQ |
| D4-A01 | A | Sello `covers_all` (documento completo) | reviewer | BLOQ |
| D4-A02 | A | Retirar MI sello antes de la aprobación (DP-08) → evento append-only + recompute | reviewer | ENR |
| D4-E01 | E | Sellar una versión que no es la última analizada → 409 (I10) | reviewer | BLOQ |
| D4-E02 | E | Sellar sin asignación en la solicitud → 403 | reviewer | BLOQ |
| D4-E03 | E | Payload adulterado → `verify/` detecta firma inválida | sistema | BLOQ |
| D4-L01 | L | Versión `failed`/en análisis → sellar imposible (I10) | reviewer | BLOQ |
| D4-C01 | C | **Dos revisores sellan simultáneamente** → ambos sellos persisten (`unique(version,reviewer)`), aprobación recomputada consistente — **único C en E2E** | reviewers | BLOQ |
| D4-P01..P04 | P | Sellar: reviewer asignado ✓ (admin/owner como revisores implícitos) · **editor 403** · anónimo 401 · ajeno 404 | — | BLOQ |

### D5 — Re-entrega e invalidación selectiva 💎 · P1 · It3
Rutas: viewer (Sellos) + `/inbox` (re-review + confirmaciones) · Endpoints: `GET versions/{ver}/seal_plan/`, `POST seal_plan/confirm/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| D5-F01 | F | v nueva cambia sección X: sello que cubre X → `invalidated` + re-review scoped + email SOLO a ese revisor; sellos de secciones intactas → `preserved` CON constancia (hashes verificados); CERO notificación a preservados (S4/S6) — la queen | sistema | BLOQ |
| D5-F02 | F | `d5_mode=coordinator` → plan `pending_confirmation` (bloquea aprobación y sellos nuevos; comparar/observar siguen); coordinador confirma fila a fila o "aplicar todo" | coordinador | BLOQ |
| D5-A01 | A | Renumeración sin cambio de cuerpo (tabla de verdad §7→6, §8→7) → identidad sobrevive, sellos PRESERVADOS | sistema | BLOQ |
| D5-A02 | A | Sección eliminada cubierta por un sello → invalida (constancia parcial de las intactas del mismo sello) | sistema | BLOQ |
| D5-A03 | A | OCR con confianza < 0.75 o modo degradado → coordinator FORZADO aunque config diga auto (It5) | sistema | BLOQ |
| D5-A04 | A | `covers_all`: cualquier cambio (incl. sección agregada) invalida; cero diffs (re-render) preserva | sistema | BLOQ |
| D5-A05 | A | Coordinador hace override de una propuesta (invalidar→preservar) viendo evidencia → auditado | coordinador | ENR |
| D5-E01 | E | Matching ambiguo (similitud 0.55–0.85 / split / merge) → INVALIDA (sesgo conservador I7; property test: ningún camino preserva sin igualdad de hash) | sistema | BLOQ |
| D5-L01 | L | El documento pierde TODAS sus secciones → todo invalidado, semáforo rojo estructural, coordinator forzado, no sellable | sistema | BLOQ |
| D5-C01 | C | v(N+1) llega con plan de vN pendiente → records de vN `superseded` (sin notificar), D5 corre contra última ready confirmada, notifs deduplicadas | sistema | BLOQ |
| D5-C02 | C | Sello puesto mientras corre seal_review → serialización por documento lo ordena sin corrupción | sistema | ENR |
| D5-P01..P04 | P | Confirmar plan: coordinador (admin/designado) ✓ · reviewer no designado 403 · anónimo 401 · ajeno 404 | — | BLOQ |

---

## 5. Módulo E · Comparación y análisis

### E1 — Comparar dos versiones ⭐ · P1 · It2
Rutas: `.../compare/[base]/[target]` · Endpoints: `POST documents/{doc}/comparisons/`, `GET comparisons/{cmp}/`, `.../sections/{sec}/diff/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| E1-F01 | F | Comparar v1↔v2 → lado a lado sincronizado POR SECCIÓN con highlights + lista de secciones EXACTA según tabla de verdad + resumen | viewer | BLOQ |
| E1-F02 | F | Conmutación entre las 3 vistas conservando la sección activa; deep-link `#sec-<key>` | viewer | BLOQ |
| E1-A01 | A | Comparar cualquier par NO adyacente (v1↔v3) | viewer | BLOQ |
| E1-A02 | A | Segunda apertura del mismo par → cache (200 sin job) | viewer | ENR |
| E1-E01 | E | Comparar contra una versión `failed` → 409/422 con mensaje | viewer | BLOQ |
| E1-L01 | L | Versiones idénticas en texto → estado explícito "sin cambios" (no diff vacío roto) | viewer | BLOQ |
| E1-P01..P04 | P | Comparar: viewer ✓ · no-miembro 404 · anónimo 401 · (P02: sin rol inferior → usuario de otra org 404) | — | BLOQ |

### E2 — Comparaciones guardadas · P2 · It7
Rutas: `/projects/[id]` (tab/lista) + compare view · Endpoints: `POST comparisons/{cmp}/save/`, `GET projects/{proj}/saved_comparisons/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| E2-F01 | F | Guardar la comparación con nombre → aparece en la lista del proyecto | viewer+ | BLOQ |
| E2-F02 | F | Compartir enlace interno → otro MIEMBRO lo abre y ve la misma comparación | viewer | BLOQ |
| E2-A01 | A | Renombrar / eliminar una guardada (autor o admin) | autor/admin | ENR |
| E2-E01 | E | No-miembro abre el enlace → 404 (I12) | no-miembro | BLOQ |
| E2-P01..P04 | P | Guardar: miembro ✓ · anónimo 401 · ajeno 404 | — | BLOQ |

### E3 — Checks configurables · P2 · It5
Rutas: settings (Checklist) + viewer (tab Checks) · Endpoints: `projects/{proj}/config/`, `versions/{ver}/checks/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| E3-F01 | F | Admin arma checklist (presencia de sección/campo/valor) → la SIGUIENTE versión los corre → semáforo con evidencia página+razón | admin | BLOQ |
| E3-F02 | F | Click en la evidencia → el visor salta a la página/zona exacta | viewer | BLOQ |
| E3-A01 | A | Check en rojo NO bloquea por sí solo; approval_policy decide (semáforo informativo) | sistema | ENR |
| E3-A02 | A | Aplicar plantilla org (kit 2) → checks copiados en nueva config | admin | ENR |
| E3-E01 | E | Params de check malformados → 400 en PUT config | admin | ENR |
| E3-L01 | L | Config nueva NO re-evalúa versiones existentes (I8) | sistema | BLOQ |
| E3-P01..P04 | P | Configurar: admin ✓ · reviewer 403 · anónimo 401 · ajeno 404 | — | BLOQ |

### E4 — Constancia exportable · P2 · It7 (la exige M1)
Rutas: viewer (Sellos) · Endpoints: `POST versions/{ver}/certificates/`, `GET certificates/{id}/download/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| E4-F01 | F | Emitir constancia sobre versión APROBADA → PDF con historia, sellos, hashes y firmas; serial correlativo; re-descarga byte-idéntica | admin | BLOQ |
| E4-F02 | F | Verificación OFFLINE: payload canónico + firma + clave pública (`seal_keys/{key_id}/`) validan fuera del sistema | tercero | BLOQ |
| E4-A01 | A | Listar emisiones previas con serial y fecha | viewer | ENR |
| E4-E01 | E | Emitir sobre versión NO aprobada → 409 | admin | BLOQ |
| E4-E02 | E | Firma que no verifica al emitir (tamper) → aborta con alerta + AuditEvent | sistema | BLOQ |
| E4-P01..P04 | P | Emitir: admin ✓ · reviewer 403 · anónimo 401 · ajeno 404; descargar: viewer ✓ | — | BLOQ |

---

## 6. Módulo F · Administración y configuración

### F1 — Plan y límites · P2 · It7 (Wompi diferido)
Rutas: `/org/settings` (Plan) · Endpoints: `GET plans/`, `GET orgs/{org}/subscription/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| F1-F01 | F | Org free ve su plan, límites y uso actual | owner/admin | BLOQ |
| F1-A01 | A | CTA de upgrade → pantalla informativa (checkout Wompi diferido; sin cobro) | owner | BLOQ |
| F1-L01 | L | 2º proyecto activo en free → 402 + modal de límite (enforced I13) | editor | BLOQ |
| F1-L02 | L | 3er miembro en free → 402 | admin | BLOQ |
| F1-L03 | L | Versión >30 días en free → `locked`: visible, descarga/comparación bloqueadas con CTA (DP-04: acceso, NUNCA borrado) | viewer | BLOQ |
| F1-X01 | X | Checkout Wompi NO expuesto — **DECISIÓN PENDIENTE llaves** (misión posterior) | — | — |
| F1-P01..P04 | P | Plan/billing: owner gestiona ✓ · admin ve · editor 403 · anónimo 401 | — | BLOQ |

### F2 — Consumo y avisos · P2 · It7
Rutas: `/org/settings` (Plan/Uso) · Endpoints: `GET orgs/{org}/usage/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| F2-F01 | F | Panel de uso: proyectos activos / miembros / almacenamiento vs límites (UsageMeter) | owner/admin | BLOQ |
| F2-F02 | F | Aviso PREVENTIVO al cruzar 80% de un límite (banner + notificación in-app) | sistema | BLOQ |
| F2-L01 | L | Uso al 100% → la acción bloqueada referencia F1-L01/L02 (coherencia de mensajes) | — | ENR |
| F2-P01..P04 | P | Uso: owner/admin ✓ · editor 403 · anónimo 401 · ajena 404 | — | BLOQ |

### F3 — Auditoría (base) + históricos · P2 · It7 (feed en It4)
Rutas: `/org/audit` (admin), tab Activity por proyecto · Endpoints: `orgs/{org}/audit_events/`, `projects/{proj}/activity/` · Estado: **No implementado**

| ID | Clase | Escenario | Rol | Sev. |
|---|---|---|---|---|
| F3-F01 | F | `/org/audit`: eventos filtrables por actor/tipo/proyecto/rango de fechas + paginación | org admin | BLOQ |
| F3-F02 | F | Export CSV respetando los filtros activos | org admin | BLOQ |
| F3-A01 | A | Feed de actividad POR PROYECTO (whitelist humanizada, SIN ip/request_id) visible a todo miembro (kit 6) | viewer | ENR |
| F3-A02 | A | Reporte de estado del proyecto (sellos/checks/observaciones abiertas) + actividad por rango (kit 4) | viewer | ENR |
| F3-L01 | L | No-admin: `/org/audit` oculta en nav + API 403 | member | BLOQ |
| F3-P01..P04 | P | Audit log: org admin ✓ · project admin (no org) 403 · anónimo 401 · org ajena 404 | — | BLOQ |

---

## 7. M1 · LA PRUEBA MAESTRA (`e2e/master/master-journey.spec.ts`) · It8

Flujo `master-e2e-journey` (flow-definitions v2.1.0). Un solo test serial (justificado),
timeout 12 min, `d5_mode=auto` (coordinator queda cubierto por D5-F02), 3 contexts:
Editor (registrado por UI), Revisor A y Revisor B (invitados por UI). **Todo por UI: cero
consola, cero BD, cero seed por API.**

| Paso | Actor | Acción | Aserción exacta | Escenarios |
|---|---|---|---|---|
| 1 | Editor | Sign-up con email único | sesión creada, org personal visible | A1 (alta) |
| 2 | Editor | Crea proyecto | proyecto vacío con dropzone-guía | B1-F01 |
| 3 | Editor | Sube `contrato_v1.pdf` | v1: 8 secciones + semáforo | C1-F01 |
| 4 | Editor | Sube `contrato_v2.pdf` + mensaje | resumen "2 modificadas, 1 eliminada, 1 añadida" | C2-F01 |
| 5 | Editor | Abre comparación v1↔v2 | lista de secciones = tabla de verdad EXACTA | E1-F01 |
| 6 | Editor | Invita a Revisor A y B | 2 emails en mailpit con token | A2-F01 |
| 7 | A/B | Aceptan invitación (cuentas nuevas) | aterrizan en el proyecto como reviewers | A2-F01 |
| 8 | Rev B | Observación anclada en §3 de v2 | estado `open`; email al editor | D3-F01 |
| 9 | Editor | Sube `contrato_v3.pdf` "atiende observación" | job done; observación re-anclada a §3 | C2-F01, D3-A03 |
| 10 | Rev B | Marca la observación resuelta | `resolved` | D3-F02 |
| 11 | Editor | Solicita revisión de v3 seleccionando A y B | bandejas de A y B pobladas | D1-F01 |
| 12 | Rev A / Rev B | A sella {1,2}; B sella {3,7} | panel: 2 sellos colocados | D4-F01 |
| 13 | Editor | Sube `contrato_v4.pdf` (solo §3 cambia) | espera `notify`: mailpit contiene email SOLO para B | C2-F01→D5-F01 |
| 14 | Rev B | Abre bandeja | re-review acotada a §3 | D5-F01 |
| 15 | Rev A | Abre bandeja y panel v4 | bandeja vacía; su sello `preserved` con constancia (origen v3); `assertNoEmailFor(A)` | D5-F01 |
| 16 | Editor | Exporta la constancia | descarga PDF (`%PDF`, filename con serial) | E4-F01 |

Requiere fixtures nuevas (H04): `contrato_v3.pdf` (v2 + §3 gana la frase de notificación
previa — SOLO §3 modified) y `contrato_v4.pdf` (v3 + §3 "cinco días"→"diez días" — SOLO §3
modified ⇒ B invalidado, A preservado). Funciones generadoras independientes; bytes de v1/v2
INTACTOS (DP-A9); README de testdata gana las tablas v2→v3 y v3→v4.

Anti-flake: correos únicos por corrida, purga de mailpit al inicio, positivo-antes-de-negativo
(paso 13 confirma ANTES de asertar el paso 15 negativo), esperas solo por estado visible/poll
de job en UI, retries 2 en CI. **Criterio de misión cumplida: M1 verde dos corridas seguidas.**

## 7.bis Módulo P · Superficie pública y freemium (It9) — añadido 2026-07-23

Superficies nacidas después del snapshot original de este mapa. Rutas públicas
(AllowAny): `/`, `/precios`, `/comparar[/:id]`, `/manual`, `/admin-login`.

### PC — Comparador público anónimo · P1 · It9
Rutas: `/comparar`, `/comparar/[id]` · Endpoints: `public/comparisons/` (POST/GET) ·
Estado: **Implementado**

| id | tipo | escenario | actor | crit |
|---|---|---|---|---|
| PC-F01 | F | Visitante sube dos PDF → ve la truth table y el CTA lo lleva a registro | guest | BLOQ |
| PC-F02 | F | Resultado compartible por enlace durante su TTL (24 h) | guest | ENR |
| PC-S01/S02 | S | Reuso puro del engine: `analyze_bytes(allow_ocr=False)` + `compare_snapshots` sin filas de tenencia | sistema | BLOQ |
| PC-E01..E08 | E | No-PDF (415) · sobre-tamaño (413) · protegido/corrupto (400) · exceso de páginas (422) · escaneado → upsell OCR (422) · throttle (429) · id inexistente (404) · resultado caducado (410) | guest | BLOQ |
| PC-P01..P03 | P | Endpoint AllowAny sin sesión ✓ · sin fugas de tenencia (cero filas Organization/Document) · limpieza de archivos efímeros | guest | BLOQ |

### PR — Precios públicos · P1 · It9
Ruta `/precios` · Endpoint `public/plans/` · Estado: **Implementado**

| id | tipo | escenario | actor | crit |
|---|---|---|---|---|
| PR-F01 | F | Tres tarjetas con precios COP y badge de prueba en Pro | guest | BLOQ |
| PR-F02 | F | Tabla comparativa con los límites honestos (1/20/∞ · 2/25/∞ · 30 días/∞) | guest | ENR |
| PR-F03 | F | CTAs: gratis y Pro → registro; Enterprise → contacto (sin checkout) | guest | BLOQ |
| PR-E01 | E | API caída → catálogo estático de respaldo, la página no se rompe | guest | ENR |

### TR — Prueba Pro de 14 días (clase `T`) · P2 · It9
Estado: **Implementado** (sin cobro en línea — Wompi diferido, F1-X01)

| id | tipo | escenario | actor | crit |
|---|---|---|---|---|
| F1-T01 | T | Alta nueva estrena trial Pro de 14 días (sin tarjeta) | owner | BLOQ |
| F1-T02 | T | Plan efectivo perezoso: override de consola > trial activo > gratis | sistema | BLOQ |
| F1-T03 | T | Override de consola gana sobre trial (activo o expirado) | sistema | BLOQ |
| F1-T04 | T | El trial levanta límites de proyectos/miembros/historial; al expirar vuelven | owner | BLOQ |
| F1-T05..T07 | T | Beat diario: expira, avisa a T-3 y al vencer, una sola vez (idempotente); no avisa a orgs con override | sistema | ENR |
| F2-T01 | T | El panel de uso publica el bloque de trial (on_trial, días restantes) | member | ENR |
| TRIAL-F01 | T | Banner global con días restantes, enlace a /precios y descarte por sesión | user | ENR |

### Anexo público adicional

| id | superficie | escenario | prueba |
|---|---|---|---|
| MAN-F01/F02 | `/manual` | Secciones renderizadas · búsqueda difusa encuentra un proceso | `e2e/public/manual.spec.ts` |
| ADM-F01/E01 | `/admin-login` | Handoff con tokens reales aterriza autenticado · sin tokens rebota a sign-in | `e2e/auth/admin-login.spec.ts` |
| HOME-* | `/` | CTA dual · secciones honestas · nav a precios · footer de producto | `e2e/public/smoke.spec.ts` |
| A11Y-01 | app | Cero violaciones críticas de axe en tablero/inbox/settings | `e2e/app/a11y.spec.ts` |
| NTF-F01..F04, NTF-A01, NTF-E01 | notificaciones | Catálogo, preferencias por canal, silenciables vs obligatorias | `notifications/tests/` |
| FD-01..FD-08 | infra (no-producto) | Fake data cumple reglas de negocio; delete respeta superusers y evidencia protegida | `accounts/tests/commands/` |

## 8. Anexo · Flujos heredados (auth/home) — estado actual

| ID | Flujo (flow-definitions) | Estado | Prueba |
|---|---|---|---|
| U1 | auth-sign-in-form | ✅ cubierto | `e2e/auth/auth.spec.ts` |
| U2 | auth-login-invalid | ✅ cubierto | ídem |
| U3 | Google login (parte de U1) | ⚠️ unit/integración; sin E2E real (OAuth externo) — aceptado | `test_auth_endpoints.py` |
| U4 | auth-sign-up-form | ✅ cubierto | `auth.spec.ts` |
| U5 | sesión/refresh/validate | ✅ unit+integración | `test_jwt_endpoints.py`, `http.test.ts` |
| U6 | auth-forgot-password-form | ✅ cubierto (forms) | `auth.spec.ts` |
| U7 | auth-admin-login-handoff | ✅ cerrado 2026-07-23 (guard + handoff real) | `e2e/auth/admin-login.spec.ts` |
| U8 | auth-sign-in-success (sesión real) | ✅ cerrado en It1 | `e2e/auth/session.spec.ts` |
| U9 | auth-sign-out | ✅ cerrado en It1 | `e2e/auth/session.spec.ts` |
| H1 | home-loads | ✅ cubierto | `smoke.spec.ts` |
| H2 | help-manual-browse | ✅ cerrado 2026-07-23 | `e2e/public/manual.spec.ts` |

## 9. Checklist de estados por pantalla (matriz obligatoria)

Celdas: `✓` cumple (con prueba en 04) · `—` falta · `n/a` no aplica · `It#` no existe aún
(obligatorio al implementarse). Columnas: **V**acío-con-guía · **C**argando · **E**rror+retry ·
**X** éxito-feedback · **2P** confirmación 2 pasos destructivas · **Pg** paginación ·
**B**úsqueda · **R**ol oculta/deshabilita · **D**ominio deshabilita (sellada/aprobada/locked/archivado).

| Pantalla (ruta) | V | C | E | X | 2P | Pg | B | R | D |
|---|---|---|---|---|---|---|---|---|---|
| Landing `/` | n/a | n/a | n/a | n/a | n/a | n/a | n/a | ✓ (CTA por sesión) | n/a |
| `/sign-in`, `/sign-up`, `/forgot-password` | n/a | ✓ | ✓ | ✓ | n/a | n/a | n/a | n/a | n/a |
| `/admin-login` | n/a | ✓ | — (token inválido sin pantalla clara) | ✓ | n/a | n/a | n/a | n/a | n/a |
| `/manual` | n/a | n/a | n/a | n/a | n/a | n/a | ✓ (fuzzy) | n/a | n/a |
| `/dashboard` (placeholder→muere en It1) | ✓ | n/a | n/a | n/a | n/a | n/a | n/a | ✓ | n/a |
| `/onboarding` | It6 | It6 | It6 | It6 | n/a | n/a | n/a | It6 | n/a |
| `/projects` (tablero) | It1 | It1 | It1 | It1 | n/a | It5 | It5 | It1 | It6 (archivados) |
| `/projects/new` | n/a | It1 | It1 | It1 | n/a | n/a | n/a | It1 | It7 (límite plan) |
| `/projects/[id]` (Documentos/Actividad/Equipo/Reportes) | It1 | It1 | It1 | It1 | n/a | It1 | It1 | It1 | It6 (archivado) |
| `/projects/[id]/settings` (+Peligro) | It5 | It5 | It5 | It5 | **It6** | n/a | n/a | It5 | It6 (sellos→solo archivar) |
| `.../documents/[docId]` (timeline) | It1 | It1 | It1 (job failed) | It1 | **It1** (borrar borrador) | It1 | n/a | It1 | It1/It3 (sellada/locked) |
| `.../versions/[versionId]` (visor+tabs) | It1 | It1 | It1 | It1 | n/a | n/a | It4 (filtros obs.) | It3/It4 | It3 (aprobada congelada) |
| `.../compare/[base]/[target]` | It2 ("sin cambios") | It2 | It2 | It2 | n/a | n/a | n/a | n/a | It2 (failed) |
| `/inbox` | It3 | It3 | It3 | It3 | n/a | It4 | n/a | It3 | n/a |
| `/org/settings` (General/Miembros/Plantillas/Plan) | It6 | It6 | It6 | It6 | It6 (revocar/remover) | It6 | It6 | It6 | It7 (límites) |
| `/settings` usuario (Perfil/Notifs/Seguridad/Prefs) | n/a | It1 | It1 | It1 | It6 (revocar sesiones) | n/a | n/a | n/a | n/a |
| `/org/trash` | It1 | It1 | It1 | It1 | **It1** (purga) | It1 | It1 | It1 (owner purga) | It1 (sellado jamás aparece) |
| `/org/audit` | It7 | It7 | It7 | It7 | n/a | It7 | It7 (filtros) | It7 (solo admin) | n/a |
| Centro de notificaciones (panel) | It3 | It3 | It3 | It3 | n/a | It4 | n/a | n/a | n/a |
| `/invite/[token]` | n/a | It6 | It6 (token inválido) | It6 | n/a | n/a | n/a | n/a | n/a |

Verificación sistemática: cada celda `✓` debe referenciar un test en `04-trazabilidad.md`
(RTL `[Pantalla-*]` o E2E). El helper `expectListStates()` + el tag `@states` se agregan en
It1 (H05/H06) y su uso es punto 10 del DoD.

## 10. Preguntas abiertas (DECISIÓN PENDIENTE)

1. **A3-X01** SSO corporativo: proveedor IdP + credenciales del operador.
2. **F1-X01** Wompi: llaves sandbox (misión posterior).
3. **D1-E02**: ¿segunda solicitud reemplaza a la abierta o 409? (mapeado como 409; objetar si
   se prefiere reemplazo).
4. **E4**: verificación online con QR (offline-only por ahora, T6).
5. **T12**: `version.downloaded` de terceros visible solo a admin (adoptado).
6. **D4-A02**: retirar sello — confirmado pre-aprobación only (DP-08).

## 10.bis Divergencias mapa ↔ código (auditadas 2026-07-23)

Escenarios donde el comportamiento real difiere de lo que este mapa asumía. El test
sigue al CÓDIGO (asevera lo que hace hoy) y la fila queda anotada aquí para decidir
después si se cambia el producto o el mapa.

| id | lo que el mapa asumía | lo que hace el código | veredicto |
|---|---|---|---|
| F2-P01 | editor 403 en el panel de uso | cualquier MIEMBRO ve el uso; el no-miembro recibe 404 (I12) | decisión It7 — actualizar el mapa, no el producto |
| A3-L01 | "cerrar todas las sesiones" incluye la actual | `revoke_other_sessions` conserva a propósito el refresh en curso | contrato real documentado; reabrir sólo si producto lo pide |
| D2-A01 | saltar desde un check rojo a su sección | `ChecksPanel` pinta la evidencia como texto inerte; ni enlace ni botón; `scrollToPage` sólo lo alimenta `ObservationsPanel` | **brecha de producto** (el dato `evidence.page/section` ya viaja) — pendiente |
| C2-L01 | "comparación deshabilitada **con explicación**" | CTA deshabilitado + `compare.pickTwo` genérico; no dice "este documento sólo tiene una versión" | media-brecha de copy — pendiente |
| D1-L01 | copy "estás al día" | `notifications.empty` = "No tienes notificaciones" | equivalente; alinear mapa o diccionario |
| A1-L01 | métrica de activación S1 (< 5 min) | analítica de producto, sin superficie testeable | **no-testeable**: sólo documento |
| A2-A02 | reenviar invitación pendiente (mismo token) | no existe endpoint ni servicio; el rodeo (revocar + reinvitar) acuña un token NUEVO, contradiciendo la fila | clase X: verificación negativa |
| A2-A04 | remover miembro ⇒ 404 en sus recursos | el 404 se cumple (I12) al desactivar la membresía, pero **no existe API de remoción**: `projects/{p}/members/` es GET-only (DELETE → 405) | clase X parcial: la invariante sí, la acción no |
| A1-E01 | siembra falla ⇒ error con reintento en el wizard | `onboarding_state` no tiene estado de fallo (`no_org|pending|done`) y la vista sólo atrapa `DomainError` ⇒ un fallo de MinIO/engine escapa como 500. El reintento funciona de facto (transacción atómica deja `pending`) pero sin representación explícita | **brecha de producto** — pendiente |
| D2-P01 | matriz de permisos de `progress/` | el endpoint no existe | clase X: verificación negativa |
| B2-L02 / C3-L01 | — | el tablero pinta el paginador siempre; la línea de tiempo lo oculta con una sola página | inconsistencia menor de UX — pendiente |
| D1-A01 | revisores auto-sugeridos por dueños de sección | `section_owners` sólo alimenta la matemática de aprobación (`seal_service`); `create_review_request` exige `reviewer_ids` y fija `scope='all'` | clase X: verificación negativa |
| E2-A01 | renombrar/eliminar comparación guardada (autor o admin) | eliminar existe; renombrar NO. Además el DELETE **no distingue autor** (cualquier editor/reviewer borra la de otro) y **borra todas** las filas guardadas de esa comparación | clase X parcial + **2 bugs de producto** — pendientes |
| D2-P01 | matriz 200/403/401/404 en `progress/` | ruta inexistente ⇒ la pata "anónimo 401" es inalcanzable; el sustituto real `versions/{v}/review_context/` se rige por rol de proyecto, no por asignación (no hay 403 de no-asignado en ningún punto) | clase X + regla sin punto de aplicación |
| B1-A01 | crear proyecto desde plantilla de org ⇒ config v1 con checks | el serializer sólo acepta name/description; la única vía es `config/apply_template/` (copy-on-apply ⇒ config v2) | clase X: verificación negativa |
| B4-A01 | purga anticipada del owner con 2ª confirmación + auditoría | no existe ruta de purga manual (el docstring de `trash_service` la promete); sólo `purge_expired` automática | clase X: verificación negativa |
| C3-A02 | historial por sección (blame) | no hay endpoint; `versions/{v}/sections/` no lleva procedencia. El dato SÍ existe (`SectionVersion.body_hash` difiere entre versiones) ⇒ brecha sólo de API | clase X: verificación negativa |
| C2-L02 | el puntero aprobado no se mueve | correcto, pero `Document.approved_version` es **campo muerto**: nadie lo escribe en producción (la aprobación vive en `DocumentVersion.is_approved`) ⇒ la garantía es vacua hoy | **bug latente** — el test fija el puntero en Arrange para que la aserción muerda cuando se cablee |
| D5-L01 | pérdida total de secciones ⇒ todo sello invalidado **+ coordinador forzado + versión no sellable** | invalidación total ✅ (I7 intacto, cero `preserved`). PERO: (a) `persist_analysis` nunca persiste `degraded`, así que la regla DP-09 de forzar coordinador no dispara y el plan se resuelve en auto; (b) no existe guarda de "rojo estructural": una versión sin secciones sigue siendo sellable | ✅ lo crítico + **2 requisitos incumplidos** — pendientes |

## 11. Procedimiento de alta de escenario

Todo PR que agregue comportamiento: (1) fila nueva aquí con id de la gramática; (2) fila en
`04-trazabilidad.md`; (3) pruebas con el id en título/marker/tag — en ese orden. Un test sin
escenario es "prueba huérfana" (gate de cierre = 0).
