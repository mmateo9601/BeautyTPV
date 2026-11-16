# Instalación de BeautyTPV en Windows

Esta guía prepara una instalación independiente por empresa con el código actual `0.1.0`. No hay instalador gráfico comercial ni servicio de Windows que se registre automáticamente. Existen scripts de instalación y accesos directos para la DEMO. La producción fiscal continúa sujeta a los bloqueos de [VERI*FACTU](../integraciones/VERIFACTU.md).

## Elegir el entorno antes de instalar

| Objetivo | Procedimiento | Datos y red |
|---|---|---|
| Aprender o mostrar el producto | [Arranque DEMO](ARRANQUE_DEMO.md) | SQLite separada, datos sintéticos, localhost, TEST sin remisión |
| Desarrollar | [Entorno de desarrollo](../desarrollo/ENTORNO_DESARROLLO.md) | Base aislada; `runserver` solo para desarrollo |
| Preparar un salón real | Esta guía y [despliegue local](DESPLIEGUE_LOCAL.md) | Una empresa, SQLite local, Waitress detrás de HTTPS; sin aprobación fiscal automática |

No copie la base DEMO ni su archivo de credenciales a una instalación real.

## Requisitos y preparación

**Objetivo:** disponer del intérprete, código autorizado y directorio privado de instancia.

**Previos:** Windows 10/11, Python de 64 bits compatible con `requires-python >=3.12`, permisos de escritura en código e instancia y navegador actualizado. El equipo efectivamente probado se identifica en [la guía DEMO](../GUIA_WINDOWS_DEMO.md); no se acredita aquí una prueba física en todos los Windows. Confirme espacio para código, SQLite, estáticos, temporales de restauración y copias. No hay umbral universal de hardware certificado.

1. Obtenga el código y los avisos de su versión por el canal del proyecto; cumpla AGPL-3.0-only y las licencias de terceros al redistribuir. Véase [SOURCE_CODE](../../SOURCE_CODE.md).
2. Sitúelo, por ejemplo, en `C:\BeautyTPV\app`. Reserve `C:\BeautyTPV\instancia` para SQLite, configuración y copias; fuera del repositorio y sin compartir SQLite por red.
3. Abra PowerShell en la carpeta del código. Compruebe el intérprete:

   ```powershell
   python --version
   ```

4. Si prepara el entorno por separado:

   ```powershell
   python -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.lock.txt
   .venv\Scripts\python.exe -m pip install --no-deps -e ".[dev]"
   .venv\Scripts\python.exe -m pip check
   ```

El lock contiene también herramientas de pruebas. Esta documentación no añade dependencias ni modifica sus versiones.

## Crear la instancia

**Riesgo:** elegir otra carpeta de empresa no convierte BeautyTPV en multiempresa. Cada negocio requiere su instalación, configuración y base separadas.

1. Desde la raíz del código ejecute:

   ```powershell
   $env:DJANGO_SETTINGS_MODULE = "config.settings"
   powershell.exe -NoProfile -File scripts\install.ps1 -InstanceDirectory "C:\BeautyTPV\instancia"
   ```

2. El instalador crea o reutiliza `.venv`, instala el lock, genera `instance.json` externo con secretos aleatorios y configuración inicial TEST, aplica migraciones, ejecuta `bootstrap`, comprobaciones y recopilación de estáticos.
3. Cree el Superadmin cuando `createsuperuser` lo solicite. No existe contraseña predeterminada. Si necesita posponerlo, el CLI equivalente admite:

   ```powershell
   .venv\Scripts\python.exe scripts\install.py --instance-dir "C:\BeautyTPV\instancia" --no-user
   ```

4. Proteja toda la carpeta de instancia y sus copias mediante los permisos de Windows acordados con el responsable. El instalador aplica ACL a `instance.json`; no sustituye una revisión de permisos de todo el equipo ni cifra globalmente SQLite.
5. Conserve la clave de backups por un medio seguro independiente de las copias. No publique `instance.json` ni copie sus valores a incidencias, capturas o Git.

**Resultado esperado:** configuración externa, SQLite migrada, plano A/B y caja inicial, sin catálogo ficticio ni usuarios comerciales de ejemplo. Si `instance.json` ya existe, el instalador rechaza sobrescribirlo: use actualización o recuperación según corresponda.

## Crear después el primer Superadmin

Los comandos `manage.py` no leen automáticamente `instance.json` ni `.env`. Use una consola con el perfil normal explícito `config.settings`; no herede `config.demo_settings` de una sesión de desarrollo. El lector de instancia valida claves, pero conserva un `DJANGO_SETTINGS_MODULE` ya establecido. Desde la raíz cargue la configuración con el lector permitido y ejecute el comando:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings"
.venv\Scripts\python.exe -c "from scripts.runtime import load_instance; load_instance(r'C:\BeautyTPV\instancia\instance.json'); from django.core.management import execute_from_command_line; execute_from_command_line(['manage.py','createsuperuser'])"
```

La contraseña se introduce interactivamente, sin argumento de proceso. Entre con la opción de contraseña administrativa y cree usuarios inferiores desde Equipo. Consulte [la guía del Administrador](../manuales/GUIA_ADMINISTRADOR.md).

## Validar y continuar

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings"
powershell.exe -NoProfile -File scripts\check.ps1 -Instance "C:\BeautyTPV\instancia\instance.json"
```

Este script ejecuta `check`, detección de migraciones sin generar archivos y `check --deploy`. Un resultado sin errores no valida certificados AEAT, hardware, TLS ni datos jurídicos del salón. Configure HTTPS y operación según [DESPLIEGUE_LOCAL](DESPLIEGUE_LOCAL.md) antes de ofrecer acceso real.

Los parámetros anteriores proceden de `scripts/install.py`, `install.ps1`, `runtime.py` y `check.py`. Sus ayudas CLI se ejecutaron sin mutar instalaciones durante esta fase. Los ensayos reales históricos de instalación y upgrade están en [las evidencias](../evidence/consolidation-upgrade-recovery.json); la validación independiente actual está en [DOCUMENTATION_AUDIT](../DOCUMENTATION_AUDIT.md).

Errores de intérprete, permisos, configuración o dependencias: [Solución de problemas](SOLUCION_PROBLEMAS.md).
