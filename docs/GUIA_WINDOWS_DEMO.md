# BeautyTPV DEMO en Windows 10/11

Preparado el 15-11-2026 sobre el repositorio existente. Esta instancia es de demostración, con datos sintéticos, exclusivamente localhost y fiscal TEST. No modifica la instalación principal, no abre el firewall y no envía registros a AEAT.

## Abrir ahora, sin terminal

En este equipo los accesos están en `C:\Users\mmate\Desktop`:

| Acceso directo | Función |
|---|---|
| **BeautyTPV DEMO** | Comprueba y arranca la instancia; abre `http://127.0.0.1:8000/acceso/` |
| **Detener BeautyTPV DEMO** | Parada cooperativa exclusiva de esta DEMO; no cierra otros Python |
| **Usuarios BeautyTPV DEMO** | Abre el archivo privado de credenciales de esta instancia |
| **Cambiar usuarios BeautyTPV DEMO** | Con confirmación, detiene la DEMO y genera credenciales nuevas para los cuatro usuarios; conserva datos y revoca sesiones |
| **Reinicializar BeautyTPV DEMO** | Con confirmación, detiene y archiva exclusivamente la DEMO; crea otra limpia con credenciales nuevas |

Si BeautyTPV ya está abierto, el acceso de inicio reutiliza su proceso y abre el navegador. Cerrar la pestaña no detiene el servidor: use el acceso de parada. Para reiniciar, use Detener y luego BeautyTPV DEMO. Los errores se muestran en un diálogo; no necesita una consola durante el uso habitual.

El navegador puede mostrar HTTP «No seguro» porque la DEMO usa HTTP exclusivamente en loopback. No contiene personas reales. La configuración productiva de HTTPS/cookies seguras permanece intacta; no se ha configurado esta DEMO para LAN o Internet.

## Datos y usuarios

Carpeta independiente: `C:\Users\mmate\AppData\Local\BeautyTPV-DEMO` (en otro usuario: `%LOCALAPPDATA%\BeautyTPV-DEMO`). Contiene:

- `demo.sqlite3`: única base que usan estos lanzadores.
- `config.json`: marcador DEMO y claves aleatorias externas.
- `credenciales-demo.txt`: contraseñas y PIN generados para esa instancia.
- `demo-server.log` y `preparacion.log`: diagnóstico del arranque/preparación.
- `staticfiles`, `backups` y estado efímero `server.json`.

La carpeta se restringe mediante ACL al usuario actual de Windows y SYSTEM antes de escribir secretos. Las contraseñas/PIN son distintos y aleatorios; no están en el repositorio, los informes ni las capturas. Abra **Usuarios BeautyTPV DEMO** para consultarlos. No reutilice estos secretos en otro sistema ni comparta/copíe `config.json`, `server.json` o el archivo de credenciales en un informe público.

| Usuario | Rol | Forma de entrar |
|---|---|---|
| `demo_empleado` | Empleado | Usuario y PIN del archivo privado |
| `demo_encargado` | Encargado | Usuario y PIN del archivo privado |
| `demo_admin` | Administrador | Usuario, contraseña y casilla **Acceder con contraseña** |
| `demo_superadmin` | Superadmin | Usuario, contraseña y casilla **Acceder con contraseña** |

Seleccione **Terminal DEMO**. El PIN permite operar, pero no concede elevación para administración. Si entra como Admin/Superadmin con PIN, confirme su contraseña en **Confirmar identidad** o `/elevar/` antes de administrar.

Secciones A/B, puestos A1–A3/B1, servicios Manicura DEMO y Tratamiento DEMO, producto Crema DEMO, Cliente DEMO, Caja DEMO, Terminal DEMO e Impresora simulada DEMO son sintéticos. Bootstrap conserva además la caja inicial del programa. El catálogo es de demostración; no constituye recomendación fiscal para un salón real.

La comprobación de esta entrega dejó una venta de prueba, un turno de Caja DEMO abierto y una cuenta A2 con un producto pendiente. Es intencional para mostrar persistencia. Para volver al estado sin ventas, use Reinicializar exclusivamente la DEMO.

## Acceder como Superadmin

