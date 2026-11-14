# Ajustes disponibles y restricciones

Fecha: 14-11-2026. Base: `5dc936a`; requisitos: [peticion de consolidacion](consolidation/REQUEST.md). Resultado definitivo en [FINAL_ACCEPTANCE.md](FINAL_ACCEPTANCE.md). Archivos sin prefijo se refieren a apps/, salvo config/templates/static/scripts. Pruebas en tests/ y tests/e2e/.

Estados: COMPLETO LOCAL (implementado y prueba aprobada en el escenario indicado), PARCIAL, PENDIENTE, BLOQUEADO EXTERNO. No se confunde simulacion con validacion AEAT o fisica.

| Requisito | Estado | Implementacion | Ruta o servicio | Prueba / evidencia | Observaciones / bloqueo |
|---|---|---|---|---|---|
| Nombre comercial y direccion comercial | COMPLETO LOCAL | core/models.py; forms.py | core:settings?section=commercial | test_consolidation_backend.py; test_consolidation_documents.py | Solo nuevas emisiones |
| Razon social/NIF/domicilio fiscal | COMPLETO LOCAL | core/models.py; services.py | core:settings?section=fiscal | test_consolidation_backend.py; test_consolidation_fiscal.py | NIF bloqueado tras emitir; nombre/domicilio solo futuros |
| Telefono/email | COMPLETO LOCAL | core/forms.py | core:settings?section=commercial | test_consolidation_backend.py; test_consolidation_ui.py | Email validado; snapshot comprobantes |
| Logo subir/consultar/retirar | COMPLETO LOCAL | core/services.py; views.py | core:logo_save; core:logo | test_consolidation_acceptance.py | PNG canonical; 2MiB entrada/16MP/600px/256KiB salida; UI protegida |
| Pie de comprobante | COMPLETO LOCAL | core/models.py; billing/services.py; hardware/escpos.py | save_company_settings; issue_invoice | test_consolidation_documents.py | Texto escapado/saneado y snapshot; no HTML libre |
| Timezone y EUR | COMPLETO LOCAL | core/models.py; config/middleware.py | save_company_settings | test_audit_configuration.py; test_consolidation_acceptance.py | IANA valida; EUR fijo |
| Tema/densidad/paleta estado | COMPLETO LOCAL | core/models.py; templates/base.html; static/css | core:settings?section=pos | test_consolidation_ui.py | Opciones cerradas, texto/color accesible |
| Inicio y seccion preferida | COMPLETO LOCAL | core/models.py; pos/views.py | pos:floor; CompanySettings.default_section | test_consolidation_backend.py; test_consolidation_ui.py | Inicio siempre plano, no URL arbitraria |
| Venta rapida | COMPLETO LOCAL | core/models.py; pos/services.py | quick_sale_enabled; quick_ticket | test_audit_backend.py; test_consolidation_ui.py | Opcion persistida |
| Categorias visibles y orden servicios | COMPLETO LOCAL | catalog/models.py; services.py; pos/services.py | Category.visible_in_pos/sort_order; CatalogItem.sort_order | test_consolidation_backend.py; test_consolidation_acceptance.py | Ocultacion tambien backend |
| Secciones/puestos/nombres/orden/actividad | COMPLETO LOCAL | layout/models.py; services.py | layout:* | test_consolidation_backend.py | Sin editor grafico innecesario |
| Preferencia de terminal caja/seccion | COMPLETO LOCAL | core/models.py; support/forms.py; pos/views.py | Terminal.default_section/default_register | test_consolidation_backend.py; test_consolidation_ops.py | No concede permisos; caja activa compatible |
| Cajas asociadas, actividad e historial | COMPLETO LOCAL | cash/models.py; services.py | cash:registers; save_register | test_consolidation_backend.py; test_consolidation_acceptance.py | No reasignar/desactivar con turno |
| Impresoras/driver/terminal/corte/cajon | COMPLETO LOCAL | hardware/models.py; support/forms.py | support:printer_save; save_printer | test_consolidation_hardware.py; test_consolidation_ops.py | Snapshot de bytes de cada trabajo; no mutar enviados |
| Series e instalacion | COMPLETO LOCAL | core/services.py; billing/services.py | core:settings?section=fiscal | test_consolidation_fiscal.py; test_consolidation_backend.py | Series distintas; contador legal no editable |
| Tipos soportados e impuestos | COMPLETO LOCAL | catalog/forms.py; verifactu/protocol.py | CatalogItem.tax_rate; issue_invoice | test_fiscal.py; test_acceptance.py | IVA S1/01 F1/F2 R1/R5; no ampliar alcance fiscal |
| TEST/produccion/certificados | COMPLETO LOCAL | support/fiscal.py; forms.py; billing/services.py | support:fiscal_settings; production_guard | test_audit_ops.py; test_consolidation_fiscal.py | Referencias externas; produccion bloqueada |
| Diagnostico/cola/reintento/subsanacion | COMPLETO LOCAL | support/views.py; verifactu/services.py | support:diagnostic/recover_fiscal/correct_fiscal | test_audit_fiscal.py; test_audit_ops.py | Sin aceptar respuesta AEAT inexistente |
| Backup/retencion/mantenimiento | COMPLETO LOCAL | support/models.py; operations.py | support:settings; restore_advisor | test_backup.py; test_audit_ops.py | Retencion positiva; preservar copia mas reciente |
| Paquetes/version/actualizacion/rollback | COMPLETO LOCAL | support/updates.py; scripts/update.py | support:updates; update.py --offline | test_audit_ops.py; test_backup.py | No ejecuta shell web; venv incompatible aborta |

## Validaciones externas separadas

| Requisito | Estado | Implementación / ruta | Evidencia | Cómo resolver el bloqueo |
|---|---|---|---|---|
| AEAT oficial, certificado, acuses y conformidad | BLOQUEADO EXTERNO | verifactu SOAP/outbox; production_guard | Tests locales/XSD; no remisión | Certificado autorizado, pruebas oficiales, conciliación y declaración responsable suscrita |
| Impresora, papel80mm, QR y cajón reales | BLOQUEADO EXTERNO | hardware bridge/driver/spool | Simulador/TCP/API de prueba | Facilitar modelo/firmware y ejecutar checklist físico HARDWARE.md |
| Equipo/LAN/autoarranque/TLS y usuarios del salón | BLOQUEADO EXTERNO | scripts servicio/agente/runbooks | Copias temporales y loopback | Instalar en destino, comprobar CA/firewall/backup y aceptación con operadores reales |

Detalles e instrucciones precisas: [FINAL_ACCEPTANCE.md](FINAL_ACCEPTANCE.md). No retirar el guard fiscal a partir de pruebas locales.

Indice de pruebas concretas: [TEST_INDEX](consolidation/TEST_INDEX.md). Inventario archivo/linea/ruta/modelo/plantilla: [INVENTARIO](consolidation/inventory/INVENTARIO.md).
