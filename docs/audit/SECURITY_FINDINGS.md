# Auditoría de seguridad de BeautyTPV

Base revisada: `0861517` (referencia funcional `4ce821e`), con integración concurrente coordinada por el principal. Esta revisión lee código y ejecuta pruebas locales; no certifica conformidad RGPD ni seguridad de infraestructura externa.

## Defectos reproducidos y correcciones

| ID | Prioridad | Reproducción inicial | Corrección y estado |
|---|---|---|---|
| SEC-01 | P1 | Una sesión PIN seguía autorizada después de resetear el PIN; respuesta `/tpv/` 200 | Hash de sesión HMAC incorpora PIN, rol, activo y `auth_version`. `update_user` incrementa versión al cambiar seguridad. Corregido, test negativo real navegador Django |
| SEC-02 | P1 | Sesión previamente elevada de empleado obtenía `/empresa/` 200 al promocionarlo a administrador | Cambio de rol revoca sesión y elevación. Corregido |
| SEC-03 | P1 | Administrador modificaba objeto empleado cacheado que entretanto había sido promovido a Superadmin | Recarga de destinatario dentro de transacción y revisión de rol/versión actual del actor. Corregido |
| SEC-04 | P1 | Actor cacheado ADMIN conservaba permisos de servicios después de degradarlo en BD | `require_role` comprueba estado persistido y versión; no confía exclusivamente en el objeto proporcionado. Corregido |
| SEC-05 | P1 | POST directo a `/tpv/cuentas/1/` eludía la autorización PII que solo cubría GET/HEAD | Middleware cubre todos los métodos de cuentas y reimpresión. Corregido |
| SEC-06 | P2 | Expiraciones `NaN`/`Infinity` en sesión eran consideradas elevación válida | Rechazo de valores no finitos/no numéricos/bool. Corregido; no se encontró entrada pública capaz de escribir ese valor |
| SEC-07 | P1 | SQL `INSERT OR REPLACE` reescribía auditoría pese a triggers UPDATE/DELETE | Migración `audit.0003_block_replace`: BEFORE INSERT sobre PK existente. Test falló antes del cambio y pasa después. Se comunicó el patrón a propietarios fiscales y operativos |
| SEC-08 | P2 | Origen bloqueado podía seguir creando filas de throttle para usuarios inventados | Comprobación de origen antes de crear clave de cuenta. Corregido y probado |
| SEC-09 | P2 | Autenticación PIN de usuario inexistente omitía coste de hash | Trabajo equivalente del hasher para inexistente/inactivo/sin PIN. Mitigación aplicada; no se afirma resistencia estadística absoluta a enumeración |
| SEC-10 | P2 | Forms de acceso/elevación eliminaban espacios de contraseñas legítimas | `strip=False`; preservación exacta probada. Se comunicó consistencia a formularios de gestión de usuarios |
| SEC-11 | P1 | Catálogo y configuración de plano usaban mínimo ADMIN sin exigir elevación, permitiendo cambiar IVA/precios/puestos desde sesión PIN | El decorador exige elevación automáticamente para todo mínimo ADMIN/SUPERADMIN. Las vistas operativas EMPLOYEE/MANAGER conservan acceso PIN. Corregido y probado |

El lote inicial de ocho pruebas reprodujo **7 fallos y 1 éxito** antes de las correcciones. No se atribuyen estos resultados a pruebas anteriores de la construcción inicial.

## Matriz revisada

Se ejecutan peticiones reales con Django Client para los cuatro roles y once entradas: plano, caja, clientes, facturas, catálogo, informes, empresa, configuración de plano, equipo, auditoría y soporte. La matriz incorpora elevación y autorización PII independiente cuando corresponden. También se contrastan enlaces de navegación con permisos backend.

| Capacidad | Empleado | Encargado | Administrador | Superadmin |
|---|---|---|---|---|
| Plano/caja/clientes/facturas | Sí, scopes operativos | Sí | Sí | Sí, PII temporal en rutas sensibles |
| Informes | 403 | Sí | Sí | Sí, PII temporal |
| Catálogo/plano configurable | 403 | 403 | Elevación requerida | Elevación requerida |
| Empresa/equipo/auditoría | 403 | 403 | Elevación requerida | Elevación requerida |
| Soporte técnico | 403 | 403 | 403 | Elevación requerida; acciones con autorización de alcance |

