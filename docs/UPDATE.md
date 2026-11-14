# Actualización verificada y rollback

No se ejecutan comandos arbitrarios desde Soporte web. El panel expone versión e historial y guía al operador hacia un procedimiento offline. La actualización automática desde Internet no está activada: el responsable obtiene por un canal confiable el ZIP de código y su SHA-256 independiente.

## Formato de paquete

ZIP con `release.json` y archivos de código relativos a la raíz. Ejemplo:

```json
{"version":"0.2.0","files":{"manage.py":"<sha256 de manage.py>"}}
```

Solo admite apps/config/templates/static/scripts/docs y los archivos de distribución permitidos. Rechaza rutas absolutas, `..`, barras Windows, archivos fuera de allowlist, manifiesto incompleto y hash interno/externo incorrectos. No admite `.env`, bases, backups, claves ni `.git`. El hash protege integridad; la autenticidad depende del canal de distribución confiable, no se afirma firma digital inexistente.

## Aplicar

Detenga servidor y todos los workers. Obtenga backup externo y verifique espacio/compatibilidad de migraciones. Ejecute:

```powershell
powershell -File scripts/update.ps1 -Instance C:/BeautyTPV/instance.json -Package D:/Releases/beautytpv-0.2.0.zip -Sha256 <hash verificado>
```

Solicita lock exclusivo, copia cifrada previa, aplica código, ejecuta migrate/check/collectstatic. Registra historial. En error restaura los archivos de código anteriores y conserva la BD actual, incluidos registros fiscales y migraciones ya aplicadas; crea retención de operativa. Nunca hacer rollback de BD automáticamente ni eliminar registros fiscales para volver a una versión anterior. Si las migraciones no son compatibles con el código anterior, mantenga el servicio detenido y aplique una corrección compatible por el productor.

`tests/test_backup.py` verifica manifiestos, path traversal, hash erróneo, aplicación con runner controlado y fallo de migración con rollback de código/BD preservada. Un ensayo real de paquete completo/servicio en el equipo destino sigue siendo necesario; el informe de release identifica la evidencia ejecutada.


## Construir un paquete revisable

```powershell
.venv/Scripts/python scripts/package_release.py --version 0.1.0 --output dist/BeautyTPV-0.1.0.zip
```

Incluye código, pruebas, documentación, estáticos y esquemas AEAT; excluye secretos,
BD y backups. Genera manifest por archivo y SHA256 externo. El coordinador ejecutó
un paquete completo en una copia temporal del código y una instancia sintética:
actualización/migraciones/check/collectstatic correctos, seguidos de backup/restore
CLI correctos. Esto no verifica una actualización de un negocio en producción.


## Límites comprobados en la auditoría

El preflight valida rutas, SHA256 y dependencias fijadas antes de escribir. Un entorno incompatible aborta; no se promete rollback automático del venv. El rollback de código cubre también errores parciales de IO y `release.json`, preservando la BD y el hold. La versión se obtiene del paquete instalado o `release.json`. El historial y las evidencias están en `AUDITORIA_COMPLETA.md`; la comprobación remota de un catálogo de versiones no se ofrece en V1.


## Ensayo de consolidación

`evidence/consolidation-update.json` procede de un paquete completo aplicado realmente en copia temporal con factura: preflight, backup cifrado, migrate/check/collectstatic y huellas conservadas. No representa una actualización del salón/equipo ni cambia la versión comercial por el identificador sintético de prueba.
