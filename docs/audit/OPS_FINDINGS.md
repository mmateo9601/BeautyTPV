# Auditoría operativa contra 4ce821e

Revisión y correcciones locales. No acredita hardware real, remisión AEAT ni despliegue TLS en un centro.

| Hallazgo | Corrección | Evidencia |
|---|---|---|
| P1: escritura de archivos de actualización anterior al bloque de rollback podía dejar código parcial | Staging completo, preflight de todos los destinos, reemplazos atómicos y rollback de cualquier fallo de IO o migración; base de datos conservada | test_partial_file_write_rolls_back_all_code; test_preflight_invalid_destination_never_writes_first_file |
| P1: un paquete no comprobaba compatibilidad de dependencias | Validación de lock con versiones exactas y pip check antes de backup/escrituras; entorno incompatible aborta sin mutaciones | test_dependency_mismatch_aborts_before_code_and_backup |
| Rutas duplicadas/casefold, versión insegura y archivo ZIP mutable | Rechazo de duplicados/collisions y versión no segura; snapshot en memoria y hash antes de preparar archivos | test_update_rejects_case_collision_and_unsafe_version |
| Versión de salud y backup hardcode | application_version lee release.json aplicado, metadata como fallback; update conserva/revierte release.json junto al código | test_release_version_changes_only_after_successful_update |
| P1: servidor seguía activo aunque murieran workers obligatorios | Supervisor con heartbeat por PID/estado y cierre del servidor al perder worker o monitor | test_supervisor_closes_service_when_child_exits; test_supervisor_reports_monitor_failure; prueba real descrita abajo |
| Error fiscal podía impedir las copias programadas; política permitía cero | Tareas fiscal/backup aisladas, estado DEGRADED, validadores positivos y conservación de la copia más reciente | test_fiscal_failure_does_not_prevent_backup_task; test_invalid_backup_policy_rejected |
| Faltaba gestión de terminales/tokens y desbloqueo PIN independiente del cambio | CRUD con token hash, permisos jerárquicos, desbloqueo auditado de usuario y, con TECHNICAL Superadmin, origen | test_terminal_form_hashes_token_and_never_saves_raw_token; test_unlock_user_does_not_require_pin_change |
| Ajustes de dispositivo aceptaban codificación/puertos inválidos | Validación de codificación, puerto TCP, velocidad serie, USB, simulador y asociación terminal | test_printer_form_rejects_unrenderable_encoding_and_invalid_port |
| Configuración fiscal técnica no tenía referencias configurables protegidas | Formulario de rutas absolutas externas, validación PEM/caducidad/correspondencia de clave, sin bytes de clave en BD; modo sincronizado sin abrir productionguard | test_certificate_external_references_validate_key_match; test_certificate_must_be_outside_repo |
| Aprobación temporal podía sobrevivir a la baja de aprobador | Consumo exige actor activo Superadmin y aprobador activo ADMIN/SUPERADMIN | test_revoked_approver_invalidates_support_session |

## Verificación

`pytest tests/test_audit_ops.py tests/test_backup.py -q`: 28 passed, 5.93 s. Ruff propio limpio. Migración support0002 aplicada, incorpora referencias externas, heartbeat y validadores. La prueba previa de soporte fue actualizada para volver a autenticar tras cambio de rol, conforme a revocación de sesiones nueva.

Smoke real en instancia temporal nueva: instalador --skip-dependencies --no-user EXIT0; servicio por loopback devuelve HTTP200 en acceso; heartbeats RUNNING para service/hardware_worker/operations_worker. Se detuvo únicamente el PID hardware_worker de esa instancia de prueba: el servidor cerró con EXIT1 y terminó sus workers restantes. La primera ejecución dentro del sandbox falló por permiso WinError10013 al abrir el socket interno de Waitress; repetición autorizada fuera de sandbox completó la prueba. No se ha alterado una instalación comercial.

## Límites explícitos

- El updater no modifica pip/venv ni promete rollback de dependencias. Si el lock no está satisfecho se rechaza antes de modificar la instalación; el productor debe proporcionar/provisionar un entorno compatible y probarlo. Un fallo después de migrar conserva BD y retiene la operativa; no es rollback de datos fiscales.
- La referencia de clave PEM debe estar protegida por permisos del SO; el formulario no valida el propietario ni ACL de todos los sistemas operativos. No se guarda el contenido en BD ni se exporta en diagnósticos.
- Terminal/bridge, certificado y política se prueban como software; falta hardware físico, certificado autorizado y revisión experta para producción.
- Arranque automático, TLS, custodia externa de backups y recuperación con acuses AEAT reales siguen dependiendo del equipo y de evidencias externas.