1. Entre como `demo_superadmin` con su contraseña y la casilla de contraseña marcada.
2. Abra **Soporte técnico**. El diagnóstico y las colas muestran datos reales de la DEMO.
3. Para terminales, dispositivos o incidencias técnicas, autorice soporte: motivo, alcance **Técnico**, usuario `demo_admin` y contraseña de ese Administrador.
4. Para clientes, cuentas, facturas o informes, cree una autorización adicional de alcance **Datos personales**, aprobada por `demo_admin`. Se exige otro administrador; el Superadmin no se aprueba PII a sí mismo.
5. Las autorizaciones caducan y se pueden revocar. No se ha añadido ningún atajo para saltar elevación, jerarquía o scopes.

La página fiscal se puede consultar, pero la DEMO rechaza guardar certificados/cambiar entorno. La prueba de red AEAT se rechaza: deje esa casilla sin marcar. Los registros TEST quedan pendientes, sin acuses inventados. No retire el bloqueo productivo ni intente convertir esta carpeta DEMO en una instalación fiscal.

## Comprobar los flujos

| Pantalla / operación | Rol adecuado |
|---|---|
| Plano, abrir A1/A2, añadir, volver y recuperar | Empleado o superior |
| Cobrar efectivo/tarjeta externa/mixto | Empleado o superior; caja abierta para efectivo |
| Abrir turno de Caja DEMO | Empleado o superior |
| Ingresos/retiradas, arqueo y cierre | Encargado o superior |
| Clientes, ficha e historial | Roles operativos; Superadmin con autorización PII |
| Catálogo, categorías, configuración de salón/plano/cajas/equipo | Administrador elevado o superior |
| Informes e incidencias operativas | Encargado o superior; Superadmin con los scopes correspondientes |
| Soporte, terminales, dispositivos y diagnóstico | Superadmin elevado; acciones técnicas con autorización |
| Facturas/PDF/QR y cola VERI*FACTU TEST | Acceso documental según rol; Superadmin con PII |

Para una venta de prueba: abra turno, entre en un puesto, añada Manicura DEMO, indique efectivo12,10 y recibido20,00, seleccione Caja DEMO y confirme. El cambio esperado es7,90. La factura y su alta TEST persisten; el simulador procesa el ticket. **DONE solo indica consumo simulado de bytes: no se ha impreso papel ni abierto un cajón físico.** Tarjeta registra confirmación externa sintética de la DEMO; no cobra en un banco.

## Instalación inicial y preparación en otro equipo

Este equipo ya tiene Python y `.venv` con las dependencias existentes. Al arrancar por primera vez, el lanzador crea una configuración privada, aplica migraciones, bootstrap, semilla y estáticos en la carpeta DEMO. No copia ni modifica `db.sqlite3` principal.

