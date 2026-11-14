# Consolidación fiscal — revisión independiente

Fecha: 14-11-2026. Referencia de esta evolución: `5dc936a`/correcciones `7045b03`.

## Hallazgos y contratos

| Requisito | Estado | Implementación / ruta o servicio | Prueba y evidencia | Observaciones / bloqueo |
|---|---|---|---|---|
| Configuración futura no altera identidad y dirección ya emitidas | COMPLETO LOCAL | `apps/billing/services.py:issue_invoice`, `apps/verifactu/protocol.py:qr_url`, snapshots `Invoice.issuer` | `test_commercial_configuration_changes_do_not_rewrite_fiscal_history`: DB/XML/huella/QR y texto PDF | Sin validación normativa de datos de empresa real |
| Cambiar serie afecta solo documentos nuevos | COMPLETO LOCAL | `issue_invoice`, `InvoiceSequence` | `test_new_authorized_series_applies_only_to_future_documents` | Se preserva S-1; nueva NEXT-1 y cadena coherente |
| Rectificativa conserva identidad del original y usa serie actual autorizada | COMPLETO LOCAL | `rectify_invoice` | `test_refund_keeps_original_identity_when_commercial_settings_change` | Solo devolución total soportada R1/R5 |
| Producción requiere aprobación y evidencia externa | COMPLETO LOCAL / BLOQUEADO EXTERNO | `production_guard` | `test_technical_settings_cannot_replace_external_production_gate` (dos combinaciones) | No certificado, acuse oficial ni declaración firmada |
| No cambiar NIF/identificador de instalación después de emitir | IMPLEMENTADO Y VERIFICADO LOCAL | `core.services.save_company_settings` rechaza cambiar obligado/instalación tras primera Invoice | `test_consolidation_backend.py::test_company_identity_cannot_be_reassigned_after_invoice` | El servicio bloquea el cambio y conserva la identidad; el texto previo describía el hallazgo de entrada |
| Datos comerciales/logo en documentos futuros | CONTRATO | Todo dato mostrado en documento emitido debe formar parte del snapshot, no leerse de CompanySettings al reimprimir | `test_consolidation_documents.py`: snapshot, PDF, copia térmica y rectificativa | No añadir lectura mutable del logo a PDF/térmico histórico |

## Fuentes y contraste técnico

Reconsultada la [información técnica oficial AEAT](https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu/informacion-tecnica.html), que enlaza esquemas, WSDL, hash y especificación QR. No se cambian reglas fiscales ni se amplía el régimen soportado.

Se descargaron únicamente recursos públicos por HTTPS, validando TLS y HTTP200; los cuatro SHA256 coinciden con `schemas/aeat/manifest.json`:

| Recurso | Bytes | SHA256 |
|---|---:|---|
| SistemaFacturacion.wsdl | 8780 | 05919120708ff7650612fa6683c9336eaf919335d9a4db10e86759190af48602 |
| SuministroLR.xsd | 1573 | cbdac8d427cc5ab5d77ca48974cab0f35d6bb819c4c66db361681e3710aeba36 |
| SuministroInformacion.xsd | 49540 | ee4c1655175644de44c4c25055ffeb8e5f4bb4bc3834ce8254d4222ef18c8aa1 |
| RespuestaSuministro.xsd | 6259 | 82acf80f785643caac13087aae66808ed721a13f08ca5218cf8ae81b695549ef |

El manifest conserva las URL oficiales exactas. Una descarga pública no constituye remisión fiscal, autenticación mTLS, aceptación ni evidencia de conformidad.

## Verificación ejecutada

`python -m pytest -q tests/test_consolidation_fiscal.py`: **5 PASS, 5,14 s**. Ruff check y format aplicados al archivo nuevo. La suite completa de integración pertenece al coordinador; estos cinco casos no acreditan por sí solos toda la fiscalidad.

Propiedad limitada a `tests/test_consolidation_fiscal.py` y este informe; no se modificaron módulos de otros especialistas.

## Bloqueos externos

Se mantiene IVA general S1/01, F1/F2 y rectificación total R1/R5; no regímenes especiales ni devoluciones parciales. Para cerrar producción: certificado/autorización del obligado, ensayos oficiales con acuses y errores/duplicados conciliados, revisión experta, declaración responsable suscrita y validación del QR impreso. No se remitió ningún registro y no se afirma prueba física.
