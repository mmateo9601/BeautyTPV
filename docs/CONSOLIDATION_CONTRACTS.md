# Contratos de consolidación funcional V1

Fecha: 14-11-2026. Base de consolidación: `5dc936a` (correcciones `7045b03`, referencia original `4ce821e`). Lecturas: AGENTS.md, PLAYBOOK.md, AUDITORIA_COMPLETA.md y petición maestra adjunta. Este contrato habilita trabajo por propietarios; no declara verificación de funciones nuevas.

## Inventario de carencias constatadas

| Prioridad | Carencia | Evidencia base | Corrección contratada |
|---|---|---|---|
| ALTO | Datos comerciales y ajustes incompletos | core/models.py y forms.py solo identidad fiscal, zona, series y quicksale | Ajustes categorizados, contacto, dirección comercial, logo y preferencias |
| ALTO | Catálogo sin orden/visibilidad de categorías | Category solo name; CatalogItem sin sort_order | Ordenación y visibilidad TPV separada del historial |
| ALTO | Puestos sin orden explícito | Station ordering por code | sort_order editable, active ya existente |
| ALTO | Cajas sin gestión propia | CashRegister solo name; cash/views.py solo sesiones | Alta/edición/lista/desactivación/terminal; restricciones con sesión abierta |
| ALTO | Incidencias sin registro operativo | support/models.py sin Incident | Registro, clasificación, actuaciones y resolución auditados |
| ALTO | Revocación explícita no disponible | auth_version cambia con credenciales/rol, sin acción dedicada | Servicio accounts + acción POST jerárquica |
| MEDIO | Feedback/navegación administrativa desigual | formularios devuelven redirects sin mensajes; algunas listas sin filtros | Revisión de controles, empty states, mensajes y responsive |
| ALTO | Matrices maestras nuevas inexistentes | docs no contiene los siete entregables exigidos | Matrices con rutas/servicios/pruebas concretas; cierre independiente QA |

No se califican aquí defectos fiscales críticos sin reproducirlos. Las 697 pruebas previas son evidencia histórica, no prueba de las mejoras contratadas.

## Propiedad exclusiva de archivos

| Agente | Propiedad de escritura | Consumo / restricciones |
|---|---|---|
| architect | Este documento | Ningún módulo productivo |
| backend | apps/core, apps/catalog, apps/layout, apps/cash, apps/pos; pruebas nuevas test_consolidation_backend.py | Terminal también pertenece a core: hardware/devops no lo modifican. Comunicar campos/rutas/contextos antes de consumidores |
| frontend | templates, static; pruebas nuevas e2e/test_consolidation_ui.py | Propiedad exclusiva de todas las plantillas/static, incluidas las nuevas; backend comunica contexto sin crear plantillas. No modificar Python ni migraciones de backend. Implementar con interfaces acordadas; no perder formularios viejos válidos |
| security | apps/accounts; pruebas test_consolidation_security.py | Implementar revoke_user_sessions. Devops conecta team endpoint en support; security no modifica support |
| fiscal | apps/billing, apps/verifactu; pruebas test_consolidation_fiscal.py | Solo ampliar snapshots futuros/validaciones necesarias; no editar core ni documentos emitidos |
| hardware | apps/hardware; pruebas test_consolidation_hardware.py | Consume Terminal/core, no modifica esos modelos ni plantillas. Entregar necesidades UI a frontend |
| devops | apps/support y scripts operativos; pruebas test_consolidation_ops.py | Incluye integrar revoke_user_sessions en funciones de equipo y PrinterForm con cut_paper/drawer_enabled. Incidencias en módulos nuevos aislados; comunicar contexto UI |
| qa | Pruebas nuevas independientes test_consolidation_acceptance.py, matrices QA | No alterar aserciones existentes para ocultar fallos; verifica controles reales y DB |
| coordinador | config, integración secuencial y documentación global | Integra contratos cruzados, matriz de rutas y gate final; no escribir mientras propietario modifica el mismo archivo |

Los nombres de pruebas son propiedad reservada, no promesa de existencia. Cambios de contrato se comunican antes de implementarlos. El principal conserva ownership final tras entrega del agente.

## Ajustes de empresa, branding y TPV

Mantener `name`, `tax_id`, `address`, `installation_number`, las series y sus significados actuales. Añadir datos sin renombrar/destruir columnas previas:

