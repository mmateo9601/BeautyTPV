> Guía canónica actual: [instalacion/INSTALACION_WINDOWS.md](instalacion/INSTALACION_WINDOWS.md). Este documento conserva procedimientos y evidencias históricos; consulte la guía actual antes de operar.

# Instalación local

Requisitos: Python 3.12 o superior compatible con Django 5.2; este desarrollo se prueba en Windows con Python 3.14. SQLite en disco local fiable; no recurso compartido. Un PC servidor por empresa, navegadores de terminales acceden al servidor. Copie el repositorio de una versión revisada a un directorio local y abra PowerShell.

```powershell
powershell -File scripts/install.ps1 -InstanceDirectory "$env:LOCALAPPDATA/BeautyTPV"
```

El instalador crea `.venv`, instala dependencias, crea una configuración **JSON externa al repositorio** con claves aleatorias independientes, aplica migraciones, ejecuta semilla sin credenciales y `collectstatic`, y solicita el primer Superadmin interactivamente. No sobrescribe una instancia ya existente. En Windows quita herencia de ACL del archivo de configuración y concede acceso al usuario instalador; compruebe también los permisos del directorio/BD/backups y la cuenta operadora. Guarde una copia de la clave de backup en un lugar protegido separado; sin ella las copias cifradas son irrecuperables.

Para verificar instalación automatizada sobre un directorio nuevo sin crear usuario, con dependencias ya disponibles:

```powershell
.venv/Scripts/python scripts/install.py --instance-dir D:/BeautyTPV-prueba --skip-dependencies --no-user
```

Esto verifica instalación/DB/estáticos; no acredita una descarga de dependencias limpia. El informe de release debe indicar qué variante se ejecutó.

## Arranque y primer uso

```powershell
powershell -File scripts/start.ps1 -Instance "$env:LOCALAPPDATA/BeautyTPV/instance.json" -Development
```

En desarrollo abre [la aplicación](http://127.0.0.1:8000), solo loopback. `service.py` mantiene bloqueo compartido y lanza workers de hardware y operación fiscal/backup; al detenerlo termina sus workers. Para instalar arranque al iniciar sesión sin guardar contraseñas:

```powershell
powershell -File scripts/install-startup.ps1 -Instance "$env:LOCALAPPDATA/BeautyTPV/instance.json"
```

El registro en Programador de tareas es una opción de servicio local por usuario; debe verificarse en el equipo de destino. No se afirma que un servicio Windows físico haya sido instalado en este entorno.

Acceda con contraseña administrativa. Configure empresa/NIF/domicilio/productor, catálogo e impuestos, empleados/PIN y dispositivos. Cliente es una ficha comercial externa, no un rol de acceso.

## Producción LAN

No exponga `runserver`. Use `scripts/start.ps1` sin `-Development`, Waitress en loopback y un proxy HTTPS de la organización con certificado de confianza. Configure `BEAUTYTPV_ALLOWED_HOSTS` en instance.json con el nombre real. La configuración segura exige HTTPS (redirección y cookies Secure); el proxy debe comunicar el esquema por un encabezado confiable y sobrescribir el recibido del cliente. El administrador de la red debe configurar y verificar TLS/proxy/firewall; no activar confianza ciega en proxies públicos. Los estáticos se recopilan en `staticfiles` y se sirven mediante el middleware de estáticos configurado por el proyecto.

No publique un puerto LAN sin TLS en red no confiable. Las claves privadas AEAT se referencian como archivos externos; no se guardan en BD ni logs. Mantenga producción fiscal bloqueada hasta pruebas oficiales y revisión experta documentadas.

## Verificación y límites SQLite

```powershell
powershell -File scripts/check.ps1 -Instance "$env:LOCALAPPDATA/BeautyTPV/instance.json"
```

`check --deploy` puede señalar configuración TLS/HSTS pendiente hasta completar el despliegue. SQLite usa transacciones IMMEDIATE y timeout, un único escritor; las pruebas de concurrencia y límites medidos están en la matriz/release. Incremente capacidad solo tras medir; PostgreSQL es evolución futura, no se usa en V1.


Para un proxy local que sobrescribe `X-Forwarded-Proto`, configure
`"BEAUTYTPV_TRUST_PROXY": "1"` y, si corresponde,
`"BEAUTYTPV_CSRF_TRUSTED_ORIGINS": "https://tpv.nombre-local"` en instance.json.
Mantenga Waitress en 127.0.0.1 y publique solo el proxy HTTPS. Esta opción no
instala ni valida automáticamente el certificado del equipo destino.
