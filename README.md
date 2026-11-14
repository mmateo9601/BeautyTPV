# BeautyTPV

Estado de consolidación: [aceptación y matrices completas](docs/FINAL_ACCEPTANCE.md). **836 pruebas locales aprobadas**; producción fiscal y validación física siguen bloqueadas externamente.

TPV local para un centro de estética: una instalación y una base SQLite por empresa. Django 5.2, Bootstrap 5 y HTMX vendorizados; servidor LAN y navegadores de puestos. No SaaS ni portal de clientes V1.

## Arranque de desarrollo

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py bootstrap
.venv/Scripts/python manage.py createsuperuser
.venv/Scripts/python manage.py runserver
```

Abra [BeautyTPV local](http://127.0.0.1:8000). El primer usuario se crea interactivamente, sin contraseña predeterminada. Acceda con usuario, contraseña y la opción contraseña administrativa; configure empleados y PIN desde Equipo. La semilla crea secciones A/B, puestos A1–A3/B1 y caja, sin catálogo ficticio ni usuarios.

**La instalación comienza en TEST. Sus documentos de prueba no tienen validez fiscal productiva.** La integración fiscal usa esquemas oficiales, huella/QR y transporte SOAP; la remisión real requiere certificado y evidencias externas. No declare conformidad ni pruebas físicas basándose en los simuladores.

## Instalación y operación

Siga [INSTALL](docs/INSTALL.md), [manual de usuario](docs/USER_MANUAL.md) y [Superadmin](docs/SUPERADMIN.md). Para instalación aislada:

```powershell
powershell -File scripts/install.ps1 -InstanceDirectory "$env:LOCALAPPDATA/BeautyTPV"
powershell -File scripts/start.ps1 -Instance "$env:LOCALAPPDATA/BeautyTPV/instance.json" -Development
```

`-Development` sirve HTTP en loopback para pruebas. Producción requiere HTTPS y configuración segura, detallados en el manual. Los secretos quedan en el directorio externo de instancia. No comparta SQLite por SMB/NFS: solo el servidor Django accede al archivo local.

## Verificación

```powershell
.venv/Scripts/python manage.py check
.venv/Scripts/python manage.py makemigrations --check --dry-run
.venv/Scripts/python -m pytest -q
.venv/Scripts/ruff check .
.venv/Scripts/ruff format --check .
```

Las evidencias y límites definitivos están en [IMPLEMENTATION_STATUS](docs/IMPLEMENTATION_STATUS.md), [ACCEPTANCE_MATRIX](docs/ACCEPTANCE_MATRIX.md), [VERIFACTU_COMPLIANCE](docs/VERIFACTU_COMPLIANCE.md) y [RELEASE_REPORT](docs/RELEASE_REPORT.md). No se sustituye el informe por esta introducción.

Auditoría anterior contra `4ce821e`: [matriz integral y evidencias](AUDITORIA_COMPLETA.md). 697 pruebas locales aprobadas; producción fiscal y hardware físico siguen sujetos a los gates externos documentados.
