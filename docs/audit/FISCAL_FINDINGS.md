# Auditoría fiscal técnica contra 4ce821e

Auditor fiscal; propiedad apps/billing, apps/verifactu, tests/test_audit_fiscal.py.
No modifica módulos ajenos ni afirma remisión AEAT o prueba física. La integración
final del coordinador prevalece sobre resultados parciales de este módulo.

## Fuentes reconsultadas y vigencia técnica observada

- [Índice técnico AEAT](https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu/informacion-tecnica.html).
- [Servicio AEAT v1.0.3, 28-07-2025](https://sede.agenciatributaria.gob.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/Veri-Factu_Descripcion_SWeb.pdf), apartados 6.4.4.1, 9.1.2, 9.1.3, 9.2.2 y 9.2.3.
- Comparación HTTPS con TLS validado de los cuatro archivos vigentes WSDL,
  SuministroLR.xsd, SuministroInformacion.xsd y RespuestaSuministro.xsd:
  **los cuatro hashes coinciden con schemas/aeat/manifest.json**. No se sustituyeron
  esquemas ni se desactivó verificación TLS.
- [Ejemplo orientativo AEAT de declaración v0.5.1](https://sede.agenciatributaria.gob.es/static_files/Sede/Tema/IVA/Verifactu/EjemplosDeclaracionResponsable(V0.5.1).pdf): se añade borrador sin suscribir, no declaración ficticia.

La especificación de servicio publica espera entre remisiones; se implementa por
endpoint y se conserva entre workers/reinicios. La subsanación de aceptación con
errores usa S sin rechazo previo; el alta rechazada usa S/X; la anulación rechazada
continúa siendo anulación y usa rechazo S. Validar XSD local no acredita aceptación
ni corrección jurídica del supuesto concreto.

## Hallazgos reproducidos y corregidos

| ID | Baseline 4ce821e | Corrección / prueba nueva | Estado local |
|---|---|---|---|
| A-F01 | verify_chain solo calculaba hash del texto almacenado: podía aprobar XML de importe/identidad distinto | Comparación del XML, hash canónico, identidad/fecha/encadenamiento, destinatario, referencia rectificada, grupos IVA y snapshots; test_a_f01_verifier_* | COMPLETO |
| A-F02 | No respetaba TiempoEsperaEnvio; workers podían emitir en paralelo y una respuesta tardía sobrescribir un lease nuevo | FiscalEndpointState persistente por entorno, CAS de lease_token y fence final; test_a_f02_* | COMPLETO |
| A-F03 | Guard productivo consultaba modo de empresa, pudiendo eludirse para registro PRODUCTION al cambiar empresa a TEST | Guard explícito basado en modo del documento; test_a_f03_* | COMPLETO |
| A-F04 | max_length12 no admitía ACCEPTED_WITH_ERRORS / DUPLICATE_REVIEW | max_length24 y migración; test_a_f04_* | COMPLETO |
| A-F05 | Rechazo de anulación generaba una nueva ALTA | Conserva ANULACION; distingue rechazo previo y ausencia de registro anterior; XSD test_a_f05_* | COMPLETO |
| A-F06 | Cobertura insuficiente de medianoche/año fiscal con persistencia UTC | Prueba cambio de año Europe/Madrid y fecha QR/canónica; test_a_f06_* | COMPLETO |
| A-F07 | cash_session no numérico en rectificación producía ValueError500 | Validación backend y rechazo sin devolución; test_a_f07_* | COMPLETO |
| A-F08 | Objeto outbox cacheado podía permitir corrección después de cambiar estado | Estado releído dentro atomic; test_a_f08_* | COMPLETO |
| A-F09 | INSERT OR REPLACE de SQLite podía eludir triggers UPDATE/DELETE con recursive_triggers desactivado | BEFORE INSERT para claves existentes de factura/líneas/refund/registro/transmisión, incluidas claves únicas; test_a_f09_* (5 tablas) | COMPLETO |
| A-F10 | Respuesta de operación Alta podía aceptarse para envío Anulacion con misma identidad | Valida TipoOperacion además de XSD/identidad; test_a_f10_* | COMPLETO |
| A-F11 | Versión XML estática no reflejaba paquete actualizado | Cada registro nuevo guarda versión real del generador; el XML previo permanece intacto; test_a_f11_* | COMPLETO |
| A-F12 | No se podía subsanar ACCEPTED_WITH_ERRORS | Registro nuevo S sin X y origen conservado; test_a_f12_* | COMPLETO |
| A-F13 | Cambiar productor mal configurado no corregía el payload nuevo porque reutilizaba snapshot antiguo | Identificación actual del SIF en nuevo registro, sin reescribir factura ni XML original; test_a_f13_* | COMPLETO |

## Inventario del módulo y flujos

Modelos: InvoiceSequence, Invoice, InvoiceLine, Refund, FiscalRecord, FiscalOutbox,
FiscalTransmission, FiscalEndpointState. Rutas billing:index/list/detail/pdf/rectify/
reprint; namespace list es alias de index, no pantalla extra. Trabajador send_fiscal.

Servicios públicos: issue_invoice, rectify_invoice, render_pdf, production_guard;
create_record, correct_rejected, annul_record, verify_chain, send_one. Protocol:
canonical_hash, fiscal_date, qr_url, build_xml, validate_xml, soap_envelope,
validate_response, parse_response, response_wait_seconds y verify_record_snapshot.

Servicios transaccionales validan EMPLOYEE para emisión; MANAGER para devolución;
ADMIN para subsanación/anulación. Vistas restringen empleado a facturas propias.
El middleware técnico del coordinador restringe PII Superadmin con aprobación
independiente. La anulación fiscal no sustituye devolución ni debe anunciarse como
anulación económica de una venta real.

Flujo: checkout → factura/líneas → registro/outbox en atomic; impresión/AEAT
fuera de esa transacción. El lease endpoint evita remisión simultánea y conserva
espera; una respuesta vencida queda en transmisión sin cambiar la cola de otro
worker. Configuración de certificado/ruta externa se resuelve con el módulo soporte;
un documento no se envía a un entorno distinto del que tiene congelado.

## Cobertura y límites

Pruebas nuevas: 19; pruebas fiscales existentes:12. Primera ejecución módulo+
auditoría: 31 PASS; la ejecución integrada con aceptación detectó errores transitorios
en módulos en modificación concurrente (hardware.terminal_id pendiente de migración;
NameError Decimal en cash). Se notificaron al coordinador, no se alteraron módulos
ajenos para ocultarlos. El coordinador repite suite final tras integrar.

- Facturas F1/F2, rectificativa total R1/R5, series autorizadas configurables por
  empresa, snapshots, QR/PDF, hash y XSD: COMPLETO en escenario local soportado.
- SOAP, colas, reintentos y respuestas sintéticas: COMPLETO en pruebas locales;
  **validación contra AEAT con certificado: BLOQUEADO**, no ejecutada.
- Impuestos soportados: IVA general S1/01. Regímenes especiales, exenciones,
  inversión, IGIC/IPSI y representación no se implementan ni anuncian como soportados.
- Rechazos por datos que exijan alterar la factura necesitan el flujo legal de
  rectificación revisado por experto. No se permite editar una factura emitida.
- Duplicados quedan DUPLICATE_REVIEW: no se inventa aceptación. Su conciliación
  real exige acuses/consulta AEAT y certificado, actualmente BLOQUEADO.
- Firma/publicación de declaración responsable, revisión normativa experta y
  lectura QR impreso: BLOQUEADO por recursos/responsable externos. El borrador
  no constituye declaración ni valida conformidad productiva.
- verify_chain compara coherencia local; no autentica a un administrador del SO
  capaz de reemplazar la BD completa. Las evidencias externas/backups siguen necesarias.
