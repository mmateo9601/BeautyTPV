# Funcionalidades de BeautyTPV 0.1.0

Catálogo funcional derivado de la interfaz, vistas, servicios y pruebas. Los procedimientos están en los [manuales](README.md); la [auditoría documental](DOCUMENTATION_AUDIT.md) indica la evidencia de esta fase. Una captura prueba el aspecto observado, no por sí sola toda la operación ni una validación oficial.

E=Empleado, M=Encargado, A=Administrador, S=Superadmin. Los superiores heredan operativa, conservando elevación, jerarquía y scopes. Para S, clientes/cuentas/facturas/informes requieren PII con otro aprobador activo; las acciones técnicas sensibles requieren su alcance temporal. [Matriz completa](ROLE_PERMISSION_MATRIX.md).

## Operativa y administración

| Funcionalidad / descripción | Rol autorizado | Acceso y flujo | Resultado esperado | Restricción | Captura | Estado |
|---|---|---|---|---|---|---|
| Identificación por usuario/PIN o contraseña | E/M/A/S con credenciales propias | Acceso → usuario/credencial → terminal → Entrar | Sesión atribuible y plano | PIN no eleva; bloqueo temporal por intentos | [Acceso](screenshots/login-desktop.png) | Implementado y verificado localmente |
| Plano de secciones/puestos y estados | E/M/A/S | Plano → sección → puesto | Cuenta activa recuperada o nueva; total pendiente visible | Una activa por puesto; libre/ocupado/en cobro con texto | [Plano](screenshots/plano-salon-desktop.png) | Implementado y verificado localmente |
| Carrito, búsqueda, categorías, cantidades/notas | E/M/A/S | Cuenta → catálogo → añadir → guardar | Líneas y notas persistentes | Ocultar categoría impide nueva adición directa; reducir/quitar/descuento restringido M | [Cuenta](screenshots/cuenta-puesto-desktop.png) | Implementado y verificado localmente |
| Preparar cobro y reanudar edición | E/M/A/S | Cuenta → Preparar cobro; Volver a editar | Estado PAYMENT_PENDING o OPEN persistido | No editar mientras está en cobro ni tras cerrar | [Carrito](screenshots/carrito-desktop.png) | Implementado y verificado localmente |
| Efectivo, tarjeta externa y mixto | E/M/A/S | Cobrar → componentes → recibido/caja/referencia → confirmar | Una venta/documento; cambio y componentes conciliados | Caja abierta para efectivo; tarjeta no ejecuta cargo bancario desde BeautyTPV | [Cobro](screenshots/cobro-efectivo.png) | Implementado y verificado localmente |
| Cuentas independientes y venta rápida opcional | E/M/A/S | Volver al plano/otro puesto; Venta rápida si habilitada | Se mantienen cuentas y líneas | Venta rápida configurable, sin agenda/reserva | [Puesto](screenshots/puesto-libre-desktop.png) | Implementado y verificado localmente |
| Apertura y consulta de caja | E/M/A/S | Caja → caja/fondo → Abrir turno | Turno único por caja e historial autorizado | Se conserva apertura E; cajas activas/terminales válidas | [Caja](screenshots/caja-desktop.png) | Implementado y verificado localmente |
| Ingresos, retiradas, arqueo/cierre | M/A/S | Caja → movimiento/motivo o contado → confirmar cierre | Saldos esperado/contado/diferencia conservados | Sin manipular movimientos o cierres confirmados | [Arqueo](screenshots/arqueo-desktop.png) | Implementado y verificado localmente |
| Clientes: ficha, búsqueda e historial | E/M/A/S con controles | Clientes → buscar/crear/editar → historial | Ficha e historial transaccional | Exportar/borrar A; borrar solo sin historia protegida; S exige PII | [Clientes](screenshots/clientes-desktop.png) | Implementado y verificado localmente |
| Servicios/productos y categorías | A/S elevados | Catálogo → alta/edición; Categorías → orden/visibilidad | Precios/impuestos/actividad/orden guardados | Cambios no alteran líneas emitidas; no eliminar categoría usada | [Catálogo](screenshots/catalogo-desktop.png) | Implementado y verificado localmente |
| Ajustes comerciales/fiscales/TPV | A/S elevados | Empresa → Salón/Fiscal/TPV → guardar categoría | Datos futuros, logo raster, apariencia y preferencias | EUR; NIF/instalación protegidos tras emitir; snapshots anteriores intactos | [Configuración](screenshots/configuracion-desktop.png) | Implementado y verificado localmente |
| Secciones/puestos: alta, orden, actividad | A/S elevados | Configurar plano → formularios/acciones | Cuadrícula y nombres configurados | No desactivar/reasignar puesto con cuenta abierta; historia protegida | [Plano configurable](screenshots/configuracion-plano-desktop.png) | Implementado y verificado localmente |
| Cajas configurables | A/S elevados | Caja → Configurar cajas | Nombre/actividad/terminal mantenidos | No desactivar/reasignar con turno abierto; no borrar historia | [Cajas](screenshots/configuracion-cajas-desktop.png) | Implementado y verificado localmente |
| Equipo, roles y credenciales | A sobre inferiores; S también S | Equipo → alta/editar/actividad/reset/revocar | Usuario y autorizaciones actuales | No contraseña/PIN en claro; cambios sensibles invalidan sesiones; desbloqueo visible S | [Equipo](screenshots/usuarios-desktop.png) | Implementado y verificado localmente |
| Documentos, PDF/QR, copia y rectificación total | E propios; M/A/S según alcance | Facturas → documento → PDF/copia o rectificar | Documento inmutable y compensación válida | F1/F2 y R1/R5 total; sin edición/borrado histórico ni devolución parcial | [Facturas](screenshots/facturas-desktop.png) | Implementado localmente; validación fiscal externa pendiente |
| Informes y exportaciones CSV | M/A/S según scopes | Informes → período/caja/método/empleado/artículo → filtrar/exportar | Desgloses conciliados con documentos y devoluciones | Filtros seleccionan operaciones completas; no inventan reparto proporcional de IVA | [Informes](screenshots/informes-desktop.png) | Implementado y verificado localmente |
| Auditoría | A/S elevados | Auditoría → consulta según permisos | Eventos protegidos, sin reescribir historia | No es un CRUD de logs ni una copia de secretos/PII sin control | [Manual de administración](manuales/GUIA_ADMINISTRADOR.md) | Implementado y verificado localmente |