- `trade_name`, `commercial_address`, `phone`, `email`, `ticket_footer`: campos comerciales opcionales acotados; no sustituyen identidad fiscal.
- EUR fijo: validar `currency == EUR` también en servicio/modelo, no solo ocultar el campo.
- `logo_data`: BinaryField de PNG canónico validado; nunca SVG/HTML, URLs remotas ni nombres de fichero. Límite de subida 2 MiB, píxeles decodificados limitados, normalización con Pillow a miniatura máxima 600×600, bytes finales máximo 256 KiB. Formulario de subida separado y eliminación explícita del logo; endpoint `core:logo` protegido devuelve solo PNG con nosniff. Al persistir en SQLite queda incluido en backup consistente. El agente puede ajustar formato/nombre comunicándolo antes de frontend/fiscal.
- Preferencias visuales mediante opciones cerradas, sin CSS/HTML libre. `theme` con opciones contrastadas y `floor_density` comfortable/compact son suficientes. Estados siguen siendo OPEN/PAYMENT_PENDING/CLOSED/CANCELLED reales; personalizar etiqueta/color permitido solo si se conserva indicador textual accesible y contraste.
- El plano continúa siendo el inicio obligatorio. Configuración de pantalla inicial significa sección/filtro o densidad inicial, no redirección arbitraria ni URLs proporcionadas por usuario. `default_section` nullable FK Section PROTECT/SET_NULL según política documentada; no genera cuenta ni venta automáticamente.
- Terminales pueden tener preferencias operativas concretas (sección inicial y/o caja predeterminada) mediante FK nullable y validación de actividad. Preferencias no son autorizaciones; jamás permiten acceder a caja/terminal desactivada.

Pantalla `core:settings` se conserva para compatibilidad. Dividir con navegación en categorías comercial/fiscal/TPV, por parámetro cerrado `section` o rutas nuevas nombradas; formularios guardan exclusivamente sus campos. El formulario legacy completo de tests existentes debe seguir siendo válido hasta adaptar consumidores expresamente. Todas las mutaciones ADMIN elevado, autorización adicional de Superadmin cuando corresponda y servicio reutilizable que recargue actor con require_role.

**Identidad fiscal:** tras primera Invoice se rechaza cambiar NIF o installation_number; no reasignar una instalación a otro obligado. Nombre fiscal/domicilio/series solo afectan a nuevas emisiones. No actualizar snapshots, FiscalRecord, huellas ni trabajos previamente emitidos. Registrar cambios sin PII en metadatos de auditoría. No retirar production_guard.

## Catálogo, plano y cajas

- Category añade `sort_order` entero no negativo y `visible_in_pos` booleano, por defecto 0/true; CatalogItem añade `sort_order` 0. Orden estable sort_order/name/pk. Ocultar categoría excluye sus artículos del catálogo ofrecido en TPV, incluyendo búsqueda y adición directa por POST/servicio; no borra líneas ya añadidas ni altera historial. Artículos sin categoría permanecen visibles si activos. Edición administrativa conserva acceso a todo el catálogo.
- Station añade `sort_order` 0, orden por sección/sort_order/code/pk. No desactivar ni reasignar un puesto con cuenta activa sin operación explícita válida; no crear editor gráfico.
- CashRegister añade `active` true y `terminal` FK core.Terminal nullable PROTECT. Crear/editar/desactivar requiere ADMIN elevado en HTTP y require_role ADMIN en servicios. Se conserva apertura EMPLOYEE de la implementación existente: la nueva petición enumera esta capacidad para Encargado pero no la prohíbe expresamente al Empleado, y exige no eliminar funcionalidades. Cierre/movimientos siguen MANAGER. No cambiar terminal ni desactivar con turno abierto. No borrar caja con historial; preferir desactivación. Registro sin terminal es caja compartida del servidor; asignación no elimina permisos ni obliga a que un terminal tenga caja.
- Sesiones históricas, movimientos y cobros permanecen inmutables. El selector de apertura y checkout solo ofrece cajas activas, validación también por servicio con datos actuales.
- Rutas nuevas propuestas `cash:registers` y `cash:register_edit`, nombre final comunicado a frontend. Listas incluyen q/estado cuando pertinente y acciones accesibles. No CRUD sobre sesiones cerradas.

## Revocación explícita de sesiones

