# Revisión fiscal de la DEMO Windows

Fecha: 14-11-2026. Revisión de código existente, sin cambios de reglas fiscales, esquemas, algoritmos ni módulos funcionales. Propiedad de este especialista: este documento únicamente. No se remitió ningún registro a AEAT.

## Hallazgos y contrato recomendado

| Requisito | Evidencia del código actual | Control DEMO requerido |
|---|---|---|
| TEST no equivale a desconectado | `apps/verifactu/services.py::send_one` usa un endpoint oficial TEST si dispone de certificado | No iniciar `operations_worker`, `send_fiscal` ni ningún scheduler que invoque `send_one` |
| Bloqueo antes de red | `send_one` consulta `settings.FISCAL_RESTORE_HOLD` antes de reservar outbox o invocar transporte | Perfil `config.demo_settings` debe fijar ese flag a True. No crear el archivo `.fiscal-restore-hold`, que también impediría vender/imprimir |
| Entorno y aprobación | `CompanySettings.fiscal_mode`, `TechnicalSettings.fiscal_environment` y el modo inmutable de Invoice se utilizan en caminos distintos | Perfil y DB exclusivamente TEST; `FISCAL_PRODUCTION_APPROVED=False`, evidencia vacía. Validar al iniciar, sin modificar DB principal |
| Certificados | `support.fiscal.fiscal_configuration` prioriza referencias de TechnicalSettings sobre settings | AEAT_CERTIFICATE/AEAT_PRIVATE_KEY vacíos y rechazar configuración DEMO con referencias persistidas; no heredar variables de una instalación real |
| Panel fiscal visible | POST `support:fiscal_settings` guarda referencias y modo de empresa | Permitir GET para inspección; rechazar POST mediante middleware/wrapper exclusivo DEMO con mensaje de modo TEST desconectado |
| Diagnóstico de red | POST diagnóstico con `network=1` realiza TCP443 hacia AEAT | Rechazar esa opción en DEMO o devolver diagnóstico explícitamente no realizado sin llamada a red. El diagnóstico DB local puede seguir funcionando |
| Cola real, no acuses ficticios | Cobro genera Invoice/FiscalRecord/FiscalOutbox en la misma transacción | Conservar PENDING; mostrar remisión deshabilitada. Recuperar cola solo cambia elegibilidad, nunca significa aceptación |
| Fiscalidad soportada | F1/F2 y rectificación total R1/R5, IVA general S1/01 existentes | No ampliar alcance. Mantener aviso de pruebas, QR de TEST y guard productivo |

Datos sintéticos ya utilizados por la suite fiscal: NIF `89890001K`, razón social `Centro BeautyTPV DEMO`, domicilio ficticio claramente identificado y productor `Productor DEMO sin validez fiscal`, NIF de productor `89890001K`. Es un valor de prueba con formato aceptado por los tests/XSD, no una afirmación de identidad o autorización del titular. Instalación de prueba separada, por ejemplo `DEMO-LOCAL`.

## Comprobación local ejecutada

Se ejecutó Python con Django y `override_settings(FISCAL_RESTORE_HOLD=True)`, interceptando `requests.post` para que fallara si fuera invocado. `send_one()` devolvió ValidationError antes de acceder a transporte; el mock no recibió ninguna llamada. No se crearon facturas ni se escribieron datos para esa comprobación. Resultado: **PASS** del guard existente.

El coordinador debe comprobar además el perfil completo de arranque, la validación de DB, el rechazo del POST fiscal/diagnóstico de red y que el servidor DEMO no inicia el scheduler fiscal. Esta revisión inicial no atribuye todavía esas pruebas a los archivos nuevos.

## Bloqueos externos

La demostración no valida AEAT, certificado, acuses oficiales, declaración responsable ni hardware físico. No se retirará el bloqueo productivo. No fue necesario reconsultar normativa/XSD porque esta tarea no modifica las reglas fiscales; los esquemas fijados y sus evidencias anteriores permanecen intactos.

## Cierre integrado del coordinador

La decisión final y pruebas reales están en ../GUIA_WINDOWS_DEMO.md y ../evidence/windows-demo-smoke.json. Perfil config.demo_settings con DEBUG=False, guards específicos de simulación, transportes físicos rechazados y remisión bloqueada. Factura TEST/spool simulado verificados, cero FiscalTransmission. Se preservan límites externos; esta sección supersede recomendaciones preliminares que no se adoptaron.
