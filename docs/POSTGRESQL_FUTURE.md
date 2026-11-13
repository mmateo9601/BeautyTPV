# Evolución futura de SQLite

No se migra ahora. SQLite reside solo en el disco del servidor. Las pruebas actuales
cubren tres escritores locales concurrentes, no una capacidad sostenida comercial.
Registre latencia de cobro y errores locked en carga real antes de decidir migrar.

Para una futura migración supervisada: detener servidor/workers y adquirir lock de
mantenimiento; backup cifrado e informe de highwatermarks; preparar PostgreSQL con
migraciones equivalentes y restricciones/triggers revisados; exportar con dumpdata
natural keys e importar en destino aislado. Comparar cantidades por tabla, importes
por día/método/IVA, secuencias completas, fingerprints y verify_chain; contrastar
acuses externos y trabajos de impresión. No enviar colas durante la comparación.
Conservar SQLite original de solo lectura y copias; autorizar corte solo tras E01–E16,
restore de prueba y conciliación fiscal. La portabilidad futura de triggers requiere
migraciones específicas PostgreSQL; no está certificada por los tests SQLite actuales.