La matriz de rangos no crea rol Cliente: sigue reservado sin acceso. La autenticación por PIN no concede elevación. Reautenticar el mismo usuario con PIN elimina elevación anterior. Logout exige POST y los POST administrativos exigen CSRF.

`role_required` impone elevación para mínimos ADMIN/SUPERADMIN incluso cuando no se escribe `elevated=True`; una sesión privilegiada sigue pudiendo realizar operaciones heredadas de mínimos EMPLOYEE/MANAGER mediante PIN. Los servicios sin petición comprueban rol y revisión de seguridad persistidos; las entradas HTTP aportan el control de elevación.

Las sesiones técnicas PII exigen aprobador distinto de rango administrador o superior, activo, autorización vigente y no revocada. Las modificaciones de credenciales/rol/actividad por el servicio soportado revocan las concesiones donde el usuario es actor o aprobador. Desactivar y reactivar por ese servicio no resucita sesiones anteriores. Se ha probado también el rechazo de actores de servicios con versión de autenticación obsoleta.

## Terminal y trazabilidad

`LoginForm.terminal` valida exclusivamente terminales activos; la selección es opcional, se guarda tras autenticación válida y se elimina al acceder sin selección. Un terminal inactivo no autentica al usuario. `TerminalContextMiddleware` elimina referencias inválidas/desactivadas, expone `request.terminal` y limita la actualización CAS de `last_seen_at` a una por minuto.

`audit.record` añade `terminal_id` desde un ContextVar aislado por petición, sin dejarlo en peticiones posteriores ni tareas de fondo. La selección de terminal identifica el contexto operativo del navegador: **no constituye autenticación criptográfica de un bridge**. El bridge requiere su token separado y la autorización/ruta de dispositivo del módulo hardware.

El middleware debe instalarse después de SessionMiddleware y AuthenticationMiddleware y antes de SupportPIIMiddleware. La integración en `config/` pertenece al coordinador; el archivo de configuración no ha sido modificado por este agente.

## Pruebas y límites

Suite propia: `pytest tests/test_security.py tests/test_audit_security.py -q`; verificaciones de migraciones limitadas a `accounts audit`, Ruff sobre ambos módulos y sus pruebas. El coordinador registra la ejecución final del conjunto del producto y la instalación limpia. Los cambios de autenticación invalidan las sesiones creadas antes de esta actualización, por diseño.

Ejecución final de este agente: **110 passed in 16.66s**; `makemigrations accounts audit --check --dry-run`: sin cambios; `ruff check` y `ruff format --check` sobre la propiedad del agente: correctos (25 archivos formateados). Un intento intermedio de matriz encontró un fallo de columna `hardware_printer.terminal_id` durante la creación concurrente de su migración; la repetición posterior de la matriz completa pasó, sin ocultar ni deseleccionar ese caso.

Se probaron: hash PIN, bloqueo persistente usuario/origen, escalada horizontal de administración, scopes PII, expiración/revocación, evidencias SHA-256, inmutabilidad ORM/UPSERT/SQL REPLACE, contexto de terminal, CSRF y menús. Las restricciones SQLite no defienden frente a alguien con control del servidor que modifique esquema/código/ficheros.

Los servicios de gestión de usuarios son la vía soportada para cambios de credenciales y roles. Cambios manuales por SQL no pueden reclamar auditoría/invalidación de concesiones de soporte equivalente; no deben emplearse como procedimiento operativo. Ningún dato de tarjeta se añade a la autenticación ni a la auditoría. Los metadatos se filtran por lista permitida y el SHA-256 de conciliación se valida como 64 caracteres hexadecimales.

Revisión externa pendiente: infraestructura TLS/firewall/permisos OS, pruebas oficiales AEAT, dispositivos físicos y análisis de dependencias del paquete final. La presencia de esta revisión no elimina esos gates.
