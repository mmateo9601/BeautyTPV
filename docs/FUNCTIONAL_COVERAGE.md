# Cobertura funcional V1

Fecha: 14-11-2026. Base: `5dc936a`; requisitos: [peticion de consolidacion](consolidation/REQUEST.md). Resultado definitivo en [FINAL_ACCEPTANCE.md](FINAL_ACCEPTANCE.md). Archivos sin prefijo se refieren a apps/, salvo config/templates/static/scripts. Pruebas en tests/ y tests/e2e/.

Estados: COMPLETO LOCAL (implementado y prueba aprobada en el escenario indicado), PARCIAL, PENDIENTE, BLOQUEADO EXTERNO. No se confunde simulacion con validacion AEAT o fisica.

| Requisito | Estado | Implementacion | Ruta o servicio | Prueba / evidencia | Observaciones / bloqueo |
|---|---|---|---|---|---|
| Instalacion independiente, EUR y SQLite | COMPLETO LOCAL | core/models.py; config/settings.py | CompanySettings; manage.py migrate | test_audit_backend.py; test_consolidation_backend.py; upgrade JSON | Sin tenants; fichero local |
| Acceso PIN/password y jerarquia | COMPLETO LOCAL | accounts/permissions.py; services.py | /acceso/; /elevar/ | test_security.py; test_audit_security.py | PIN no eleva |
| Revocacion explicita y credenciales | COMPLETO LOCAL | accounts/services.py; support/views.py | revoke_user_sessions; team:revoke_sessions | test_consolidation_security.py; test_consolidation_acceptance.py | Admin solo inferiores; SA puede autorrevocar |
| Plano por secciones, estados y total | COMPLETO LOCAL | pos/views.py; templates/pos/floor.html | pos:floor; open_ticket | test_browser.py; test_audit_ui.py; test_consolidation_ui.py | Inicio obligatorio plano |
| Cuentas persistentes y estado en cobro | COMPLETO LOCAL | pos/services.py | prepare_payment; resume_ticket | test_concurrency.py; test_audit_backend.py | Una activa/puesto; sin edicion en cobro |
| Carrito, notas, cantidad, descuentos | COMPLETO LOCAL | pos/services.py; templates/pos/ticket.html | add_line; update_line; remove_line | test_backend.py; test_audit_forms.py; test_audit_ui.py | Reducir/quitar/descuento restringido Manager |
| Catalogo ordenado y categorias visibles | COMPLETO LOCAL | catalog/models.py; pos/services.py | catalog:index; pos:ticket; add_line | test_consolidation_backend.py; test_consolidation_acceptance.py | Ocultar impide tambien POST directo; conserva historial |
| Venta rapida opcional | COMPLETO LOCAL | core/models.py; pos/services.py | quick_ticket | test_audit_backend.py | Persistente por actor/terminal |
| Efectivo, cambio, tarjeta y mixto | COMPLETO LOCAL | pos/services.py; cash/services.py | checkout | test_acceptance.py; test_browser.py | Datáfono externo; sin integracion bancaria |
| Idempotencia y muerte proceso | COMPLETO LOCAL | pos/services.py; core/transactions.py | checkout | test_concurrency.py | Rollback factura/alta/spool antes commit |
| Gestion cajas y preferencias terminal | COMPLETO LOCAL | cash/models.py; services.py; core/models.py | cash:registers; save_register | test_consolidation_backend.py; test_consolidation_acceptance.py | No desactivar/reasignar con turno abierto |
| Caja/arqueo/movimientos/historial | COMPLETO LOCAL | cash/services.py | open_session; close_session; add_movement | test_audit_forms.py; test_acceptance.py | Apertura Employee conservada; cierre/movimiento Manager |
| Clientes y exportacion | COMPLETO LOCAL | customers/views.py; services.py | customers:index/detail/edit/delete | test_regressions.py; test_audit_forms.py; test_consolidation_customer_services.py | PII para SA; sin portal |
| Ajustes salon/TPV/fiscal separados | COMPLETO LOCAL | core/forms.py; services.py | core:settings; save_company_settings | test_consolidation_backend.py; test_consolidation_acceptance.py | Formulario solo guarda su categoria |
| Logo raster seguro | COMPLETO LOCAL | core/services.py; views.py | core:logo; core:logo_save | test_consolidation_acceptance.py | Reencode PNG; limite; logo comercial UI incluido backup DB |
| Datos ticket congelados | COMPLETO LOCAL | billing/services.py; hardware/escpos.py | issue_invoice; render_pdf; render_receipt | test_consolidation_documents.py | Nombre/contacto/pie futuros; no cambia documento emitido |
| F1/F2 y rectificativa total | COMPLETO LOCAL | billing/services.py | issue_invoice; rectify_invoice | test_fiscal.py; test_consolidation_fiscal.py | S1/01, R1/R5; sin ampliar regimen |
| Inmutabilidad/hash/XML/QR | COMPLETO LOCAL | billing/models.py; verifactu/protocol.py | verify_chain; validate_xml | test_fiscal.py; test_audit_fiscal.py | Triggers tambien REPLACE |
| Outbox y subsanaciones | COMPLETO LOCAL | verifactu/services.py | send_one; correct_rejected; annul_record | test_audit_fiscal.py | Respuesta sintetica identificada; oficial pendiente |
| Cola impresion y agente remoto | COMPLETO LOCAL | hardware/services.py; agent.py | enqueue_invoice; bridge claim/ack | test_audit_hardware.py; test_consolidation_hardware.py | UNKNOWN no reenvia automaticamente |
| Corte/cajon y dispositivos | COMPLETO LOCAL | hardware/models.py; support/forms.py | save_printer; enqueue_test | test_consolidation_hardware.py; test_consolidation_ops.py | Politica snapshot de bytes; cash solamente |
| Incidencias/actuaciones/resolucion | COMPLETO LOCAL | support/incidents.py; models.py | support:incidents; incident_detail | test_consolidation_ops.py; test_consolidation_acceptance.py | Manager operativa; SA+TECH tecnica; sin datos personales |
| Superadmin diagnostico y servicios | COMPLETO LOCAL | support/services.py; views.py | support:index; diagnostic | test_audit_ops.py; test_consolidation_ops.py | Mediciones/versiones reales |
| Backup/restore/updates | COMPLETO LOCAL | support/operations.py; updates.py; scripts | support:restore_advisor; update.py; restore.py | test_backup.py; test_audit_ops.py; upgrade JSON | Offline seguro; no consola web |
| Informes/exportacion/auditoria | COMPLETO LOCAL | reports/views.py; audit/views.py | reports:index; audit:index | test_audit_backend.py; test_audit_matrix.py | Snapshots y devoluciones conciliados |
| Navegacion/responsive/error/empty | COMPLETO LOCAL | templates; static/css/beautytpv.css | Todos los modulos autorizados | test_audit_matrix.py; tests/e2e; UI_REVIEW.md | No basta ruta existente |