## Soporte, mantenimiento e integraciones

| Funcionalidad / descripción | Rol y acceso | Flujo / resultado | Restricciones | Captura / procedimiento | Estado |
|---|---|---|---|---|---|
| Panel técnico, salud, versiones y diagnóstico | S elevado; Soporte técnico | Consulta DB/disco/migraciones/workers/colas; diagnóstico medido | No prometer métrica no medida; conexión TCP no es autenticación ni envío AEAT | [Panel](screenshots/superadmin-dashboard.png), [diagnóstico](screenshots/diagnostico-desktop.png) | Implementado y verificado localmente |
| Autorización temporal de soporte | S y aprobador autorizado | Motivo+scope+contraseña → concesión limitada → revocar | PII requiere otro Admin; elevación10min y concesión20min | [Guía S](manuales/GUIA_SUPERADMIN.md) | Implementado y verificado localmente |
| Incidencias y actuaciones | M/A operativas; S técnicas con TECHNICAL | Registrar/clasificar → actuaciones → resolver/reabrir | Sin datos personales, secretos ni XML/logs crudos; actuaciones append-only | [Incidencias](screenshots/incidencias-desktop.png) | Implementado y verificado localmente |
| Terminales, preferencias y dispositivos | S elevado+TECHNICAL | Soporte → terminal/impresora → configurar/probar | Token hash; terminal no concede permisos; DEMO solo simulador | [Terminales](screenshots/terminales-desktop.png), [impresoras](screenshots/impresoras-desktop.png) | Configuración implementada localmente |
| Spool ESC/POS, corte/cajón, copias y agente remoto | E copias propias; S pruebas/retry; worker/agente OS | Encolar → entregar fuera de atomic → estado/evento | UNKNOWN no se repite automáticamente; copia sin cajón; driver/firmware físico pendiente | [HARDWARE](integraciones/HARDWARE.md) | Implementado; validación física externa pendiente |
| VERI*FACTU, cadena y cola | Worker OS; S recuperación autorizada | Factura+alta/outbox → remisión preparada → estado/acuse real cuando exista | TEST no es homologación; DEMO no remite; producción bloqueada | [Registro](screenshots/verifactu-desktop.png), [integración](integraciones/VERIFACTU.md) | Implementado localmente; AEAT oficial pendiente |
| Backup cifrado, verificación y descarga | S elevado+BACKUP | Crear → listar/verificar → descargar autorizado | Clave externa; proteger copias como datos sensibles | [Backups](screenshots/backups-desktop.png) | Implementado y verificado localmente |
| Restauración asistida y recuperación | S+BACKUP y operador OS | Web verifica/prepara; CLI offline reemplaza con lock y hold | Servicio detenido; conciliar documentos/acuses antes de retirar retención | [Restauración](screenshots/restauracion-desktop.png), [runbook](instalacion/BACKUP_RESTORE.md) | Implementado localmente; conciliación real externa pendiente |
| Actualizaciones y rollback de código | S+UPDATE para preflight; operador OS para aplicar | Validar paquete → backup → actualización offline → checks | No shell web, no retroceso automático de BD ni rollback de venv | [Versiones](screenshots/actualizaciones-desktop.png), [runbook](instalacion/ACTUALIZACIONES.md) | Implementado y verificado localmente con límites del paquete |
| DEMO Windows por accesos directos | Usuario OS; cuatro roles de prueba | Inicio/parada/usuarios/reset con perfil independiente | Localhost/DEBUGFalse/TEST; no instala servicio OS ni abre firewall | [ARRANQUE_DEMO](instalacion/ARRANQUE_DEMO.md) | Implementado; Windows11 probado, Windows10 sin equipo adicional |

## Alcance y posibilidades futuras

| Clasificación | Elementos |
|---|---|
| Implementado y verificado localmente | Operativa, persistencia, permisos, inmutabilidad, formularios, informes, simulación, CLI de recuperación y DEMO según sus evidencias |
| Implementado y pendiente de validación externa | Remisión/acuse oficial AEAT, declaración responsable suscrita, papel80mm/QR/cajón físicos, TLS/LAN/equipo/operadores de destino |
| No incluido en V1 | Portal/login Cliente, agenda, reservas, bonos, banco/datáfono integrado, devoluciones parciales y regímenes fiscales no soportados |
| Posibilidades futuras, sin compromiso de implementación | Portal Cliente/agenda/reservas si se aprueban en otra versión; migración PostgreSQL cuando haya necesidad medida |

Una ficha Cliente no es una cuenta web ni forma parte de la jerarquía interna. El proyecto conserva SQLite, una instalación por empresa y la fiscalidad soportada explícitamente. La [licencia AGPLv3](../LICENSE), la entrega del [código correspondiente](../SOURCE_CODE.md) y los [avisos de terceros](../THIRD_PARTY_NOTICES.md) tienen obligaciones independientes de la completitud técnica.
