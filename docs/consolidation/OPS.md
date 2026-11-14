# Consolidación operativa de soporte

Base `5dc936a`. Propiedad: `apps/support/`, `tests/test_consolidation_ops.py`; todas las plantillas pertenecen a frontend. No se modificaron scripts ni cuentas ni hardware ajenos. Los contratos transversales se comunicaron antes de consumirlos.

| Requisito | Estado local | Implementación / ruta | Evidencia |
|---|---|---|---|
| Incidencias operativas | COMPLETO | `support/incidents.py`, `support:incidents` | Creación/listado/búsqueda/filtros HTTP y persistencia en test_consolidation_ops |
| Consulta y actuaciones | COMPLETO | `support:incident_detail`, `add_action` | Resolución y reapertura con motivo, clasificación, versionado condicional, rechazo de formulario obsoleto |
| Historial conservado | COMPLETO SQLite | IncidentAction sin update/delete ORM; migración support0004 SQL update/delete/REPLACE | Intentos SQL y ORM bloqueados; descripción original de Incident no se reescribe |
| Roles incidencias | COMPLETO | Manager/Admin solo OPERATIONAL; categorías técnicas SA con TECHNICAL y elevación HTTP | Denegación de Empleado, ocultación técnica, rechazo backend y scope caducado/revocado |
| Minimización | COMPLETO en validación indicada | Texto acotado y plano, rechazo de controles/XML/email/DNI/PAN probable/secretos etiquetados; sin FK Cliente | Tests parametrizados; auditoría solo referencia/estado, sin copiar notas |
| Revocar sesiones | COMPLETO | `team:revoke_sessions`, POST confirmado REVOCAR SESIONES; servicio accounts ajeno | Cliente antiguo deja de acceder, PIN intacto; autorización jerárquica y CSRF existentes |
| Terminales configurables | COMPLETO | TerminalForm con default_section/default_register; `save_terminal` | Scope técnico, full_clean, búsqueda q/active y guardado auditado; modelo core pertenece a backend |
| Preferencias impresora | COMPLETO | PrinterForm cut_paper/drawer_enabled; `hardware.services.save_printer` | Frontera HTTP elevada+TECH y servicio especializado; hardware prueba bytes/snapshot |
| Usuarios listados | COMPLETO | users q/state/role; UserUpdateForm first_name | Listado filtrado conserva restricción de rango; nombre editable usa API accounts del principal |
| Colas/dispositivos filtrables | COMPLETO | soporte q/print_status/fiscal_status | Choices cerradas, consultas reales sin cambiar estados por GET |
| Verificar copia independiente | COMPLETO | `support:backup_verify`, POST con BACKUP | Archivo real cifrado/hash/manifest, corrupción produce fallo auditado y no activa mantenimiento |
| Diagnóstico versiones reales | COMPLETO | `support.services.diagnostics` | Python/Django y versiones de once dependencias consultadas con importlib.metadata; ausencia explícita |
| Política técnica | COMPLETO | `save_technical_settings` | TECHNICAL actual, validación completa y auditoría, sin consola arbitraria |

La validación de texto reduce patrones frecuentes; no demuestra que un operador no pueda escribir información personal no detectable en lenguaje natural. La interfaz exige descripción sin datos personales, no copiar logs ni certificados. Los textos se escapan en plantillas y no se añaden a los metadatos de auditoría.

Las incidencias no constituyen una vía para editar facturas, cobros o registros fiscales. Una incidencia fiscal describe un problema técnico; su resolución no cambia ni atribuye acuse AEAT. No hay eliminación de actuaciones ni cierre ficticio de colas.

## Verificaciones

- `pytest tests/test_consolidation_ops.py tests/test_audit_ops.py -q`: **31 PASS** (16 nuevos, 15 anteriores), 5,47 s.
- Regresion adicional `pytest tests/test_backup.py tests/test_security.py tests/test_audit_security.py tests/test_audit_forms.py -q`: **131 PASS**, 24,54 s. Migraciones support sin drift.
- Ruff check/format sobre support y nuevas pruebas: limpio, 25 archivos.
- Primer ensayo: dos errores de compilación del include de formularios durante edición frontend y una fixture de backup sin tabla django_migrations. Se comunicó el include al propietario y se completó la fixture; se repitió el conjunto completo con 31 PASS, sin suprimir assertions.
- El coordinador ejecuta suite integrada/Chromium/migraciones de toda la aplicación para el gate final. No se atribuye a este módulo un resultado aún no ejecutado.

## Bloqueos externos

AEAT/certificado y firma responsable, impresora/cajón/QR físicos, equipo destino/LAN/TLS y aceptación humana siguen BLOQUEADO EXTERNO. Los tests usan SQLite y archivos cifrados reales con datos sintéticos, no equipos o acuses oficiales.