Servicio `apps.accounts.services.revoke_user_sessions(actor, target)` transaccional: recargar actor/target; usar authorize_user_change; incrementar auth_version; revocar SupportSession donde target sea actor o aprobador; registrar user.sessions_revoked; devolver usuario actualizado. No permitir que Admin opere sobre igual/superior. Superadmin puede revocar a otro Superadmin. No cambiar PIN/password ni guardar listas de cookies. Definir explícitamente si permite autorrevocación: si sí, termina la propia sesión y exige acceso posterior.

Devops conecta acción POST `team:revoke_sessions` en support, elevación ADMIN, CSRF y mensajes. Servicio sin request verifica rango/actividad vigentes; elevación pertenece a frontera HTTP igual que servicios existentes. Probar cliente previamente autenticado, denegación backend, target promovido después de cargar objeto, concesión revocada y no resurrección.

## Incidencias y actuaciones

Devops añade `Incident` en support con título acotado, categoría OPERATIONAL/HARDWARE/FISCAL/SYSTEM, severidad LOW/MEDIUM/HIGH/CRITICAL, estado OPEN/IN_PROGRESS/RESOLVED, created_by/created_at/updated_at/resolved_at; descripción acotada y responsable nullable si aporta valor real. `IncidentAction` append-only enlaza incidente/actor/fecha/nota/estado anterior/nuevo. No asociar clientes ni copiar XML/secretos/tarjetas. La UI explica no incluir datos personales o credenciales; auditoría solo IDs/transición, no contenido libre.

Vista operativa mínimo MANAGER; ADMIN hereda y SUPERADMIN necesita elevación y TECHNICAL. El scope no concede PII. Crear/listar/consultar/filtrar categoría/estado/severidad, añadir actuación, transiciones OPEN→IN_PROGRESS/RESOLVED, IN_PROGRESS→RESOLVED y reapertura RESOLVED→OPEN con motivo. Resolución exige nota. No eliminación de actuaciones ni borrado de incidente con historial; conservación auditada. Comparación condicional de estado/version previene pérdida de actuaciones concurrentes.

Rutas propuestas `support:incidents`, `support:incident_detail`; servicios en `support/incidents.py` que requieren rol actual. Navegación principal para MANAGER+ y soporte; acceso no implica acceso a otras funciones técnicas. Si se necesitan rutas fuera de `/soporte/` para no aplicar guard global SUPERADMIN, usar include dedicado, conservando names estables y verificación de middleware.

## Snapshots y dispositivos

Fiscal puede incluir los nuevos campos comerciales en `Invoice.issuer` exclusivamente al emitir; thermal/PDF consume ese snapshot, nunca CompanySettings mutable para documentos existentes. Sin logo previo en factura histórica no inventar uno al reimprimir. Texto libre se escapa en HTML y se sanea antes de ESC/POS. Datos legales/QR y guard fiscal permanecen obligatorios e independientes de branding.

Hardware añade Printer.cut_paper=True y drawer_enabled=True; devops los expone en PrinterForm. render_receipt/render_test aceptan cut_paper y enqueue_invoice respeta drawer_enabled conservando guard CASH/copia. Routing por terminal ya existe. Configuración cambia trabajos futuros, jamás muta intención de PrintJob; bloquear cambios de destino con trabajo SENDING. Sin prueba física, conservar BLOQUEADO EXTERNO.

## Gates de implementación y cierre

1. Cada propietario entrega rutas/contextos/servicios/migraciones, pruebas positivas y negativas y limitaciones. No se considera completa una ruta sin enlace o un formulario sin persistencia.
2. Backend integra consumidores pos y frontend templates; principal integra config después de contratos definitivos. QA contrasta requisitos con operaciones independientes del autor y actualiza políticas de cada ruta con PK reales.
3. Ejecutar check, migrate, drift, Ruff, pytest completo, Chromium escritorio/tablet/estrecho, upgrade de BD con datos emitidos, instalación/backup/restore/update. Conservar pruebas anteriores salvo cambio de política expresamente documentado y más cobertura equivalente.
4. Crear FUNCTIONAL_COVERAGE, ROLE_PERMISSION_MATRIX, CRUD_COVERAGE, SETTINGS_COVERAGE, SUPERADMIN_COVERAGE, UI_REVIEW y FINAL_ACCEPTANCE con requisito/estado/archivo/ruta-servicio/prueba/evidencia/límites. No deducir COMPLETO del número de tests.
5. Commit por módulo/gate verificado; no incluir secretos/datos de negocio. AEAT certificado/acuses, impresión/cajón físicos, destino TLS/LAN y aceptación humana siguen BLOQUEADO EXTERNO hasta evidencia real.
