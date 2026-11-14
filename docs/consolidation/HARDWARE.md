# Consolidación de dispositivos y preferencias de impresión

Referencia: auditoría `7045b03`/`5dc936a`. Propiedad de este módulo: `apps/hardware/`, `tests/test_consolidation_hardware.py`. Contrato aprobado por architect; integración del formulario protegida corresponde a support/devops.

| Requisito | Estado local | Implementación y operación | Prueba/evidencia | Límite |
|---|---|---|---|---|
| Corte de papel configurable | Implementado y probado en servicio | `Printer.cut_paper`, `render_receipt`, `render_test`; campo True preserva conducta anterior | `test_output_preferences_persist_and_snapshot_receipt`, `test_test_ticket_obeys_cut_and_explicit_drawer_policy` | Compatibilidad de cortador físico BLOQUEADO EXTERNO |
| Cajón desactivable por dispositivo | Implementado y probado en servicio | `Printer.drawer_enabled`; efectivo genera recibo sin pulso si está deshabilitado; prueba explícita de cajón rechazada | `test_cash_drawer_can_be_disabled_without_removing_receipt` ejecuta venta/caja/factura reales; prueba positiva y negativa de TEST | Apertura física BLOQUEADO EXTERNO |
| Guard efectivo y copia sin pulso | Verificado | `enqueue_invoice`: solo pago CASH permite pulso, COPIA nunca | Suite hardware original + ampliada | No cobro bancario simulado |
| Cambios solo afectan nuevas intenciones | Verificado | Bytes persistidos `PrintJob.payload`, no reconstruidos al reintentar | Snapshot original idéntico después de editar preferencias; original idempotente; nueva copia usa configuración nueva | Trabajos pendientes previos conservan su configuración |
| Configuración protegida sin request | Verificado | `save_printer(printer, actor)` requiere Superadmin actual, valida y audita `device.saved` | Tres roles inferiores denegados, edición auditada | Elevación y scope TECHNICAL se aplican además en frontera HTTP |
| No cambiar destino durante entrega | Verificado en validación/servicio | `Printer.clean` impide cambiar conexión/dirección/puerto/USB/terminal con SENDING | `test_configurable_output_change_audited_and_inflight_target_protected` | No es defensa contra un administrador OS que modifique SQL directamente |
| No operar con impresora desactivada mediante objeto obsoleto | Verificado | `enqueue_test` y `retry_job` recargan Printer actual | `test_stale_enabled_printer_cannot_create_or_reroute_work` | Actualización concurrente posterior se vuelve a comprobar al reclamar trabajo |
| Entrega incierta no reintentable | Verificado | UNKNOWN/leases, journal y ACK ya existentes; copia explícita | Suites existentes y nuevo caso de mantenimiento | Revisar papel/cajón antes de solicitar copia |
| CRUD y preferencias desde pantalla | Integración pendiente del propietario support al entregar este módulo | `PrinterForm`: añadir `cut_paper`, `drawer_enabled`; `printer_save`: `save_printer(form.save(commit=False), request.user)` | QA coordinador verificará formulario HTTP/Chromium | No marcar completo solo por campo existente |

Migración aditiva `hardware/0004_printer_output_preferences.py`; defaults True, sin modificar filas de PrintJob ni bytes de documentos emitidos. No hay eliminación física de dispositivos con historial; enabled conserva trazabilidad.

Verificación ejecutada: `pytest -q tests/test_consolidation_hardware.py tests/test_hardware.py tests/test_audit_hardware.py` → **44 PASS en 2,33 s**. Incluye TCP loopback real, simulador y transportes controlados; ninguna impresora ni cajón físicos. Primer intento sandbox de TCP fue denegado por Windows10013; repetición autorizada fuera del sandbox pasó sin omitir el caso. Una prueba nueva inicialmente aislaba pago con mock ineficaz; se sustituyó por venta real de aceptación, sin debilitar validaciones.

Ruff check y format para archivos del módulo correctos. Los tests aplicaron migraciones desde DB nueva; instalación/upgrade integral y revisión visual quedan en el gate del coordinador.
