# Operaciones reales de Superadmin

Fecha: 14-11-2026. Base: `5dc936a`; requisitos: [peticion de consolidacion](consolidation/REQUEST.md). Resultado definitivo en [FINAL_ACCEPTANCE.md](FINAL_ACCEPTANCE.md). Archivos sin prefijo se refieren a apps/, salvo config/templates/static/scripts. Pruebas en tests/ y tests/e2e/.

Estados: COMPLETO LOCAL (implementado y prueba aprobada en el escenario indicado), PARCIAL, PENDIENTE, BLOQUEADO EXTERNO. No se confunde simulacion con validacion AEAT o fisica.

| Requisito | Estado | Implementacion | Ruta o servicio | Prueba / evidencia | Observaciones / bloqueo |
|---|---|---|---|---|---|
| Salud/version/Python/Django/dependencias/SQLite/disco/migraciones | COMPLETO LOCAL | support/services.py; config/views.py | support:index; diagnostics; health | test_consolidation_ops.py; test_audit_configuration.py | Datos reales sin PII; no metricas inventadas |
| Estado servicios/workers/latencias | COMPLETO LOCAL | support/services.py; scripts/service.py | diagnostics; operations_worker | test_audit_ops.py; evidence previo | STALE medido; mata web si worker requerido muere |
| Usuarios crear/editar/activar/desactivar/Superadmins | COMPLETO LOCAL | accounts/services.py; support/views.py | team:index/edit | test_security.py; test_audit_matrix.py | Elevado; Admin solo inferiores |
| Desbloquear/reset credenciales/revocar sesiones | COMPLETO LOCAL | accounts/services.py; support/views.py | team:unlock/revoke_sessions | test_consolidation_security.py; test_consolidation_acceptance.py | Auditoria, sin mostrar PIN/hash |
| Auditoria y autorizaciones temporales | COMPLETO LOCAL | audit/views.py; support/services.py | audit:index; support:authorize/revoke | test_audit_security.py; test_audit_matrix.py | PII otro Admin; scope y expiracion |
| Terminales y preferencias | COMPLETO LOCAL | core/models.py; support/views.py | support:terminals/terminal_edit | test_consolidation_ops.py; test_audit_acceptance.py | Token hash; sin cookie machine auth |
| Impresoras/driver/asignacion/pruebas | COMPLETO LOCAL | hardware/services.py; support/views.py | support:printer_save; hardware:test | test_consolidation_hardware.py; test_audit_acceptance.py | TECHNICAL/elevado; sin dispositivo fisico |
| Colas impresion/errores/recuperacion | COMPLETO LOCAL | hardware/services.py; support/views.py | support:index; hardware:retry | test_audit_hardware.py | UNKNOWN requiere copia sin cajon, no reenviar bytes |
| Fiscal/certificado/caducidad/diagnostico | COMPLETO LOCAL | support/fiscal.py; forms.py; views.py | support:fiscal_settings/diagnostic | test_audit_ops.py; test_audit_acceptance.py | Sin clave en DB; conexion TCP no envio |
| Fiscal cola/reintento/subsanacion/anulacion | COMPLETO LOCAL | verifactu/services.py; support/views.py | support:recover_fiscal/correct_fiscal/annul_fiscal | test_audit_fiscal.py; test_audit_matrix.py | Anular registro no devuelve venta; produccion bloqueada |
| Backup generar/verificar/descargar/historial/politica | COMPLETO LOCAL | support/operations.py; views.py | support:backup/backup_download/settings | test_backup.py; test_audit_acceptance.py | Scope BACKUP; cifrado; key externa |
| Restore asistido fuera DB activa | COMPLETO LOCAL | support/views.py; scripts/restore.py | support:restore_advisor; restore.py --offline | test_audit_acceptance.py; upgrade JSON | Confirmacion, mantenimiento, lock, hold y conciliacion |
| Version/paquete/preflight/update/rollback | COMPLETO LOCAL | support/updates.py; views.py; scripts/update.py | support:updates; update.py --offline | test_audit_ops.py; test_backup.py | Canal verificado local; sin consola arbitraria |
| Logs y export saneados | COMPLETO LOCAL | support/views.py; services.py | support:logs; diagnostics_export | test_audit_ops.py; test_audit_matrix.py | No secretos ni datos personales innecesarios |
| Incidencias/actuacion/clasificacion/resolucion | COMPLETO LOCAL | support/incidents.py; views.py | support:incidents; incident_detail | test_consolidation_ops.py; test_consolidation_acceptance.py | TECHNICAL, nota sin PII; registro de actuaciones |
| Finalizar soporte/revocar autorizacion | COMPLETO LOCAL | support/views.py | support:revoke; team:revoke_sessions | test_audit_forms.py; test_consolidation_security.py | Revocacion auditada y caducidad real |

## Validaciones externas separadas

| Requisito | Estado | Implementación / ruta | Evidencia | Cómo resolver el bloqueo |
|---|---|---|---|---|
| AEAT oficial, certificado, acuses y conformidad | BLOQUEADO EXTERNO | verifactu SOAP/outbox; production_guard | Tests locales/XSD; no remisión | Certificado autorizado, pruebas oficiales, conciliación y declaración responsable suscrita |
| Impresora, papel80mm, QR y cajón reales | BLOQUEADO EXTERNO | hardware bridge/driver/spool | Simulador/TCP/API de prueba | Facilitar modelo/firmware y ejecutar checklist físico HARDWARE.md |
| Equipo/LAN/autoarranque/TLS y usuarios del salón | BLOQUEADO EXTERNO | scripts servicio/agente/runbooks | Copias temporales y loopback | Instalar en destino, comprobar CA/firewall/backup y aceptación con operadores reales |

Detalles e instrucciones precisas: [FINAL_ACCEPTANCE.md](FINAL_ACCEPTANCE.md). No retirar el guard fiscal a partir de pruebas locales.

Indice de pruebas concretas: [TEST_INDEX](consolidation/TEST_INDEX.md). Inventario archivo/linea/ruta/modelo/plantilla: [INVENTARIO](consolidation/inventory/INVENTARIO.md).
