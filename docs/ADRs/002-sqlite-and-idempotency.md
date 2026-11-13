# ADR 002 — Concurrencia e integridad SQLite

Estado: aceptada para implementación inicial; evidencia de carga pendiente.

DB en disco local del servidor; terminales solo HTTP. Transacciones cortas Django atomic y SQLite IMMEDIATE para operaciones de escritura si soportado por configuración Django. busy_timeout acotado; WAL si supera pruebas en plataforma. No usar select_for_update como serialización. Constraints únicos para ticket activo/puesto, caja activa, venta/ticket, clave idempotente, número fiscal y trabajo original de impresión.

Versionado entero y UPDATE condicional impiden actualizaciones perdidas; número y cadena se reservan bajo escritura exclusiva SQLite dentro de la misma transacción que factura/venta/outbox. Reiniciar transacción completa tras SQLITE_BUSY con reintentos acotados e idempotencia; nunca reintentar un efecto bancario o cajón como consecuencia. Claves de idempotencia persistentes con huella de petición distinguen repetición de uso indebido.

Pruebas deben usar varios procesos/conexiones sobre archivo real; rollback a mitad de emisión no consume número ni crea venta parcial. Backups con API sqlite3.backup y recuperación offline con reconciliación fiscal. ORM portable a PostgreSQL, sin migración ahora.
