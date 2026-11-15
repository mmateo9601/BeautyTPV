# Soporte de BeautyTPV

BeautyTPV se instala localmente por empresa. No hay un servicio SaaS central, un correo de soporte, un SLA comercial ni una organización titular anunciados en este repositorio. Acuerde el contacto y las condiciones con el propietario del producto o el instalador que mantiene su equipo; no envíe datos a una dirección supuesta.

## Elegir el procedimiento

| Necesidad | Primer recurso |
|---|---|
| Aprender a vender, guardar cuentas o cerrar sesión | [Guía de usuario](docs/manuales/GUIA_USUARIO.md) |
| Configurar catálogo, salón, cajas y usuarios inferiores | [Guía de Administrador](docs/manuales/GUIA_ADMINISTRADOR.md) |
| Diagnóstico, permisos técnicos, colas o mantenimiento | [Guía Superadmin](docs/manuales/GUIA_SUPERADMIN.md) |
| DEMO no arranca, credenciales de prueba o accesos de escritorio | [Guía Windows DEMO](docs/GUIA_WINDOWS_DEMO.md) |
| Instalación o recuperación Windows | [Solución de problemas](docs/instalacion/SOLUCION_PROBLEMAS.md) |
| Posible vulnerabilidad o exposición de datos | [SECURITY.md](SECURITY.md), mediante canal privado acordado |
| Cambiar o ampliar código | [CONTRIBUTING.md](CONTRIBUTING.md) y [documentación de desarrollo](docs/desarrollo/GUIA_DESARROLLADOR.md) |

## Preparar una solicitud útil y segura

Registre versión/commit, fecha aproximada, rol, pantalla, acción, mensaje de error y resultado esperado. Describa si afecta a una cuenta, a todas las operaciones o a un solo terminal. Use identificadores internos mínimos cuando sean necesarios en el canal privado; para una reproducción pública o compartida utilice exclusivamente una DEMO sintética.

El Encargado/Administrador puede registrar una incidencia **operativa** desde el menú Incidencias. El Superadmin elevado con TECHNICAL puede clasificar y tratar incidencias técnicas, registrar actuaciones, resolver y reabrir sin modificar el historial anterior. No pegue nombres de clientes, XML fiscales, tarjetas, contraseñas, PIN, tokens, certificados o logs completos en una incidencia.

El panel ofrece diagnóstico/exportación saneada y logs restringidos. Un export saneado no autoriza distribuir cualquier archivo del equipo. No adjunte `instance.json`, `config.json`, `server.json`, archivos de credenciales, SQLite, copias, claves ni capturas de formularios con secretos. Si un análisis requiere una copia, acuerde primero propósito, destinatario autorizado, canal protegido, retención y devolución/eliminación.

## No agravar un fallo

- Ante doble clic o error de impresión, consulte la cuenta, factura y spool antes de repetir. No vuelva a cobrar para imprimir.
- Un trabajo UNKNOWN puede haberse entregado: revisión física y copia autorizada sin cajón; no reenvío automático.
- Un registro fiscal pendiente/rechazado no es aceptado. No edite el documento emitido para forzar el envío; use el flujo fiscal permitido con revisión adecuada.
- Ante mantenimiento o restauración, detenga operaciones según el runbook y preserve acuses/evidencias. No quite una retención fiscal sin conciliación.
- No use `taskkill /IM python.exe`, borre SQLite ni restaure una copia anterior como solución genérica. La DEMO tiene su propio acceso de parada y reinicialización aislada.

## Límites de lo ofrecido

Las pruebas locales, capturas y simulador están documentados en [RELEASE_REPORT](docs/RELEASE_REPORT.md). Certificado/acuse oficial AEAT, declaración responsable suscrita, impresora/cajón físicos, TLS/LAN y aceptación con operadores reales requieren recursos y procedimientos externos. El soporte técnico no habilita indiscriminadamente PII: conserva motivo, aprobación, scope, expiración y auditoría.

La reutilización técnica del repositorio no equivale a licencia de redistribución. Consulte [OPCIONES_LICENCIA](docs/legal/OPCIONES_LICENCIA.md) y [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md) antes de distribuir paquetes.
