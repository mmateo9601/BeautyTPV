# CRUD y transiciones por modulo

Fecha: 14-11-2026. Base: `5dc936a`; requisitos: [peticion de consolidacion](consolidation/REQUEST.md). Resultado definitivo en [FINAL_ACCEPTANCE.md](FINAL_ACCEPTANCE.md). Archivos sin prefijo se refieren a apps/, salvo config/templates/static/scripts. Pruebas en tests/ y tests/e2e/.

Estados: COMPLETO LOCAL (implementado y prueba aprobada en el escenario indicado), PARCIAL, PENDIENTE, BLOQUEADO EXTERNO. No se confunde simulacion con validacion AEAT o fisica.

| Requisito | Estado | Implementacion | Ruta o servicio | Prueba / evidencia | Observaciones / bloqueo |
|---|---|---|---|---|---|
| Usuarios: alta/lista/filtros/edicion/activo/credenciales/revocar | COMPLETO LOCAL | accounts/services.py; support/views.py | team:index/edit/unlock/revoke_sessions | test_security.py; test_consolidation_security.py; test_consolidation_ops.py | Identificador estable; sin borrado con historial |
| Clientes: alta/busqueda/consulta/edicion/historial/borrado permitido | COMPLETO LOCAL | customers/views.py; services.py | customers:* | test_regressions.py; test_audit_forms.py | Borrado solo Admin y sin relaciones; PII SA |
| Servicios y productos: alta/lista/busqueda/filtro/edicion/desactivar/orden | COMPLETO LOCAL | catalog/forms.py; services.py; views.py | catalog:create/edit/index | test_audit_forms.py; test_consolidation_backend.py | Mismo CatalogItem con kind; no altera snapshot |
| Categorias: alta/lista/edicion/orden/visible/borrado permitido | COMPLETO LOCAL | catalog/services.py; views.py | catalog:category/category_edit/category_delete | test_regressions.py; test_consolidation_backend.py | PROTECT si hay articulos |
| Secciones: alta/lista/edicion/orden/borrado permitido | COMPLETO LOCAL | layout/services.py; views.py | layout:section_create/edit/delete | test_audit_backend.py; test_consolidation_backend.py | Puestos protegidos; seccion inicial nullable |
| Puestos: alta/lista/busqueda/edicion/orden/activo/estados | COMPLETO LOCAL | layout/services.py; pos/views.py | layout:station_create/edit/delete | test_consolidation_backend.py; test_consolidation_acceptance.py | No desactivar/reasignar con cuenta; historial PROTECT |
| Cuentas: abrir/consultar/modificar/cancelar/cobrar/cerrar | COMPLETO LOCAL | pos/services.py | pos:open_station/ticket/cancel_ticket/checkout | test_acceptance.py; test_concurrency.py | Transiciones, no delete |
| Lineas: agregar/consulta/cantidad/nota/descuento/retirar | COMPLETO LOCAL | pos/services.py | pos:add_line/update_line/remove_line | test_audit_ui.py; test_audit_forms.py | No modificar al cerrar/en cobro |
| Ventas: consultar/filtrar/documentar/rectificar | COMPLETO LOCAL | reports/views.py; billing/views.py | reports:index; billing:* | test_acceptance.py; test_audit_backend.py | Sin CRUD historico; operaciones compensatorias |
| Cajas: alta/lista/consulta/edicion/desactivar/terminal | COMPLETO LOCAL | cash/services.py; views.py | cash:registers/register_create/register_edit | test_consolidation_backend.py; test_consolidation_acceptance.py | Sin borrado con historial; turno abierto protegido |
| Turnos: apertura/consulta/cierre/arqueo/movimientos/historial | COMPLETO LOCAL | cash/services.py | cash:index/open/movement/close | test_audit_forms.py; test_backend.py | Sin edicion/borrado retrospectivo |
| Facturas: emitir/listar/filtrar/consulta/PDF/imprimir/rectificar | COMPLETO LOCAL | billing/services.py; views.py | billing:index/detail/pdf/rectify/reprint | test_fiscal.py; test_browser.py | Inmutables; rectificacion total |
| Terminales: alta/lista/busqueda/edicion/activo/preferencias/diagnostico | COMPLETO LOCAL | core/models.py; support/services.py; views.py | support:terminals/terminal_edit | test_audit_ops.py; test_consolidation_ops.py | Token hash; last_seen medido |
| Impresoras: alta/lista/edicion/activo/driver/asignacion/pruebas/cola | COMPLETO LOCAL | hardware/services.py; support/views.py | save_printer; support:printer_save/printer_edit | test_audit_hardware.py; test_consolidation_hardware.py | Entrega incierta sin reintento automatico |
| Backups: crear/listar/verificar/descargar/restore | COMPLETO LOCAL | support/operations.py; views.py | support:backup/backup_download/restore_advisor | test_backup.py; test_audit_acceptance.py | Cifrado y restore offline con hold |
| Incidencias: alta/lista/filtros/consulta/clasificar/actuar/resolver/reabrir | COMPLETO LOCAL | support/incidents.py; views.py | support:incidents/incident_detail | test_consolidation_ops.py; test_consolidation_acceptance.py | Actuaciones append-only; no borrado |

## Validaciones externas separadas

| Requisito | Estado | Implementación / ruta | Evidencia | Cómo resolver el bloqueo |
|---|---|---|---|---|
| AEAT oficial, certificado, acuses y conformidad | BLOQUEADO EXTERNO | verifactu SOAP/outbox; production_guard | Tests locales/XSD; no remisión | Certificado autorizado, pruebas oficiales, conciliación y declaración responsable suscrita |
| Impresora, papel80mm, QR y cajón reales | BLOQUEADO EXTERNO | hardware bridge/driver/spool | Simulador/TCP/API de prueba | Facilitar modelo/firmware y ejecutar checklist físico HARDWARE.md |
| Equipo/LAN/autoarranque/TLS y usuarios del salón | BLOQUEADO EXTERNO | scripts servicio/agente/runbooks | Copias temporales y loopback | Instalar en destino, comprobar CA/firewall/backup y aceptación con operadores reales |

Detalles e instrucciones precisas: [FINAL_ACCEPTANCE.md](FINAL_ACCEPTANCE.md). No retirar el guard fiscal a partir de pruebas locales.

Indice de pruebas concretas: [TEST_INDEX](consolidation/TEST_INDEX.md). Inventario archivo/linea/ruta/modelo/plantilla: [INVENTARIO](consolidation/inventory/INVENTARIO.md).
