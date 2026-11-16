# Abrir y administrar la DEMO Windows

**Objetivo:** aprender BeautyTPV sin usar la base principal, remitir facturas ni depender de una terminal durante el uso habitual. El procedimiento completo y las ubicaciones verificadas en el equipo de referencia están en [GUIA_WINDOWS_DEMO](../GUIA_WINDOWS_DEMO.md).

## Qué hace realmente este perfil

| Elemento | Comportamiento |
|---|---|
| Servidor | Waitress en `127.0.0.1:8000`, `DEBUG=False`; no `runserver` |
| Instancia | `%LOCALAPPDATA%\BeautyTPV-DEMO`, separada del código |
| Datos | `demo.sqlite3`, cuatro roles y catálogo/clientes sintéticos |
| Fiscal | TEST fijo, sin certificados ni trabajador fiscal; envío bloqueado antes de transporte |
| Impresión | SIMULATOR; no envío a TCP/USB/serie físicos |
| Navegador | Se abre en `http://127.0.0.1:8000/acceso/` |
| Exposición | Solo localhost, sin abrir firewall ni publicar LAN/Internet |

HTTP y cookies no-Secure son excepciones exclusivas del perfil DEMO de loopback. La configuración normal de producción no se cambia. La DEMO no acredita conformidad fiscal ni una instalación real del salón.

## Crear los accesos una vez

**Previos:** código autorizado, Python y dependencias existentes en `.venv`; escritorio disponible para el usuario de Windows.

1. Si falta el entorno, siga la preparación de [INSTALACION_WINDOWS](INSTALACION_WINDOWS.md), sin crear una instancia comercial para hacer una DEMO.
2. Desde la raíz del repositorio ejecute:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\crear_acceso_directo.ps1
   ```

3. El script resuelve el escritorio real de Windows y crea cinco accesos. No sobrescribe accesos ajenos con el mismo nombre. La opción Bypass afecta solo a ese proceso, no a la política permanente del equipo.

| Acceso | Acción |
|---|---|
| BeautyTPV DEMO | Preparar si es nueva, comprobar, iniciar y abrir navegador |
| Detener BeautyTPV DEMO | Parada cooperativa exclusiva de la instancia |
| Usuarios BeautyTPV DEMO | Abrir el archivo privado de credenciales |
| Cambiar usuarios BeautyTPV DEMO | Confirmar rotación, preservar datos y revocar accesos anteriores |
| Reinicializar BeautyTPV DEMO | Confirmar, detener, archivar la DEMO y crear otra limpia |

Los scripts de raíz `iniciar_beautytpv_demo.bat` y `detener_beautytpv_demo.bat` ofrecen las mismas acciones de inicio/parada. El acceso directo oculta los procesos auxiliares; no instala un servicio automático del sistema.

## Entrar y trabajar

1. Abra **BeautyTPV DEMO**. En una instancia nueva se aplican migraciones y se generan credenciales privadas aleatorias; el primer arranque puede tardar más.
2. Abra **Usuarios BeautyTPV DEMO**. El archivo `credenciales-demo.txt` está fuera del repositorio y protegido para el usuario de Windows y SYSTEM. No hay contraseñas fijas que copiar de esta guía.
3. Use `demo_empleado` o `demo_encargado` con su PIN. Use `demo_admin` o `demo_superadmin` con su contraseña y la casilla **Acceder con contraseña**.
4. Seleccione Terminal DEMO. Para Superadmin, conserve los requisitos de elevación y autorización temporal; PII requiere aprobación de otro Administrador. Consulte [GUIA_SUPERADMIN](../manuales/GUIA_SUPERADMIN.md).
5. Opere con datos sintéticos. La factura indica TEST; el ticket puede llegar a DONE por consumo simulado, sin papel ni cajón físicos.

**Resultado:** el plano se muestra y las cuentas permanecen al cambiar de puesto o reiniciar. Las ventas y documentos TEST son persistentes, no una maqueta.

## Parar, reiniciar y recuperar acceso

1. Para cerrar sesión use la acción de la aplicación. Cerrar una pestaña no detiene Waitress.
2. Para detener la DEMO use **Detener BeautyTPV DEMO**. No se buscan ni matan otros procesos Python por nombre o puerto.
3. Para reiniciar use Detener y luego BeautyTPV DEMO. Un segundo inicio de la instancia identificada reutiliza el proceso; no crea otro servidor.
4. Si olvidó credenciales, abra el archivo privado. Si requiere cambiarlas, use **Cambiar usuarios BeautyTPV DEMO** y confirme. La rotación conserva ventas/cuentas y exige nuevas credenciales en las sesiones anteriores.
5. Para quitar los datos de prueba de la instancia activa use **Reinicializar BeautyTPV DEMO**. Se archiva su carpeta marcada como `BeautyTPV-DEMO-archivada-<fecha>-<id>` y se crea otra. No se borra ni restaura una base principal.

No copie una configuración comercial a esta carpeta. Se rechazan rutas ajenas, archivos sensibles con hardlinks y enlaces/junctions que eludan el aislamiento.

## Soporte y alcance probado

Los logs de preparación y servidor están dentro de la carpeta DEMO. Un puerto 8000 ocupado por otra aplicación produce un error; el lanzador no la cierra. Véase [SOLUCION_PROBLEMAS](SOLUCION_PROBLEMAS.md).

Implementación: `scripts/windows_demo.py`, `demo_config.py`, `demo_seed.py`, `demo_server.py`, `demo_launcher.ps1` y `config/demo_settings.py`. Evidencias reales previas: [ciclo Windows](../evidence/windows-demo-smoke.json), [navegación](../evidence/windows-demo-browser.json) y [reset temporal](../evidence/windows-demo-reset.json). No se presentan como una repetición en todos los Windows 10/11; la comprobación de esta fase figura en [DOCUMENTATION_AUDIT](../DOCUMENTATION_AUDIT.md).
