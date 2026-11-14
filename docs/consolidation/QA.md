# QA independiente de consolidación V1

Fecha: 14-11-2026. Base funcional de entrada: `5dc936a`. Propiedad QA: `tests/test_consolidation_acceptance.py`, ampliación de `tests/test_audit_matrix.py` y este documento. No se modificaron aplicaciones, plantillas ni pruebas de los otros especialistas.

## Evidencias y resultado

`python -m pytest -q tests/test_consolidation_acceptance.py tests/test_audit_matrix.py --junitxml=docs/evidence/consolidation-qa-tests.xml -o junit_family=xunit1`: **484 PASS, 40,75 s**. El XML contiene 20 casos de aceptación independientes y 464 casos de la matriz transversal; cero fallos/errores/omisiones.

Después se añadió `test_superadmin_operational_inheritance_does_not_bypass_incident_support_controls`: **1 PASS, 2,50 s** en ejecución específica. El JUnit anterior no incluye este caso adicional; la suite final del coordinador deberá incluir los 21 casos de aceptación nuevos. Ruff check y format de ambos archivos QA pasan.

La matriz mantiene todas las aserciones anteriores y añade políticas para nueve rutas: logo/guardar logo, configuración/alta/edición de cajas, lista/detalle de incidencias, verificación de backup y revocación de sesiones. Se usan registros reales, incluido un logo PNG válido y una incidencia operativa, para evitar confundir permiso con ausencia de objeto. Comprueba anónimo y los cuatro roles, elevación administrativa, scopes PII, CSRF y cada enlace visible del menú.

Un POST inválido en esta matriz solo prueba autorización y manejo de errores, no éxito del negocio. Los casos independientes de aceptación y las pruebas de formularios/navegador son la evidencia de persistencia y comportamiento positivo.

## Defectos encontrados por QA y correcciones verificadas

| Prioridad | Reproducción independiente | Archivo corregido por propietario | Evidencia posterior |
|---|---|---|---|
| ALTO | Una categoría oculta seguía admitiendo artículos mediante servicio y POST directo; la UI no era una barrera suficiente | `apps/pos/services.py`, backend recarga artículo/categoría y rechaza categoría no visible | `test_hidden_category_cannot_be_added_by_direct_post_or_stale_item`, PASS; no cambia la cuenta |
| MEDIO | `save_register` aceptaba un objeto Terminal cacheado como activo tras su desactivación en otra operación | `apps/cash/services.py`, backend recarga terminal por PK; reforzó también la validación de caja predeterminada de Terminal | `test_register_service_checks_terminal_activity_from_database`, PASS; no crea caja inválida |
| Integración | Include de formulario en edición produjo `TemplateSyntaxError` y GET500 en páginas de acceso/configuración | `templates/includes/form.html`, frontend reescribe bloque anidado y compila plantillas | Matriz final de 464 casos PASS; no se quitaron aserciones de GET200 |
| Integración | Ruta `support:backup_verify` se añadió mientras la primera ejecución ya tenía las políticas cargadas | `tests/test_audit_matrix.py`, QA añade política SA/POST/backup real | Matriz final PASS, incluida denegación CSRF y cuatro roles |

Los fallos anteriores se notificaron a los propietarios y se repitieron. No se ocultaron mediante `skip`, `xfail` ni reducción de permisos/aserciones. Son resultados de la construcción e integración actual; no se atribuyen automáticamente al commit original.

## Matriz de comprobaciones independientes

