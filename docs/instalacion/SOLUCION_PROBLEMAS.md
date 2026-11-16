# Solución de problemas operativos y de instalación

**Objetivo:** identificar el incidente sin repetir cobros, alterar historia fiscal ni exponer secretos. Empiece por distinguir DEMO, desarrollo e instalación real. Conserve hora, pantalla, rol, acción y mensaje; no adjunte contraseñas, PIN, PEM, archivo de instancia, tarjetas o datos de clientes.

## Comprobación inicial

1. Confirme qué acceso/script se utilizó y qué instancia corresponde. La DEMO usa su carpeta propia; los scripts normales reciben `--instance` o `-Instance`.
2. Compruebe si el problema afecta a web, DB, dispositivo o fiscalidad. Superadmin elevado consulta `/soporte/`; las acciones técnicas requieren autorización temporal según alcance.
3. Revise diagnóstico y logs saneados. `/health/` distingue DB y supervisión, pero no verifica un cobro ni una impresora física.
4. Registre una incidencia sin PII y las actuaciones. Si hace falta ayuda, use [SUPPORT](../../SUPPORT.md) y acuerde un canal privado apropiado.

## Arranque y configuración

| Síntoma | Verificar / actuación segura | Evitar |
|---|---|---|
| Python o `.venv` no encontrado | Versión `>=3.12`, carpeta correcta y dependencias del lock; recrear accesos si movió el repositorio | Instalar paquetes aleatorios o arrancar otra copia sobre la misma DB |
| Falta SECRET_KEY con DEBUG0 | Cargar el `instance.json` externo correcto mediante los scripts oficiales | Copiar una clave a Git o activar DEBUG en producción |
| Clave de configuración no permitida | Revisar claves admitidas por `scripts/runtime.py`; el JSON es datos, no código | Ejecutar un archivo de configuración como script |
| Puerto8000 ocupado | En DEMO, un segundo inicio propio se reutiliza; para otro proceso se rechaza. Identificar su aplicación y detenerla por su procedimiento | `taskkill /IM python.exe`, matar por puerto sin identificar propietario |
| HTTP redirige a HTTPS en instalación normal | Es el comportamiento con DEBUG0. Revisar proxy/certificado y esquema de confianza | Resolverlo con `runserver` o cookies inseguras productivas |
| Host inválido / error400 | Nombre real en `BEAUTYTPV_ALLOWED_HOSTS`; URL y encabezados del proxy | Host comodín indiscriminado |
| CSRF403 | Cookies, origen HTTPS real, `CSRF_TRUSTED_ORIGINS` y proxy que sobrescribe el esquema | Desactivar CSRF globalmente |
| Sin estilos | `collectstatic` y raíz de estáticos del perfil; permisos de lectura/servidor | Cambiar a un CDN para esconder un despliegue incompleto |
| Servicio web se cierra al caer un worker | Revisar error del trabajador requerido; el supervisor evita operativa parcialmente sana | Reiniciar solo web indefinidamente sin corregir el hijo |

Para una instancia normal, este control usa el JSON externo:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings"
powershell.exe -NoProfile -File scripts\check.ps1 -Instance "C:\BeautyTPV\instancia\instance.json"
```

`manage.py` por sí solo no carga ese JSON ni `.env`. Para DEMO use los accesos o `scripts/windows_demo.py status --no-gui`; sus logs están dentro de la carpeta DEMO.

## Acceso y permisos

| Síntoma | Acción |
|---|---|
| Credencial rechazada | Comprobar usuario, PIN frente a contraseña y casilla correspondiente; no realizar intentos repetidos indiscriminados |
| Bloqueo por intentos | Esperar la ventana de bloqueo o usar desbloqueo autorizado y auditado. El bloqueo por origen tiene control técnico específico |
| Admin/Superadmin entra pero recibe403 | El PIN no eleva. Confirmar contraseña; la elevación y los scopes expiran |
| Superadmin no ve clientes/facturas/informes | Autorizar PII con otro Administrador activo; TECHNICAL no sustituye PII ni permite autoaprobación |
| Sesión deja de servir tras cambio de usuario | Cambio de credenciales/rol/actividad o revocación invalida sesiones. Volver a entrar; reactivar no resucita concesiones antiguas |
| Admin no puede modificar otro Admin/Superadmin | Es una restricción jerárquica. Solo gestiona perfiles inferiores; escalar al responsable autorizado |

## Cuenta, cobro e impresión

1. Si hubo error o pérdida de red al cobrar, **consulte primero la cuenta/factura**. La respuesta del navegador puede perderse después del commit. No cree otra venta para «probar».
2. Ante conflicto de versión, recargue y revise el estado actual antes de editar. En PAYMENT_PENDING use **Volver a editar cuenta**; una cuenta cerrada no admite edición.
3. Si falla la impresora, la venta y factura permanecen. Revise el trabajo persistente; una copia identificada no abre cajón ni vuelve a cobrar.
4. FAILED previo al envío puede tener reintento autorizado. UNKNOWN indica entrega incierta: comprobar físicamente y solicitar copia sin cajón cuando proceda; no reenviar automáticamente.
5. El estado DONE del transporte no garantiza papel. En DEMO es consumo simulado, no prueba física.

Configuración, USB/TCP/serie, codepage y agente remoto: [HARDWARE](../integraciones/HARDWARE.md).

## SQLite, backups y mantenimiento

| Síntoma | Actuación |
|---|---|
| `database is locked` persistente | Revisar transacciones largas, procesos que acceden directamente a SQLite, disco y carga; recopilar evidencia sin repetir cobros. Solo un escritor a la vez |
| Se detecta SQLite en carpeta compartida | Planificar mantenimiento y traslado controlado al disco local del servidor; no seguir compartiendo el fichero entre terminales |
| Backup no descifra o falla verificación | Confirmar clave correcta por canal seguro, archivo íntegro y permisos. Conservar el original; no intentar «reparar» el cifrado |
| Destino de backup ya existe | Elegir nombre nuevo autorizado; la operación no sobrescribe |
| Restore/update indica servicio activo | Detener todos los entrypoints oficiales y bridges. El lock protege el ciclo de vida; no borrar su archivo para forzar acceso |
| Operativa retenida tras restore/update | Consultar el marcador y el procedimiento de conciliación. No retirarlo manualmente ni reescribir secuencias |
| Actualización falla por dependencias | Preparar entorno compatible con el lock; no existe rollback automático de pip/venv |

Procedimientos completos: [SQLITE](../integraciones/SQLITE.md), [BACKUP_RESTORE](BACKUP_RESTORE.md) y [ACTUALIZACIONES](ACTUALIZACIONES.md).

## Fiscalidad

- TEST no es homologación. En la DEMO la remisión se bloquea deliberadamente y no se permite configurar certificados; pendiente en outbox es esperado.
- En instalación normal un fallo de red conserva el registro y programa reintento. REJECTED o ACCEPTED_WITH_ERRORS requiere tratamiento reglamentario; no editar la factura emitida.
- DUPLICATE_REVIEW no se presenta automáticamente como aceptado. Hace falta conciliar la respuesta y la evidencia externa.
- Una devolución de venta se resuelve con rectificativa dentro del alcance soportado; anular un registro fiscal no devuelve dinero al cliente.

Escenario, estados y bloqueos: [VERIFACTU](../integraciones/VERIFACTU.md). No active el guard productivo como medida de diagnóstico.

Los comandos de ayuda y rutas se contrastan con código; las resoluciones no realizadas en un equipo real no se presentan como probadas. Estado de esta fase: [DOCUMENTATION_AUDIT](../DOCUMENTATION_AUDIT.md).
