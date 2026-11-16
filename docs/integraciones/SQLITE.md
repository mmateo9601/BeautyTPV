# SQLite: persistencia y operación

BeautyTPV V1 usa Django ORM y una SQLite por instalación/empresa. El fichero permanece en disco local del servidor: navegadores y agentes remotos no comparten la base por SMB/NFS ni abren conexiones SQLite a través de una carpeta de red.

## Configuración efectivamente implementada

| Parámetro | Valor / significado | Fuente |
|---|---|---|
| Motor | `django.db.backends.sqlite3` | `config/settings.py` |
| Ubicación normal | `BEAUTYTPV_DB`; si no se configura, `BASE_DIR/db.sqlite3` | Settings y `scripts/runtime.py` |
| Ubicación DEMO | `<carpeta DEMO>/demo.sqlite3`, con validación de aislamiento | `config/demo_settings.py`, `scripts/demo_config.py` |
| Timeout |20 segundos de espera configurada | `DATABASES.default.OPTIONS.timeout` |
| Transacción | Modo `IMMEDIATE` | `DATABASES.default.OPTIONS.transaction_mode` |
| WAL | No se habilita mediante configuración/migración del proyecto | Ausencia de `journal_mode=WAL` en el arranque soportado |

No se promete que el modo efectivo de una DB manipulada externamente sea siempre DELETE: el código no fuerza `journal_mode` al arrancar. Si un técnico estudia WAL, deberá medir y validar topología, backup/restore y sidecars; no se presenta como una optimización ya activada ni como requisito que el operador deba cambiar.

## Concurrencia sin bloqueos de fila

SQLite tiene un único escritor a la vez. `select_for_update` no es la garantía de serialización de BeautyTPV. Los servicios operativos combinan:

- Transacciones cortas para cuenta, venta, pagos, numeración, factura, registro fiscal y spool.
- Versionado de cuenta y actualizaciones condicionales (CAS) para detectar cambios de otra terminal.
- Restricción de una cuenta activa por puesto y una sesión abierta por caja.
- Claves idempotentes y huella de petición para no formalizar una misma venta dos veces.
- `atomic_retry` para repetir una transacción completa después de rollback ante locked/busy, sin repetir solo una parte ya confirmada.
- Remisión y hardware fuera de la transacción financiera; reclamar trabajo/lease no equivale a mantener un bloqueo de escritura durante la red.

El timeout y el retry no garantizan capacidad ilimitada. No añada llamadas HTTP, impresiones o esperas humanas dentro de `atomic` para «asegurar» una venta.

```mermaid
flowchart LR
    T[Terminales por HTTP/HTTPS] --> S[Servicios Django y validaciones]
    S --> A[Atomic + CAS + idempotencia]
    A --> D[(SQLite local)]
    D --> Q[Outbox y spool confirmados]
    Q --> W[Workers: red e IO fuera de la venta]
```

## Integridad e inmutabilidad

El ORM y los triggers SQLite protegen documentos e historia sellada, con controles UPDATE/DELETE y contra sustitución mediante INSERT OR REPLACE. La numeración y el registro fiscal se generan en la misma unidad financiera. Los cambios de catálogo o datos comerciales futuros no reescriben los snapshots de documentos emitidos.

Esto no cifra SQLite ni aísla a un administrador OS capaz de reemplazar código/esquema/base completa. Requiere ACL, backups y evidencia externa. Las migraciones de ampliación deben preservar restricciones y triggers; «arreglar» datos borrando facturas invalida las garantías del sistema.

## Copia consistente, restauración y locks

1. Use la API de backup implementada; no copie únicamente un fichero vivo y suponga que ya es consistente.
2. La copia usa `sqlite3.Connection.backup`, revisa integridad, captura migraciones/marcas fiscales y produce un sobre cifrado/autenticado con Fernet.
3. El servicio y los entrypoints oficiales mantienen lock compartido de ciclo de vida. Restore/update exige exclusivo y rechaza procesos activos que respetan ese contrato.
4. Un proceso ajeno que escribe SQLite directamente puede ignorar ese lock. No está soportado; coordine todos los escritores antes del mantenimiento.
5. Restore comprueba y prepara el reemplazo, conserva copia previa y elimina sidecars `-wal`/`-shm` solo dentro del procedimiento offline controlado. No convierta esas líneas en una instrucción manual de borrado con la aplicación activa.
6. El hold posterior impide reanudar sin conciliación. Conserve acuses y evidencias fiscales/impresión que pudieron completarse antes del corte.

Pasos autorizados, CLI y confirmaciones: [BACKUP_RESTORE](../instalacion/BACKUP_RESTORE.md). Actualizaciones y rollback solo de código: [ACTUALIZACIONES](../instalacion/ACTUALIZACIONES.md).

## Medición y límites observados

El [benchmark local histórico](../evidence/audit-sqlite-benchmark.json) realizó100 ventas sintéticas en1, 3 y 6 procesos:10, 30 y 60 éxitos, cero errores y conteos/cadena coherentes. Sus p95 fueron0,1792 / 0,7839 / 1,8796 segundos para el flujo medido. No incluye una LAN comercial, AEAT, impresora física ni una jornada sostenida.

El criterio interno documentado para revisar capacidad es p95 superior a 2 s con carga representativa o locked persistentes, después de descartar IO dentro de transacciones/configuración incorrecta. Es un disparador de revisión, no una capacidad comercial certificada de seis terminales ni un límite oficial de SQLite.

Pruebas relevantes: `tests/test_concurrency.py` ejecuta procesos independientes, dobles cobros y muerte antes de commit; `test_audit_backend.py` cubre retry y límites; pruebas fiscales/hardware verifican historia y spool. Los resultados de la ejecución actual pertenecen a [DOCUMENTATION_AUDIT](../DOCUMENTATION_AUDIT.md), no se deducen del número histórico de tests.

## Evolución a PostgreSQL

Es futura, no implementada ni certificada. El uso de ORM no elimina la necesidad de revisar constraints, triggers e idempotencia para otro motor. El procedimiento propuesto es preparar destino aislado, detener escritores, backup y exportación controlados, comparar conteos/importes/secuencias/huellas/colas, conservar SQLite original y autorizar corte solo tras pruebas y conciliación.

No cambie ahora el motor ni ejecute una importación sobre una base fiscal viva por seguir esta sección. Véanse [POSTGRESQL_FUTURE](../POSTGRESQL_FUTURE.md), [modelos](../arquitectura/MODELOS_DATOS.md) y [decisiones](../arquitectura/DECISIONES_TECNICAS.md).
