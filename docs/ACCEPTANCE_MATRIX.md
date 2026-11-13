# Matriz de aceptación E01–E16

Fecha: 13-11-2026. Ejecución local con Python 3.14.7, Django 5.2.19,
SQLite en disco local y Chromium 158.0.8127.18 mediante Playwright.
Los datos de prueba son sintéticos y las bases temporales están separadas de la instalación.

**Release productiva BLOQUEADA.** Las pruebas de software no sustituyen la remisión
oficial de AEAT, la revisión experta fiscal, la declaración responsable del productor
ni las pruebas de impresora y cajón físicos. No se ha recibido certificado ni hardware.

## Evidencias automatizadas

| Escenario | Prueba repetible | Resultado de software | Límite pendiente |
|---|---|---|---|
| E01 abrir turno, manicura efectivo, factura, imprimir, liberar puesto | `test_acceptance.py::test_e01_cash_sale_invoice_spool_and_closure`; `test_browser.py::test_e01_browser_pin_cash_invoice_copy_report_and_close` | VERIFICADO: navegador PIN→caja→plano→carrito→cobro→PDF/QR→copia→informe→arqueo. Spool y cajón probados con simulador identificado | Impresión y cajón físicos BLOQUEADOS |
| E02 A1/A2 persistentes después de reinicio | `test_concurrency.py::test_e02_accounts_survive_process_restart`; `test_browser.py::test_e02_browser_accounts_survive_navigation_and_new_browser_session` | VERIFICADO: cuentas independientes recuperadas por procesos nuevos y sesiones de navegador nuevas | Reinicio completo del sistema operativo NO VERIFICADO |
| E03 varios IVA y descuento autorizado | `test_acceptance.py::test_e03_multiple_tax_rates_and_authorized_discount`; `test_browser.py::test_e03_e16_browser_catalog_customer_full_invoice_and_snapshot` | VERIFICADO: 21 % + 10 %, descuento denegado a empleado, totales/base/cuota exactos; catálogo, cliente y factura F1 desde navegador | Tipo legal aplicable a los artículos reales requiere configuración del negocio |
| E04 pago mixto | `test_acceptance.py::test_e04_mixed_cash_only_component_in_cash_balance` | VERIFICADO: componentes suman venta, cambio correcto y caja solo aumenta por efectivo | Confirmación bancaria real del datáfono NO VERIFICADA; se registra referencia externa |
| E05 doble cobro/dos terminales | `test_concurrency.py::test_e05_two_terminals_same_idempotency_key_one_sale`; `test_e05_different_keys_do_not_double_charge_ticket` | VERIFICADO: dos procesos reales, una venta/factura/alta/trabajo original con misma clave; clave distinta sobre cuenta cerrada rechazada | Capacidad mayor y topología LAN real NO VERIFICADAS |
| E06 impresora caída | `test_acceptance.py::test_e06_printer_failure_keeps_sale_and_controlled_copy`; `test_hardware.py` | VERIFICADO: fallo previo al envío mantiene factura/venta; copia explícita sin cajón; entrega incierta no se reintenta automáticamente | Fallo físico y firmware BLOQUEADOS |
| E07 red/AEAT caída | `test_acceptance.py::test_e07_network_loss_does_not_regenerate_fiscal_record`; `test_fiscal.py::test_network_failure_persists_chain` | VERIFICADO: excepción de red simulada, RETRY persistente, cadena y registro originales intactos | Caída y recuperación con endpoint AEAT oficial BLOQUEADAS sin certificado |
| E08 rechazo AEAT y subsanación | `test_acceptance.py::test_e08_rejected_correction_preserves_original`; `test_fiscal.py::test_soap_schema_identity_and_receipt_persistence` | VERIFICADO: fixture SOAP conforme a XSD oficial, rechazo 1100 y respuesta preservados; subsanación nueva encadenada sin alterar origen | Rechazo/subsanación oficial y resolución experta BLOQUEADOS |
| E09 factura inmutable | `test_acceptance.py::test_e09_e16_sql_immutability_and_historical_price_snapshot`; `test_fiscal.py` | VERIFICADO: denegación de edición/borrado por ORM y SQL directo; rectificativa separada | Acceso físico administrativo al fichero requiere controles del servidor |
| E10 empleado sin cierre/informes/soporte | `test_acceptance.py::test_e10_e11_roles_reject_backend_privilege_escalation`; `test_security.py`; `test_backup.py` | VERIFICADO: 403 backend y PermissionDenied en servicios; encargado autorizado puede cerrar | Prueba de aceptación con empleados reales NO VERIFICADA |
| E11 admin no crea Superadmin; diagnóstico elevado auditado | `test_acceptance.py::test_e11_superadmin_diagnostic_requires_elevation_and_authorization`; `test_backup.py::test_admin_cannot_create_superadmin_via_team_ui` | VERIFICADO: elevación y autorización temporal obligatorias; diagnóstico auditado y revocación inmediata | Operación técnica con responsable real NO VERIFICADA |
| E12 backup/restore sin duplicados | `test_concurrency.py::test_e12_restore_real_issued_database_holds_send_and_preserves_idempotency`; `test_backup.py` | VERIFICADO: backup cifrado de BD real emitida, highwatermarks, restore a fichero nuevo, cadena válida; remisión y cobro bloqueados hasta conciliación, sin duplicados | Conciliación de acuses AEAT reales BLOQUEADA |
| E13 tres terminales SQLite | `test_concurrency.py::test_e13_three_terminal_sales_numbering_and_chain` | VERIFICADO: tres procesos independientes, cuentas cerradas, números únicos y cadena correcta | Ensayo pequeño local; no es certificación de capacidad ni benchmark de carga sostenida |
| E14 ticket 80 mm, QR legible y cajón | `test_hardware.py::test_receipt_snapshot_qr_cut`; `test_acceptance.py::test_e14_card_receipt_never_opens_drawer_software_only` | VERIFICADO SOLO SOFTWARE: bytes ESC/POS, URL/QR, corte, efectivo con cajón y tarjeta sin cajón | **BLOQUEADO FÍSICO**: legibilidad 80 mm, escaneo QR, marca/modelo/firmware, USB/Ethernet y apertura real |
| E15 devolución mediante rectificativa y conciliación | `test_acceptance.py::test_e15_rectification_reconciles_cash_and_report`; `test_e15_refund_rechecks_closed_cash_session_from_database` | VERIFICADO: original intacto, R5 conforme XSD, caja/IVA/métodos/empleados/artículos netos conciliados; caja cerrada rechazada incluso con objeto obsoleto | Remisión oficial de rectificativa y devolución bancaria real BLOQUEADAS |
| E16 cambio de precios no altera histórico | `test_acceptance.py::test_e09_e16_sql_immutability_and_historical_price_snapshot`; `test_browser.py::test_e03_e16_browser_catalog_customer_full_invoice_and_snapshot` | VERIFICADO: modificar catálogo después de emitir mantiene descripción/precio/total de factura | Sin límite adicional de software identificado por esta prueba |

