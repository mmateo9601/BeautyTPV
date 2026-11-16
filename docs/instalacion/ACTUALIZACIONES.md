# Actualizaciones y recuperación de código

**Objetivo:** instalar código revisado preservando documentos fiscales y un camino de recuperación. La aplicación comprueba paquetes locales; no consulta un catálogo remoto de versiones ni actualiza el sistema operativo.

## Qué existe y qué falta para distribuir

`scripts/package_release.py` construye ZIP con `release.json`, lista de archivos y SHA256. `apps/support/updates.py` valida y aplica un paquete offline. Soporte muestra versión/historial y permite comprobar una ruta local más su hash; no ejecuta una consola de comandos ni completa el reemplazo desde el navegador.

La versión procede de `release.json` o metadatos instalados; `0.1.0` en el proyecto no equivale a lanzamiento estable aprobado. Licencia principal, revisión de terceros, gates fiscales/hardware y autorización de publicación siguen el [proceso de release](../../RELEASE_PROCESS.md).

**Límite del empaquetado actual:** la allowlist admite `apps`, `config`, `templates`, `static`, `scripts`, `docs`, `schemas`, `manage.py`, `pyproject.toml`, `requirements.lock.txt`, `README.md` y `.env.example`. Admite además los archivos raíz exactos `LICENSE`, `THIRD_PARTY_NOTICES.md` y `SOURCE_CODE.md`, sin habilitar subdirectorios bajo esos nombres. No incluye automáticamente `.editorconfig`, `crear_acceso_directo.ps1`, los BAT ni los restantes documentos profesionales de raíz. Que un archivo exista en Git no garantiza que esté en el ZIP. Revise el manifiesto; una futura distribución completa deberá resolver expresamente estos artefactos y sus avisos antes de publicarse. La preparación AGPL amplía solo esos tres nombres legales y conserva los controles de actualización. Revise también la entrega del [código correspondiente](../../SOURCE_CODE.md).

## Comprobar un candidato

**Previos:** paquete obtenido del canal autorizado y SHA256 recibido por un medio verificable, versión/compatibilidad revisadas y copia recuperable. Un hash publicado junto a un ZIP en un canal no confiable no autentica al proveedor.

1. Entre como Superadmin elevado y autorice alcance **Actualización** para la comprobación del candidato.
2. Abra `/soporte/actualizaciones/`. Consulte versión instalada e historial.
3. Indique ruta del ZIP local y SHA256 esperado; ejecute la comprobación.
4. Revise versión y cantidad de archivos. El éxito confirma estructura/hashes, no aprobación de negocio ni seguridad absoluta del código.

El validador rechaza rutas fuera de allowlist, traversal, colisiones de mayúsculas, entradas duplicadas y diferencias entre manifiesto y contenido. La aplicación offline valida destinos antes de escribir, incluyendo enlaces y la protección de la SQLite.

## Construir un paquete para revisión interna

Desde una revisión de código controlada:

```powershell
.venv\Scripts\python.exe scripts\package_release.py --version 0.1.0 --output dist\BeautyTPV-0.1.0.zip
```

El identificador es un ejemplo alineado con los metadatos actuales: no cree una etiqueta o release público por ejecutar este comando. El script genera también `.zip.sha256`. Inspeccione el contenido, los avisos de terceros y las exclusiones anteriores. `dist/` no debe contener secretos ni bases reales.

## Aplicar offline

**Riesgo:** una migración puede ser irreversible o incompatible con código anterior. El rollback del programa no deshace automáticamente cambios en la base.

1. Pruebe actualización y recuperación sobre una copia aislada con historia representativa. Compruebe requisitos de dependencias y compatibilidad de migraciones.
2. Avise al negocio, cierre terminales y detenga servicio, trabajadores y bridges por su procedimiento registrado. Mantenimiento web no equivale a parada.
3. Conserve copia cifrada verificable, clave externa, acuses y evidencia fiscal. Disponga de espacio adicional para staging, backup y archivos previos.
4. En PowerShell, desde la raíz:

   ```powershell
   $env:DJANGO_SETTINGS_MODULE = "config.settings"
   $packageHash = (Get-FileHash -LiteralPath "C:\PaquetesAutorizados\BeautyTPV-0.1.0.zip" -Algorithm SHA256).Hash
   # Compare packageHash con el valor recibido del canal verificado antes de continuar.
   powershell.exe -NoProfile -File scripts\update.ps1 -Instance "C:\BeautyTPV\instancia\instance.json" -Package "C:\PaquetesAutorizados\BeautyTPV-0.1.0.zip" -Sha256 $packageHash
   ```

5. El wrapper pasa `--offline`. La implementación obtiene lock exclusivo, prepara y verifica todos los archivos, comprueba las dependencias fijadas y `pip check`, genera backup cifrado previo, reemplaza código y ejecuta `migrate`, `check` y `collectstatic`.
6. Revise el historial `UpdateRun`, logs saneados y versión. Pruebe acceso por roles, cuenta, cobro en entorno de prueba apropiado, factura, colas y backup antes de autorizar la reapertura.

La comprobación de dependencias **no modifica ni restaura el venv**. Si el lock no coincide, aborta antes de escribir: prepare y verifique el entorno compatible mediante un procedimiento técnico aprobado; no asuma una actualización automática de pip.

## Fallo y rollback

- Ante error de reemplazo o de migraciones/check/estáticos, se intentan reponer los archivos de código anteriores, incluido `release.json`; los archivos nuevos sustituidos se retiran cuando procede.
- La base actual se conserva, con los documentos fiscales y las migraciones que ya se aplicaron. No se restaura una SQLite antigua automáticamente.
- Se crea un hold operativo; si falla parte del rollback, el marcador registra archivos pendientes de recuperación.
- Mantenga el servicio detenido si el código anterior no entiende el esquema nuevo. Revise compatibilidad y aplique una corrección validada; no borre migraciones, facturas o secuencias para forzar el retroceso.
- Si requiere recuperar una base, es un procedimiento distinto: [BACKUP_RESTORE](BACKUP_RESTORE.md), con conciliación y controles propios.

**Resultado esperado:** versión instalada coherente, base preservada y reapertura autorizada después de pruebas. Un historial SUCCESS no certifica conformidad AEAT ni hardware.

Fuentes: `scripts/package_release.py`, `update.py`, `update.ps1`, `apps/support/updates.py` y `versioning.py`. Pruebas `test_backup.py`, `test_audit_ops.py` y [actualización real histórica en copia temporal](../evidence/consolidation-update.json). Comprobaciones de esta fase: [DOCUMENTATION_AUDIT](../DOCUMENTATION_AUDIT.md).
