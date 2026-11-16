> Guía canónica actual: [integraciones/VERIFACTU.md](integraciones/VERIFACTU.md). Este documento conserva procedimientos y evidencias históricos; consulte la guía actual antes de operar.

# Trazabilidad fiscal — BeautyTPV

Estado: implementación local verificable; **NO AUTORIZADA PARA PRODUCCIÓN**. No se ha remitido ningún registro a AEAT ni se ha probado un certificado cliente. Requiere revisión fiscal experta y declaración responsable real del productor antes de su puesta en servicio.

## Fuentes oficiales consultadas 13-11-2026

- [Índice técnico AEAT](https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu/informacion-tecnica.html).
- [WSDL oficial](https://prewww2.aeat.es/static_files/common/internet/dep/aplicaciones/es/aeat/tikeV1.0/cont/ws/SistemaFacturacion.wsdl).
- [Esquemas oficiales](https://www.agenciatributaria.es/AEAT.desarrolladores/Desarrolladores/_menu_/Documentacion/Sistemas_Informaticos_de_Facturacion_y_Sistemas_VERI_FACTU/Esquemas_de_los_servicios_web/Esquemas_de_los_servicios_web.html).
- [Huella AEAT v0.1.2, 27/08/2024](https://www.agenciatributaria.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/Veri-Factu_especificaciones_huella_hash_registros.pdf). Copia íntegra `schemas/aeat/huella.pdf`; vectores páginas 10–12.
- [QR AEAT v0.5.0, 10/12/2025](https://www.agenciatributaria.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/DetalleEspecificacTecnCodigoQRfactura.pdf).
- [Servicio AEAT v1.0.3](https://sede.agenciatributaria.gob.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/Veri-Factu_Descripcion_SWeb.pdf).

Los XSD/WSDL se conservan sin modificaciones en `schemas/aeat/`; `manifest.json` registra URL y SHA-256. La dependencia XMLDSig se resuelve localmente sin acceso de red y sin habilitar entidades externas. El documento de huella se descargó con verificación TLS mediante el almacén Windows: Python/OpenSSL rechazaba la cadena de www.agenciatributaria.es por algoritmo de CA débil; no se desactivó la verificación TLS.

## Mapeo requisito → implementación → evidencia

| Requisito | Implementación | Evidencia automatizada / limitación |
|---|---|---|
| Factura simplificada/completa | billing.services.issue_invoice, snapshots de emisor/destinatario/líneas, series S/F y ejercicio | test_invoice_chain_immutable_and_official_xsd; simplificada limitada conservadoramente a 400 EUR; completa exige NIF/domicilio |
| Rectificación por diferencias | rectify_invoice crea R5 para F2 o R1 para F1, referencia original, importes negativos, Refund | test_refund_preserves_original_and_schema; devolución total, no parcial; supuesto R1 requiere revisión experta del motivo |
| Numeración y atomicidad | secuencia incremento SQL dentro de atomic de checkout | integración principal debe verificar doble terminal; no se usa select_for_update |
| Inmutabilidad | managers/modelos y triggers SQLite UPDATE/DELETE en facturas/líneas/refunds/registros/transmisiones | tests ORM; los administradores del fichero/servidor siguen pudiendo manipularlo: proteger SO y backups |
| Alta/anulación | XML conforme a SuministroLR/SuministroInformacion | alta y rectificativa validadas XSD local; anulación expuesta a servicio admin, no sustituye devolución |
| Huella exacta | canonical_hash UTF-8 SHA-256 hexadecimal mayúsculas, orden oficial alta/anulación | test_official_aeat_hash_vectors: los tres vectores oficiales coinciden |
| Encadenamiento | previous único por registro, canonical_payload, XML inmutables, verify_chain | tests continuidad; no se reinicia por año/serie |
| QR | cuatro parámetros URL encoding UTF-8, entorno correcto, M y 35 mm en PDF | test_qr_official_url_encoding; lectura física NO VERIFICADA |
| SOAP/mTLS | WSDL endpoints TEST/PRODUCTION, requests cert tuple, TLS verificado, timeout, sin firma XML para remisión VERI*FACTU voluntaria | transporte real preparado; certificado no proporcionado, prueba AEAT BLOQUEADA |
| Outbox | unidad transaccional factura/registro/outbox; lease CAS, IO fuera de atomic, retry mismo registro | test_network_failure_persists_chain; timeout no significa rechazo ni aceptación |
| Estados | ACCEPTED solo para Correcto, ACCEPTED_WITH_ERRORS separado, REJECTED y códigos conservados, duplicados DUPLICATE_REVIEW | test_response_never_assumes_acceptance y test_soap_schema_identity_and_receipt_persistence: XSD de respuesta e identidad exacta antes de aceptar; respuestas de fixtures no atribuidas a AEAT |
| Subsanación | correct_rejected crea registro nuevo con Subsanacion=S y RechazoPrevio=X conforme apartado 9.1.3 servicio AEAT | test_rejected_correction_flags_and_anulacion_xsd valida XSD de subsanación y anulación; mantiene origen; corrección de datos fiscales erróneos requiere flujo adicional revisado: BLOQUEADO para ese supuesto |
| Bloqueo productivo | production_guard exige aprobación explícita, evidencia y datos fiscales/productor | test_production_fail_closed; no se configura aprobación por defecto |

## Configuración y operación

Configurar `CompanySettings` y `settings.FISCAL_PRODUCER` con name/tax_id/installation_id reales. Configurar rutas externas `AEAT_CERTIFICATE` y `AEAT_PRIVATE_KEY`; nunca añadir claves al repositorio. `python manage.py send_fiscal --limit 100` procesa pendientes; sin certificado se conserva RETRY y nunca se inventa aceptación. El emisor de factura en modo TEST queda marcado **PRUEBAS - SIN VALIDEZ FISCAL PRODUCTIVA** en documento y UI. Cambiar el nombre de modo a PRODUCTION no basta para habilitar emisión.

Mantener `FISCAL_RESTORE_HOLD=True` o el marcador `<ruta-base-datos>.fiscal-restore-hold` tras restauración hasta reconciliar números/registros/CSV con AEAT. `send_one` consulta el marcador en cada operación; test_restore_hold_marker_blocks_remission. Mantener backup y export de transmisiones antes y después de incidencias. No reenviar nuevos registros en sustitución de un timeout: el registro original permanece y se reintenta con la misma identidad/huella.

Evidencia local del módulo: `.venv/Scripts/python -m pytest tests/test_fiscal.py -q`: **11 passed**. `ruff check apps/billing apps/verifactu tests/test_fiscal.py` y comprobación de migraciones sin drift. No confundir fixtures SOAP sintéticas con acuses AEAT reales. PDF probado por contenido/snapshots; revisión visual y lectura óptica física siguen pendientes.

## Bloqueos para conformidad

Faltan certificado y autorización para pruebas oficiales, evidencias de aceptación/duplicado/rechazo/subsanación/anulación en AEAT, revisión experta de alcance/regímenes/impuestos y supuestos rectificativos, pruebas físicas de QR, revisión de presentación PDF/ticket de casos límite y firma/publicación de declaración responsable por el productor identificado. El módulo soporta IVA general sujeto S1, régimen 01; no declara soporte de exenciones, inversión de sujeto pasivo, regímenes especiales, IGIC/IPSI ni representación. No habilitar para empresas que requieran esos supuestos.

La declaración responsable **no se emite ni se firma ficticiamente**. El productor deberá preparar documento con su identidad/NIF, producto y versión exacta, componentes, modalidad VERI*FACTU, instalación y fecha, descripción y afirmaciones exigibles tras revisión normativa vigente, firma del representante competente y acceso desde el sistema. El presente mapeo es evidencia técnica parcial, no una declaración de conformidad ni asesoramiento fiscal.


Integridad de fuentes: `test_official_sources_match_pinned_checksums` verifica
cada archivo oficial contra schemas/aeat/manifest.json. .gitattributes impide
conversion de finales de linea de los esquemas en checkouts Windows. Suite final
integrada: 112 pruebas correctas; la prueba de hashes no equivale a aceptacion AEAT.


## Auditoría integral del 14-11-2026

La matriz actual y resultados definitivos están en `../AUDITORIA_COMPLETA.md` y `audit/FISCAL_FINDINGS.md`. Se reforzaron coherencia XML/factura/cadena, espera por endpoint, fencing, subsanaciones de alta/anulación y guard basado en modo inmutable. El alcance implementado es IVA general S1/01, F1/F2 y rectificación total R1/R5; no se ofrecen regímenes especiales ni devoluciones parciales. `DECLARACION_RESPONSABLE_TEMPLATE.md` es borrador sin firma. Sin certificado autorizado, acuses AEAT y revisión experta, el gate productivo sigue BLOQUEADO.
