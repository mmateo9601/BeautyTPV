# ADR 003 — Fiscalidad y efectos externos verificables

Estado: aceptada como política de seguridad; conformidad fiscal NO VERIFICADA.

Facturas, líneas, registros fiscales y auditoría append-only tras emitir. Cambios posteriores mediante nuevos documentos fiscalmente válidos, nunca edición o borrado. Importes Decimal, snapshots y series controladas en transacción. VERI*FACTU usa exclusivamente documentación oficial versionada, XSD/WSDL y algoritmo de huella/QR oficiales. Implementación no se declara conforme sin pruebas contra AEAT y revisión experta.

Outbox persistente transmite mediante SOAP/autenticación real fuera de la transacción. Respuestas y errores se conservan; timeout no autoriza renumerar. Producción bloqueada hasta validación; modo TEST visible y simuladores aislados. No afirmar aceptación por fixtures. QR debe apuntar entorno oficial correspondiente, nunca inventar evidencia de cotejo.

Hardware ESC/POS y cajón mediante bridge autenticado, cola persistente y estados que distinguen fallo de entrega incierta. Copias explícitas no repiten venta ni abren cajón. Prueba física requiere impresora/cajón real y ficha modelo/firmware; simulador prueba protocolo y resiliencia pero no legibilidad, apertura ni lectura QR física.