## Ejecución reproducible

```powershell
.venv/Scripts/python -m pytest tests/test_acceptance.py tests/test_concurrency.py -q --junitxml=test-results/qa-services-processes.xml -o junit_family=xunit1
.venv/Scripts/python -m pytest tests/e2e/test_browser.py -q --browser chromium --junitxml=test-results/qa-browser.xml -o junit_family=xunit1 --screenshot only-on-failure
.venv/Scripts/ruff check tests/test_acceptance.py tests/test_concurrency.py tests/e2e
.venv/Scripts/ruff format --check tests/test_acceptance.py tests/test_concurrency.py tests/e2e
```

En Windows con sandbox de procesos, Chromium necesita ejecución autorizada fuera del
sandbox. El bloqueo del lanzamiento del navegador dentro del sandbox no es un resultado
de la aplicación. En CI instalar antes `python -m playwright install --with-deps chromium`.

Resultados QA ejecutados: **17 pruebas de aceptación/procesos pasadas en 38,90 s**;
**3 pruebas de navegador pasadas en 31,06 s**. Ruff de los archivos QA sin incidencias.
El plugin de navegador instalado emite un aviso de deprecación de fixture de pytest 10;
los flujos pasan con pytest 9.2. La suite integrada final puede ampliar esta evidencia.

Los procesos no usan una base `:memory:` ni deshabilitan triggers para probar la
concurrencia: crean una instalación temporal con migraciones reales, abren conexiones
independientes y terminan. El teardown elimina el entorno temporal, sin `flush` sobre
documentos emitidos. El ensayo de tres procesos guarda el tiempo observado en el JUnit;
no demuestra un umbral de migración a PostgreSQL.

Las capturas `docs/evidence/floor-desktop.png` y `ticket-tablet.png`, y el PDF
`invoice-test.pdf`, proceden de los flujos reales sobre datos de prueba. Las capturas
no son pruebas físicas de impresión y el PDF lleva aviso de pruebas sin validez fiscal.

## Gate de release

- Código automatizado E01–E16: resultados anteriores, con los límites indicados.
- Certificado, transporte mTLS y remisión/acuse real AEAT: **BLOQUEADO**.
- Revisión fiscal externa y declaración responsable del productor firmada: **PENDIENTE**.
- Hardware real, QR escaneado y ticket de 80 mm: **BLOQUEADO**.
- Ensayo de aceptación con propietario/encargado/empleado/Superadmin reales: **NO VERIFICADO**.
- No aprobar producción mientras falten estos gates. El coordinador consolida la
  evidencia definitiva en `docs/RELEASE_REPORT.md`.
