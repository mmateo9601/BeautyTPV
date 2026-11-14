# Copias cifradas y recuperación

La copia usa `sqlite3.Connection.backup`, comprueba `PRAGMA integrity_check` y cifra un sobre JSON completo mediante Fernet (cifrado autenticado). Incluye SHA-256 de la base, versión, migraciones y máximos de ID fiscal para conciliación. No es una copia del fichero vivo sin coordinación SQLite. La clave de 32 bytes codificada Fernet se encuentra en `BEAUTYTPV_BACKUP_KEY`, cargada de la configuración externa; nunca se imprime ni se incluye en el backup.

## Crear y comprobar

Desde Soporte, confirme contraseña, autorice alcance BACKUP y pulse Crear copia cifrada. Se registra nombre/hash/actor y auditoría. La descarga cifrada requiere la misma autorización. El worker `operations_worker` aplica el intervalo y retención configurados; solo expira copias automáticas registradas, nunca copias manuales ni previas a actualización. El directorio se configura con `BEAUTYTPV_BACKUP_DIR`; el responsable debe duplicar copias fuera del disco servidor y comprobar periódicamente recuperación.

```powershell
powershell -File scripts/backup.ps1 -Instance C:/BeautyTPV/instance.json -Output D:/Copias/centro-20261113.btpv
```

Destino existente se rechaza. No copie claves junto al archivo cifrado. Una copia cifrada puede contener datos personales aunque no sean visibles sin clave; aplique retención y custodia.

## Restauración asistida offline

1. Cierre terminales y detenga servidor, bridge y TODOS los workers. Los entrypoints oficiales toman un bloqueo compartido del ciclo de vida; restore/update solicitan exclusivo y rechazan servicios aún activos. Procesos ajenos que escriban directamente SQLite no respetan este contrato: no están soportados.
2. Preserve acuses/estado AEAT actuales y determine qué registros se emitieron después de la copia. La base antigua se conserva además como copia cifrada antes del reemplazo.
3. Ejecute con confirmación explícita:

```powershell
powershell -File scripts/restore.ps1 -Instance C:/BeautyTPV/instance.json -Archive D:/Copias/centro-20261113.btpv -Confirm "RESTORE OFFLINE"
```

4. Se autentica/descifra la copia y se verifica hash/integridad antes del reemplazo. Se crea `db.sqlite3.fiscal-restore-hold`; quedan bloqueadas remisión, impresión y operaciones de venta hasta conciliación. La interfaz HTTP no sustituye una base viva.
5. Concilie con los acuses AEAT y copias externas todos los documentos y secuencias posteriores al punto restaurado. No borrar ni reescribir registros emitidos; no remitir automáticamente trabajos restaurados que pudieron completarse antes de la caída. Si no hay evidencia suficiente, la retención permanece y requiere intervención experta.
6. Guarde informe externo de conciliación, cargue variables de instancia y ejecute `manage.py reconcile_restore --username <superadmin> --evidence <informe> --confirm "RECONCILED WITH AEAT"` con servicio detenido. Solicita contraseña, exige Superadmin, integridad y cadena local; registra hash del informe y retira la retención. **La comprobación local no valida automáticamente que el informe humano concuerde con AEAT.**
7. Reinicie y pruebe caja, facturas y colas antes de reabrir el centro.

Pruebas automatizadas en `tests/test_backup.py`: copia cifrada/restauración en DB nueva, corrupción/clave errónea, confirmación offline, exclusión de servicio, copia previa y retención fiscal. Ensayo operacional periódico debe constar con fecha, responsable y evidencias.


## Verificar sin restaurar

La acción Verificar de una copia en Soporte exige elevación y BACKUP. Verifica SHA256, cifrado y contenido/integridad; audita éxito/fallo sin mantenimiento ni reemplazo SQLite. El logo PNG se guarda en SQLite y queda incluido en la copia. Preparar restauración conserva el procedimiento offline/lock/hold/conciliación descrito antes.