## Validaciones externas separadas

| Requisito | Estado | Implementación / ruta | Evidencia | Cómo resolver el bloqueo |
|---|---|---|---|---|
| AEAT oficial, certificado, acuses y conformidad | BLOQUEADO EXTERNO | verifactu SOAP/outbox; production_guard | Tests locales/XSD; no remisión | Certificado autorizado, pruebas oficiales, conciliación y declaración responsable suscrita |
| Impresora, papel80mm, QR y cajón reales | BLOQUEADO EXTERNO | hardware bridge/driver/spool | Simulador/TCP/API de prueba | Facilitar modelo/firmware y ejecutar checklist físico HARDWARE.md |
| Equipo/LAN/autoarranque/TLS y usuarios del salón | BLOQUEADO EXTERNO | scripts servicio/agente/runbooks | Copias temporales y loopback | Instalar en destino, comprobar CA/firewall/backup y aceptación con operadores reales |

Detalles e instrucciones precisas: [FINAL_ACCEPTANCE.md](FINAL_ACCEPTANCE.md). No retirar el guard fiscal a partir de pruebas locales.

Indice de pruebas concretas: [TEST_INDEX](consolidation/TEST_INDEX.md). Inventario archivo/linea/ruta/modelo/plantilla: [INVENTARIO](consolidation/inventory/INVENTARIO.md).
