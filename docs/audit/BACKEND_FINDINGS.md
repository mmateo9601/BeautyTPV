# Auditoría operativa y correcciones integradas

Referencia: `4ce821e`. El coordinador terminó la integración tras los límites de cuota del especialista. Evidencia principal: `tests/test_audit_backend.py`, `tests/test_audit_forms.py`, `tests/test_concurrency.py` y JUnit definitivo.

- Se conectaron PAYMENT_PENDING/resume, notas, filtros por categoría, venta rápida configurable y terminal de cobro persistente. El carrito no se puede editar durante el cobro ni después del cierre.
- Se validan identificadores, decimales finitos y extremos, límites por componente y total agregado antes de persistir. Las entradas inválidas no producen ventas parciales ni errores 500.
- Retry SQLite repite la transacción completa después del rollback; no se usa bloqueo de fila como garantía. Concurrencia y muerte real de proceso verifican factura/alta/spool únicos.
- Mantenimiento y hold de restauración impiden operar. Pago efectivo exige caja abierta actual; tarjeta puede asociarse a una sesión sin incrementar efectivo.
- Configuración singleton, zona horaria IANA y series distintas se validan. Secciones tienen mantenimiento completo con protección de historial.
- Informes consultan snapshots emitidos, rectificativas y cancelaciones; filtros seleccionan operaciones completas y desglosan métodos/IVA/empleados. CSV neutraliza fórmulas.
- Cancelaciones incorporan fecha/actor. La migración histórica solo recupera evidencia de auditoría existente: datos desconocidos se advierten, no se fabrican.
- Triggers impiden cambios y REPLACE sobre historial sellado. Empleado ve cajas activas y cierres propios; superiores conservan supervisión.

Verificación positiva: formularios HTTP crean/modifican datos, cobran, rectifican, mueven y cierran caja. La matriz de permisos usa registros reales y pruebas negativas separadas. No se consideran suficientes archivos, botones o respuestas 404.

Límites externos: datáfono/banco, equipos LAN reales y adecuación fiscal de la empresa no se han validado. Los escenarios de datos son sintéticos.