Si se traslada el repositorio a otro Windows, la preparación inicial puede hacerse una vez en PowerShell, desde su carpeta:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.venv\Scripts\python.exe -m pip install --no-deps -e ".[dev]"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\crear_acceso_directo.ps1
```

Luego use los accesos. El script resuelve el escritorio real de Windows, incluidos escritorios redirigidos, y no sobrescribe accesos ajenos con esos nombres. `ExecutionPolicy Bypass` se aplica solo al proceso del script; no cambia la política permanente ni el firewall. Políticas corporativas pueden impedir su ejecución: no se han desactivado controles del equipo.

También están disponibles `iniciar_beautytpv_demo.bat` y `detener_beautytpv_demo.bat` en la raíz del repositorio. El acceso directo usa PowerShell/pythonw ocultos para que no permanezca una terminal. No usa `runserver`: sirve Django con Waitress, `DEBUG=False`, estáticos locales y host fijo127.0.0.1:8000.

## Reinicializar exclusivamente la DEMO

Use el acceso **Reinicializar BeautyTPV DEMO** y confirme. Primero se detiene la DEMO. La carpeta marcada se renombra a `BeautyTPV-DEMO-archivada-<fecha>-<id>` en el mismo directorio padre; no se borra recursivamente ni se toca la base principal. Se genera otra instancia DEMO con usuarios y claves nuevos. Abra de nuevo Usuarios BeautyTPV DEMO para ver las credenciales actuales.

No apunte estos scripts a una instalación real. Se rechazan carpetas sin marcador, rutas del repositorio, enlaces/junctions y archivos sensibles con hardlinks. La rotación de usuarios es distinta de reinicializar: conserva ventas, facturas y cuentas; únicamente cambia credenciales/sesiones de los cuatro usuarios de prueba.

Para soporte automatizado existen acciones CLI, siempre opcionales:

```powershell
.venv\Scripts\python.exe scripts\windows_demo.py status --no-gui
.venv\Scripts\python.exe scripts\windows_demo.py setup --no-gui
.venv\Scripts\python.exe scripts\windows_demo.py reset --no-gui --confirm "REINICIAR DEMO"
.venv\Scripts\python.exe scripts\windows_demo.py rotate-users --no-gui --confirm "CAMBIAR USUARIOS DEMO"
```

## Errores habituales

| Error | Qué hacer |
|---|---|
| No se encuentra `.venv\Scripts\pythonw.exe` | Complete la instalación inicial en esa carpeta; no mueva el repositorio sin recrear los accesos |
| Faltan dependencias / pip check incompatible | Reparar `.venv` con el lock y repetir; el arranque no instala paquetes silenciosamente |
| Puerto8000 ocupado | Detenga la otra aplicación por su procedimiento o cierre esta DEMO si ya existe. El lanzador no mata procesos por nombre o puerto |
| DEMO activa pero no responde | Use Detener; consulte `demo-server.log`. Nunca ejecute `taskkill /IM python.exe` |
| Credencial incorrecta / bloqueo temporal | Revise el archivo privado, rol, PIN vs casilla de contraseña. Si es necesario, use Cambiar usuarios DEMO con confirmación |
|403 al abrir administración/soporte | Confirme contraseña y, en Superadmin, autorización temporal del alcance correcto. No es un fallo de arranque |
| No responde en otro ordenador | Es correcto: escucha exclusivamente localhost y no abre firewall ni LAN |
| Faltan estilos | Detener y volver a iniciar recopila estáticos en la carpeta DEMO; revisar `preparacion.log` |
| Configuración, enlace o ruta no reconocidos | No copie configuraciones productivas. Use una carpeta DEMO propia y el procedimiento seguro de reinicialización |
| Fiscal pendiente / prueba de conexión bloqueada | Es el comportamiento esperado offline. No hay certificados ni remisión AEAT; no se inventan aceptaciones |
| Mantenimiento/hold operativo | Revisar ajustes DEMO/restore asistido con Superadmin o reinicializar solo la DEMO; no eliminar marcadores de una instalación real |

## Verificación realmente ejecutada

- Equipo probado: Windows11 Pro10.0.26300, Python3.14.7; no se afirma ejecución física adicional en Windows10.
- Preparación y migraciones reales de una SQLite independiente; usuarios aleatorios con hashes y ACL externas.
- Inicio, HTTP200 de acceso y Bootstrap, doble inicio con proceso reutilizado, parada exclusiva, proceso Python ajeno preservado, puerto ajeno rechazado y reinicio.
- Accesos `.lnk` reales de parada/inicio ejecutados mediante Shell de Windows; se abrió el navegador por defecto.
- Chromium real contra Waitress: acceso de cuatro roles, navegación autorizada, cobro sintético, cambio, facturaTEST, cuenta persistente e impresión simuladaDONE. Cero transmisiones fiscales.
- Capturas reales de acceso, plano, cobro, factura y Superadmin revisadas visualmente. La herramienta nativa de captura de escritorio no pudo inicializar su kernel; se utilizó Chromium y sus capturas. No se atribuye una sesión manual humana ni pruebas físicas a esta verificación.
- El hash de la SQLite principal antes/después coincide. Evidencias sin secretos en `docs/evidence/windows-demo-*.json` y JUnit.
- Regresión integrada: **893 PASS, 374,87s**, incluidos14E2E Chromium. Después del ajuste final exclusivo del heartbeat del servidor DEMO, suite específica completa **58 PASS, 75,03s** (incluye su nueva regresión). Dos avisos conocidos de pytest: override DATABASES aislado y fixture de plugin deprecada para pytest10; sin fallos. Ruff limpio302archivos, Django check0 y migraciones sin drift. BAT y accesos directos se probaron realmente aparte.

No se han enviado documentos AEAT, configurado producción, abierto firewall ni probado impresora/cajón físicos. Los bloqueos oficiales de release permanecen vigentes.

Implementación DEMO registrada en commit `4e67b44`; documentación y evidencias en el commit de cierre posterior.
