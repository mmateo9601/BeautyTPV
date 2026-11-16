# Copias de seguridad y restauración

**Objetivo:** recuperar una instalación sin copiar SQLite en caliente de forma inconsistente ni regenerar documentos fiscales. Backup, verificación y restauración son operaciones diferentes.

| Operación | Qué hace | Permiso / condición |
|---|---|---|
| Generar o descargar desde web | Copia cifrada y registro de operación | Superadmin elevado; autorización BACKUP |
| Verificar desde web | Hash, autenticación y contenido de una copia registrada | Superadmin elevado; BACKUP; no activa mantenimiento |
| Preparar restauración desde web | Verifica copia, muestra diferencia de documentos y activa mantenimiento | Superadmin elevado; BACKUP; confirmación |
| Restaurar SQLite realmente | Verificación, copia previa, reemplazo offline y hold | Cuenta OS autorizada; servicio y trabajadores detenidos |
| Retirar hold | Verifica integridad/cadena local y registra hash del informe externo | Superadmin con contraseña; conciliación real previa y lock exclusivo |

## Preparar la política de recuperación

**Previos:** instancia identificada, clave Fernet externa disponible y destino autorizado con espacio. SQLite y las copias contienen datos personales, aunque el fichero cifrado no permita leerlos sin clave.

1. En Soporte configure intervalo y retención positivos. `operations_worker` aplica la política de copias de forma independiente de errores fiscales; conserva al menos la copia exitosa más reciente cuando está presente.
2. Proteja el directorio de copias y mantenga una copia adicional fuera del equipo bajo la política del negocio. El programa no configura almacenamiento externo ni prueba su custodia automáticamente.
3. Conserve `BEAUTYTPV_BACKUP_KEY` por un procedimiento seguro distinto del archivo `.btpv`. Perder la clave puede impedir recuperar copias. Rotarla sin conservar la anterior impide descifrar sus copias antiguas.
4. Registre periodicidad, responsable y ensayo de restauración. Un archivo existente no demuestra que el negocio pueda recuperarse.

## Crear y verificar una copia

### Desde Superadmin

1. Entre con contraseña y confirme elevación si ha caducado.
2. Autorice una sesión de alcance **Copias de seguridad** con motivo y aprobador válido.
3. En `/soporte/`, solicite **Crear copia cifrada**. Compruebe su aparición en el historial.
4. Use **Verificar copia**. Un éxito confirma la comprobación del archivo registrado; un fallo exige revisar integridad, clave o permisos, sin activar mantenimiento.
5. Descargue la copia solo a un destino autorizado. No publique el archivo ni sus claves en una incidencia.

### Por CLI autorizado

Desde la raíz del código:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings"
powershell.exe -NoProfile -File scripts\backup.ps1 -Instance "C:\BeautyTPV\instancia\instance.json" -Output "D:\CopiasAutorizadas\salon-20261116.btpv"
```

El destino no debe existir: el código no lo sobrescribe. La implementación usa la API `sqlite3.Connection.backup`, verifica `integrity_check`, construye un manifiesto con hash y marcas fiscales, y cifra/autentica mediante Fernet. El CLI informa nombre y SHA256, no la clave.

**Resultado:** `.btpv` cifrado con copia consistente. La operación puede realizarse con el servicio activo; restaurar o actualizar no puede.

## Preparar desde la web no equivale a restaurar

En `/soporte/restauracion/`, seleccione una copia registrada y escriba `PREPARAR RESTAURACION`. La pantalla verifica y compara el último identificador documental de la copia con el actual; el indicador orienta sobre riesgo de pérdida, no sustituye una conciliación completa. Activa mantenimiento y registra la preparación. No reemplaza una base viva ni para los procesos del sistema.

## Restaurar offline

**Riesgo:** una copia anterior puede omitir facturas, acuses o entregas que ya ocurrieron. Reponerla y enviar sus colas automáticamente podría duplicar operaciones o dejar historia inconciliada.

1. Cierre terminales y detenga servicio, todos los trabajadores y bridges mediante el mecanismo registrado del despliegue. Conserve acuses, copias y evidencia de operaciones posteriores al punto de recuperación.
2. Verifique que la instancia y la clave corresponden al salón. Conserve su configuración externa y las versiones de código necesarias para interpretar el backup.
3. Ejecute:

   ```powershell
   $env:DJANGO_SETTINGS_MODULE = "config.settings"
   powershell.exe -NoProfile -File scripts\restore.ps1 -Instance "C:\BeautyTPV\instancia\instance.json" -Archive "D:\CopiasAutorizadas\salon-20261116.btpv" -Confirm "RESTORE OFFLINE"
   ```

   El wrapper pasa `--offline` al CLI. La alternativa Python es `scripts/restore.py --instance ... --archive ... --offline --confirm "RESTORE OFFLINE"`.
4. La operación autentica/descifra y comprueba hash e integridad. Obtiene lock exclusivo de ciclo de vida, crea una copia cifrada de la base anterior si existe, reemplaza desde un archivo preparado y crea `db.sqlite3.fiscal-restore-hold`.
5. Si el lock indica servicio activo, detenga realmente los procesos; no borre el `.service.lock` para eludirlo. El archivo de lock por sí solo no representa un proceso vivo.
6. Mantenga la operativa retenida. Concilie todos los documentos, secuencias, huellas, acuses y trabajos posteriores a la copia. Un ticket pudo imprimirse sin acuse; un registro pudo llegar a AEAT antes del corte. No invente aceptaciones ni borre historia para cuadrarla.

**Resultado:** SQLite restaurada íntegra y operativa/remisión/impresión retenidas hasta una conciliación declarada y auditada.

## Retirar la retención tras conciliar

Con servicio detenido, prepare un informe externo no vacío y custodiado por el responsable. Cargue la instancia mediante el lector permitido y ejecute el comando existente:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings"
.venv\Scripts\python.exe -c "from scripts.runtime import load_instance; load_instance(r'C:\BeautyTPV\instancia\instance.json'); from django.core.management import execute_from_command_line; execute_from_command_line(['manage.py','reconcile_restore','--username','superadmin_responsable','--evidence',r'C:\EvidenciasProtegidas\conciliacion.txt','--confirm','RECONCILED WITH AEAT'])"
```

Sustituya el usuario por el Superadmin autorizado. El comando pide su contraseña, exige lock exclusivo, revisa integridad y cadena, registra SHA256 del informe y retira el hold. **No verifica automáticamente que el informe humano concuerde con AEAT.** Si no existe evidencia suficiente, no retire la retención.

Reinicie por el procedimiento registrado y pruebe caja, facturas y colas antes de reabrir. No aplique este procedimiento a la DEMO para fingir una conciliación oficial; su remisión permanece deshabilitada por configuración.

## Evidencias y errores

Fuentes: `apps/support/operations.py`, `scheduler.py`, `views.py`, `scripts/backup.py`, `restore.py` y `reconcile_restore`. Pruebas: `tests/test_backup.py`, `test_audit_ops.py` y `test_concurrency.py`; [ensayo CLI histórico](../evidence/consolidation-upgrade-recovery.json). La verificación realizada en esta fase figura en [DOCUMENTATION_AUDIT](../DOCUMENTATION_AUDIT.md). Véase [SOLUCION_PROBLEMAS](SOLUCION_PROBLEMAS.md) para claves, permisos, corrupción y locks.
