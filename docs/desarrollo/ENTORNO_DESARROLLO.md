# Entorno de desarrollo en Windows

Requisitos: Python3.12 o posterior, Git, acceso autorizado al repositorio y Chromium para E2E. Scripts/eventos de escritorio requieren Windows. Sin Docker ni PostgreSQL obligatorios. [Instalación del usuario](../instalacion/INSTALACION_WINDOWS.md) es otro procedimiento.

## Preparar Python

Desde una copia nueva:

```powershell
python --version
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.venv\Scripts\python.exe -m pip install --no-deps -e ".[dev]"
.venv\Scripts\python.exe -m pip check
```

No necesita activar la venv: se utiliza su ejecutable explícito. El lock fija el entorno observado y pyproject declara requisitos/grupos. No cambie versiones sin revisar pruebas, licencias y compatibilidad. La instalación puede necesitar red de paquetes; no versionar credenciales de índices privados.

## Tres configuraciones distintas

| Perfil | Configuración y servidor | Datos y uso |
|---|---|---|
| Desarrollo | config.settings, variables explícitas, DEBUG1 y runserver loopback | SQLite DEV separada; depuración sin datos reales |
| DEMO Windows | config.demo_settings, config.json privado, DEBUGFalse y Waitress127.0.0.1:8000 | Semilla sintética, solo simulador, sin AEAT; no reutilizar como negocio |
| Operativa | config.settings mediante scripts de instancia, DEBUG0 y Waitress detrás de TLS/proxy confiable | Secretos externos; gates fiscales/despliegue pendientes antes de aprobar producción |

`.env.example` **no se carga automáticamente**. Copiarlo a .env no establece variables. No hay dependencia python-dotenv. Los scripts operativos cargan instance.json mediante lista de claves permitidas; la DEMO usa otro formato y nunca consume una configuración productiva.

## DB DEV aislada

En la raíz del repositorio, las variables siguientes afectan a esta sesión PowerShell y sus hijos:

```powershell
$devDirectory = Join-Path $env:LOCALAPPDATA 'BeautyTPV-DEV'
New-Item -ItemType Directory -Path $devDirectory -Force | Out-Null
$env:DJANGO_SETTINGS_MODULE = 'config.settings'
$env:BEAUTYTPV_DB = Join-Path $devDirectory 'dev.sqlite3'
$env:BEAUTYTPV_DEBUG = '1'
$env:BEAUTYTPV_ALLOWED_HOSTS = '127.0.0.1,localhost'
$env:BEAUTYTPV_FISCAL_ENVIRONMENT = 'TEST'
$env:BEAUTYTPV_AEAT_CERTIFICATE = ''
$env:BEAUTYTPV_AEAT_PRIVATE_KEY = ''
$env:BEAUTYTPV_SECRET_KEY = & .venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(64))"
.venv\Scripts\python.exe manage.py migrate --noinput
.venv\Scripts\python.exe manage.py bootstrap
.venv\Scripts\python.exe manage.py createsuperuser
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

Puerto8001 evita competir con DEMO8000. Use carpeta DEV nueva si no quiere reutilizar datos. Bootstrap es idempotente: empresa/plano/caja, sin usuarios ni catálogo fake. Createsuperuser es interactivo y asigna Superadmin; entre con contraseña y casilla marcada. Cree inferiores desde Equipo.

Custodie el secreto y manténgalo estable si quiere conservar sesiones entre arranques. No copiar a documentos/chats. DEBUG y el secreto de desarrollo del módulo base no son adecuados para producción. TEST tampoco significa offline: el entorno DEV puede enviar si configura certificados/worker. Para trabajo sin comunicaciones use la DEMO y no active diagnóstico AEAT.

## DEMO sin alterar DEV ni negocio

```powershell
.venv\Scripts\python.exe scripts\windows_demo.py setup --no-gui --no-browser
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\crear_acceso_directo.ps1
```

Se crea carpeta externa, migraciones, semilla y cuatro roles con secretos aleatorios y ACL. No se muestran aquí los valores. Abra los accesos o consulte [Arranque DEMO](../instalacion/ARRANQUE_DEMO.md). La semilla verifica perfil, marcador y ruta antes de mutar.

## Editor y Chromium

Seleccione `.venv\Scripts\python.exe` en el editor y respete .editorconfig. Bootstrap/HTMX son vendor locales, sin CDN necesario. No normalice bytes AEAT/vendor preservados por .gitattributes.

```powershell
.venv\Scripts\python.exe -m playwright install chromium
```

Es preparación de pruebas, no driver productivo. Si red/antivirus impiden descargar o ejecutar, registrar bloqueo sin desactivar controles corporativos. [Pruebas](PRUEBAS.md) detalla ejecución/plataformas.