| Requisito | Estado local | Implementación/ruta o servicio | Prueba QA | Observación |
|---|---|---|---|---|
| Logo rechaza SVG/HTML, contenido corrupto y tamaño excesivo; fallo atómico | VERIFICADO | `core.services.save_company_settings` / `canonical_logo` | `test_logo_rejects_active_malformed_and_oversize_content_atomically` (4 casos) | Cambios comerciales acompañantes tampoco se persisten al fallar |
| Logo raster canónico, tamaño acotado y respuesta privada PNG/nosniff | VERIFICADO | `core:logo`, `core:logo_save` | `test_valid_logo_is_canonical_private_png_and_removal_is_audited` | Se decodifica PNG real, dimensión máxima 600; Empleado consulta, no modifica |
| Formulario comercial no permite modificar identidad/activar producción con campos extras | VERIFICADO | `core:settings?section=commercial` | `test_commercial_form_cannot_smuggle_fiscal_identity_or_production` | El cambio comercial persiste y NIF/instalación/modo permanecen intactos |
| Servicio de ajustes comprueba rol persistido y EUR | VERIFICADO | `core.services.save_company_settings` | `test_company_service_uses_persisted_role_and_rejects_unsupported_currency` | Objeto ADMIN cacheado no conserva privilegio tras degradación en DB |
| Ocultar categoría tiene efecto en servicio y POST | VERIFICADO | `pos:add_line`, `pos.services.add_line` | `test_hidden_category_cannot_be_added_by_direct_post_or_stale_item` | No depende de ocultar botones; líneas existentes se conservan |
| Caja/puesto no se desactivan ni reasignan con operación abierta | VERIFICADO | `cash.services.save_register`, `layout.services.save_station` | `test_register_and_station_configuration_cannot_invalidate_live_operations` | Sesión y línea de cuenta permanecen |
| APIs administrativas de categoría/artículo/sección/puesto/caja no autorizan Manager | VERIFICADO | Servicios `save_*` de catálogo/plano/caja | `test_administrative_entity_services_reject_manager_without_http` (5 casos) | Prueba directa sin petición web |
| Actividad actual de terminal gobierna asignación de caja | VERIFICADO | `cash.services.save_register` | `test_register_service_checks_terminal_activity_from_database` | Rechaza FK cacheada obsoleta |
| Incidencias limitan ámbito operativo/técnico y usan CAS | VERIFICADO | `support.incidents.create_incident/add_action/visible_incidents` | `test_incident_cannot_cross_operational_scope_or_overwrite_concurrent_action` | Rechaza clasificación técnica por Manager, acción obsoleta, conserva historial y permite reapertura con nota |
| Historial de actuaciones protegido incluso SQL directo | VERIFICADO | `support/migrations/0004_incident_history_guards.py` | `test_incident_action_history_is_guarded_even_in_raw_sql` (3 casos) | UPDATE/DELETE/REPLACE rechazados |
| Revocación HTTP invalida varios logins sin cambiar contraseña/PIN | VERIFICADO | `team:revoke_sessions`, `accounts.services.revoke_user_sessions` | `test_http_revocation_invalidates_all_existing_logins_without_changing_credentials` | Manager denegado, confirmación errónea no revoca, Admin autorizado revoca y audita |
| Herencia operativa de SA mantiene elevación y TECHNICAL | VERIFICADO específico | `support:incidents`, `support:incident_detail` | `test_superadmin_operational_inheritance_does_not_bypass_incident_support_controls` | SA denegado sin elevación o grant; Manager conserva acceso operativo |

## Límites y gate final

No se concede aprobación global de release a partir de esta suite parcial. El coordinador debe integrar la suite completa, Chromium, migraciones sobre datos previos, instalación/actualización/backup/restore y revisión visual final. Las evidencias E01–E16 anteriores se conservan y deberán repetirse dentro de la suite integral.

**BLOQUEADO EXTERNO:** certificado/autorización y remisión/acuse oficial AEAT, revisión normativa y declaración responsable suscrita, impresora/cajón/lectura QR físicos, equipo/LAN/TLS/autoarranque y aceptación con personas del salón. Un transporte simulado o TCP local no supera esos gates. Producción fiscal debe seguir cerrada.

Se conserva apertura de caja por Empleado ya autorizada en V1; cierre/arqueo/movimientos requieren Encargado. La petición de consolidación hereda capacidades y prohíbe eliminar funcionalidad existente; no se interpretó la lista de Encargado como una prohibición nueva de apertura para Empleado. La matriz final debe reflejar esta política explícitamente.
