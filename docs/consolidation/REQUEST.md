# BEAUTYTPV — PROMPT MAESTRO DE CONSOLIDACIÓN FUNCIONAL Y EVOLUCIÓN V1

## 1. MISIÓN

Actúa como un equipo senior de ingeniería de software especializado en sistemas TPV, Django, Bootstrap, UX, seguridad, facturación española y aplicaciones comerciales instaladas localmente.

Tu misión es **consolidar, completar y perfeccionar BeautyTPV hasta obtener la mejor versión funcional posible dentro del alcance V1 aprobado**.

No debes reconstruir el proyecto desde cero. Debes evolucionar el código existente respetando su arquitectura, reglas de negocio, integridad fiscal, historial y pruebas.

### Contexto existente

- Proyecto: BeautyTPV.
- Referencia inicial: commit `4ce821e`.
- Auditoría y correcciones: commit `7045b03`.
- 697 pruebas aprobadas según la última auditoría.
- Backend Django.
- Frontend Bootstrap 5 + HTMX.
- Base de datos SQLite.
- Instalación independiente por empresa.
- Servidor local accesible desde terminales de la red.
- Integración VERI*FACTU preparada en modo TEST.
- Impresoras ESC/POS y cajón portamonedas.
- Roles internos: Superadmin, Administrador, Encargado y Empleado.
- Cliente: entidad comercial con acceso propio reservado para una versión futura.

Debes leer `AGENTS.md`, `PLAYBOOK.md`, `AUDITORIA_COMPLETA.md`, el código y las pruebas existentes.

El número de pruebas aprobadas no demuestra por sí solo que todos los flujos sean completos o que la experiencia de usuario sea adecuada.

**No declares el producto terminado hasta verificar cada requisito funcional contra el código, la interfaz y la persistencia.**

---

## 2. EQUIPO DE AGENTES

Utiliza los subagentes definidos en `.codex/agents/`.

Distribuye el trabajo de esta forma:

| Agente | Responsabilidad |
|---|---|
| architect | Arquitectura, contratos, modelos y coherencia global |
| backend | CRUD, formularios, reglas de negocio y servicios Django |
| frontend | Experiencia visual, navegación, Bootstrap y HTMX |
| security | Jerarquía, permisos, autenticación y auditoría |
| fiscal | Facturación, VERI*FACTU e inmutabilidad |
| hardware | Dispositivos, impresora, cajón y terminales |
| devops | Configuración, instalación, backups, actualización y recuperación |
| qa | Pruebas, cobertura, aceptación y regresiones |

El agente architect debe coordinar las dependencias.

El agente qa debe validar el trabajo de los demás y no limitarse a ejecutar las pruebas que ellos hayan escrito.

Trabaja por módulos con responsabilidades explícitas. Evita que varios agentes modifiquen simultáneamente los mismos archivos.

---

# 3. PRINCIPIO FUNDAMENTAL: FUNCIONALIDAD COMPLETA

Toda entidad administrable debe disponer de las operaciones CRUD que correspondan a sus reglas de negocio:

- Crear.
- Consultar.
- Listar.
- Buscar y filtrar.
- Editar.
- Desactivar o archivar.
- Eliminar únicamente cuando sea legal y funcionalmente permitido.
- Consultar historial cuando corresponda.

No debes implementar CRUD genérico sobre documentos fiscales, cobros confirmados, movimientos de caja o registros de auditoría.

En esas entidades deben utilizarse transiciones válidas, operaciones compensatorias, rectificaciones o anulaciones reglamentarias.

Para cada operación verifica:

1. Existe una ruta accesible y protegida.
2. Existe una vista funcional.
3. Existe una plantilla o interacción HTMX.
4. Se muestra la acción al rol autorizado.
5. El formulario contiene los campos necesarios.
6. Se validan los datos tanto en servidor como en interfaz cuando corresponda.
7. Se persisten correctamente los cambios.
8. Se informa del resultado al usuario.
9. Los errores son comprensibles.
10. Existe una prueba positiva.
11. Existe una prueba de autorización negativa.
12. Se registra auditoría cuando sea necesario.

Un botón que no realiza su operación completa es un defecto.

Una ruta que funciona pero no resulta accesible desde la navegación también debe considerarse una carencia funcional.

---

# 4. REVISIÓN COMPLETA DE CONFIGURACIONES

Diseña y completa un sistema de ajustes organizado por categorías, no una página gigantesca con parámetros sin estructura.

## 4.1 Configuración del salón

Verifica e implementa las operaciones necesarias sobre:

- Nombre comercial.
- Razón social.
- NIF.
- Dirección fiscal.
- Dirección comercial.
- Teléfono.
- Correo electrónico.
- Logotipo.
- Zona horaria.
- Moneda EUR.
- Datos mostrados en tickets.
- Preferencias visuales.
- Información fiscal aplicable.

Distingue los cambios comerciales de aquellos que puedan afectar a obligaciones fiscales o datos históricos.

## 4.2 Configuración del TPV

Debe permitir:

- Configurar la pantalla de inicio.
- Activar o desactivar la venta rápida.
- Configurar categorías visibles.
- Ordenar los servicios.
- Configurar las secciones del plano.
- Crear, editar, reordenar y desactivar puestos.
- Personalizar nombres de puestos.
- Definir estados visuales.
- Configurar preferencias de terminal.
- Asociar impresoras a terminales.
- Definir comportamientos de impresión.

No desarrolles un editor gráfico complejo si la cuadrícula por secciones cubre correctamente el alcance.

## 4.3 Configuración de caja

Verifica:

- Cajas configuradas.
- Terminal asociado.
- Apertura.
- Cierre.
- Importe inicial.
- Movimientos de entrada y salida.
- Arqueos.
- Diferencias.
- Historial.
- Permisos.
- Restricciones de caja cerrada.
- Impresión de comprobantes cuando esté prevista.

No permitas manipulación retrospectiva de movimientos confirmados.

## 4.4 Configuración fiscal

Verifica:

- Identificación del obligado.
- Series de facturación.
- Tipos fiscales soportados.
- Configuración VERI*FACTU.
- Entorno TEST y producción.
- Certificados electrónicos.
- Validez y vencimiento.
- Estado de conexión.
- Diagnósticos.
- Cola de registros.
- Errores y reintentos.
- Subsanaciones.
- Bloqueos de producción.
- Trazabilidad.

No permitas cambiar retroactivamente identidad fiscal, registros, huellas ni documentos emitidos.

Mantén los controles que impiden activar producción sin superar los requisitos exigibles.

---

# 5. SISTEMA JERÁRQUICO DE ROLES

Los roles internos forman esta jerarquía:

SUPERADMIN > ADMINISTRADOR > ENCARGADO > EMPLEADO.

Un rol superior hereda los permisos operativos de los inferiores.

La herencia no elimina los controles especiales sobre datos personales, elevación de privilegios, operaciones fiscales o acciones de soporte.

El CLIENTE será una entidad comercial independiente. No tendrá acceso web propio en esta versión.

## 5.1 Empleado

Debe poder:

- Acceder al plano.
- Consultar puestos.
- Abrir cuentas.
- Añadir servicios y productos.
- Modificar cantidades autorizadas.
- Consultar sus cuentas y operaciones permitidas.
- Cobrar en efectivo.
- Cobrar mediante tarjeta confirmada externamente.
- Realizar cobros mixtos.
- Emitir los documentos correspondientes mediante el flujo fiscal.
- Consultar su actividad permitida.
- Imprimir tickets.

No debe poder alterar configuraciones generales, modificar roles, aplicar operaciones reservadas al encargado ni consultar información global restringida.

## 5.2 Encargado

Hereda Empleado y además debe poder:

- Supervisar puestos.
- Autorizar descuentos especiales.
- Autorizar cambios restringidos en cuentas abiertas.
- Cancelar cuentas abiertas según reglas.
- Abrir y cerrar caja.
- Realizar arqueos.
- Registrar ingresos y retiradas.
- Supervisar ventas.
- Consultar informes autorizados.
- Gestionar incidencias operativas.
- Ejecutar devoluciones y rectificaciones dentro de sus permisos y procedimientos válidos.

## 5.3 Administrador

Hereda Encargado y además debe poder:

- Configurar el salón.
- Gestionar catálogo.
- Gestionar categorías.
- Gestionar secciones y puestos.
- Gestionar cajas según configuración soportada.
- Gestionar empleados de nivel inferior.
- Activar y desactivar usuarios.
- Gestionar permisos permitidos.
- Consultar informes globales.
- Exportar información autorizada.
- Configurar datos fiscales bajo las restricciones correspondientes.
- Consultar registros de actividad permitidos.

No puede crear, modificar ni eliminar Superadmins.

## 5.4 Superadmin

Hereda las capacidades operativas de Administrador, sujetas a los controles de elevación y acceso a datos protegidos.

Debe contar con un panel administrativo independiente y completamente funcional.

Revisar e implementar:

### Sistema
- Estado general del software.
- Versión instalada.
- Versión de dependencias.
- Estado de Django.
- Estado de SQLite.
- Integridad de la base de datos.
- Espacio disponible.
- Estado de servicios.
- Estado de trabajadores.
- Salud del sistema.
- Información de diagnóstico.

### Usuarios y seguridad
- Crear usuarios.
- Editar usuarios.
- Desactivar usuarios.
- Desbloquear accesos.
- Restablecer credenciales de forma segura.
- Gestionar roles.
- Gestionar Superadmins.
- Consultar auditoría.
- Revocar sesiones.
- Gestionar autorizaciones temporales.

### Hardware
- Crear y configurar terminales.
- Registrar impresoras.
- Configurar drivers.
- Asignar dispositivos.
- Probar impresión.
- Consultar colas.
- Diagnosticar errores.
- Gestionar trabajos pendientes de forma segura.
- Probar apertura de cajón con autorización.

### Mantenimiento
- Generar backups.
- Verificar backups.
- Descargar backups autorizados.
- Consultar historial.
- Configurar retención.
- Restaurar mediante un procedimiento seguro fuera de la base de datos activa.
- Comprobar actualizaciones.
- Validar paquetes.
- Ejecutar procedimientos de actualización autorizados.
- Gestionar rollback de código sin retroceder indebidamente el estado fiscal.
- Consultar registros técnicos saneados.

### Soporte
- Registrar incidencias.
- Consultar diagnóstico.
- Iniciar acceso temporal autorizado.
- Finalizar soporte.
- Registrar justificación y alcance.
- Auditar operaciones realizadas.
- Evitar acceso indiscriminado a información personal.

**No implementes botones decorativos ni páginas vacías.**

Si una operación de mantenimiento requiere ejecución externa o intervención sobre el sistema operativo, proporciona un flujo administrativo real, seguro y documentado. No conviertas el panel web en una consola arbitraria de comandos.

---

# 6. MATRIZ DE PERMISOS OBLIGATORIA

Genera `docs/ROLE_PERMISSION_MATRIX.md`.

Debe relacionar:

- Rol.
- Módulo.
- Acción.
- Permiso mínimo.
- Necesidad de elevación.
- Necesidad de autorización adicional.
- Acceso a datos personales.
- Auditoría obligatoria.
- Ruta.
- Servicio backend.
- Prueba de autorización.

Comprueba tanto las operaciones HTTP como los servicios Django que puedan ejecutarse sin petición web.

La seguridad nunca debe depender exclusivamente de ocultar botones.

Las operaciones sobre usuarios deberán comprobar el rol y estado actuales desde la base de datos, evitando decisiones basadas en sesiones obsoletas.

---

# 7. CRUD COMPLETO POR MÓDULO

Realiza una revisión exhaustiva de los siguientes módulos.

| Módulo | Operaciones requeridas |
|---|---|
| Usuarios | Alta, consulta, edición, activación, desactivación, credenciales y permisos |
| Clientes | Alta, búsqueda, consulta, edición, historial y eliminación permitida |
| Servicios | Alta, consulta, edición, desactivación y categorías |
| Productos | Alta, consulta, edición, desactivación y categorías |
| Secciones | Alta, consulta, edición, ordenación y eliminación permitida |
| Puestos | Alta, consulta, edición, ordenación, desactivación y estados |
| Cuentas | Apertura, consulta, modificación permitida, cancelación y cierre |
| Líneas de cuenta | Añadir, consultar, cambiar cantidad, notas, descuentos y retirar |
| Ventas | Consultar, filtrar, emitir documento y gestionar operaciones posteriores válidas |
| Caja | Apertura, cierre, arqueo, movimientos e historial |
| Facturas | Emisión, consulta, PDF, impresión y procedimientos de corrección válidos |
| Terminales | Alta, consulta, edición, desactivación y diagnóstico |
| Impresoras | Alta, consulta, edición, prueba, asociación y diagnóstico |
| Backups | Crear, consultar, verificar, descargar y restauración segura |
| Incidencias | Consultar, clasificar, registrar actuaciones y resolver |

En cada módulo distingue las entidades editables de los registros históricos inmutables.

No añadas eliminación física donde deba conservarse historial o trazabilidad.

---

# 8. INTERFAZ Y EXPERIENCIA DE USUARIO

BeautyTPV debe parecer un producto comercial profesional, no el Django Admin expuesto a empleados.

Mantén la filosofía de un TPV de hostelería adaptado al salón de estética.

## 8.1 Plano

La pantalla inicial debe mostrar:

- Secciones.
- Puestos agrupados.
- Estado de cada puesto.
- Cuenta abierta.
- Total pendiente cuando corresponda.
- Acceso táctil.
- Indicadores claros.
- Navegación rápida.

Debe funcionar correctamente en escritorio, pantalla táctil y tablet.

## 8.2 Cuenta del puesto

Debe ofrecer:

- Catálogo por categorías.
- Buscador.
- Carrito persistente.
- Cantidades.
- Precios.
- Notas.
- Descuentos autorizados.
- Totales.
- Botón de guardar/volver.
- Botón de cobrar.
- Mensajes de error y confirmación.

## 8.3 Cobro

Debe mostrar:

- Total.
- Efectivo.
- Cambio.
- Tarjeta.
- Pago mixto.
- Confirmación.
- Estado de operación.
- Emisión fiscal.
- Impresión.
- Recuperación ante errores.

## 8.4 Paneles administrativos

Cada pantalla debe tener:

- Título comprensible.
- Navegación coherente.
- Tabla o listado.
- Buscador y filtros cuando procedan.
- Botón de creación cuando esté autorizado.
- Acciones de consulta y edición.
- Confirmación de operaciones destructivas.
- Mensajes de éxito y error.
- Estado vacío útil.
- Diseño responsive.

Revisa toda la navegación para eliminar enlaces rotos, vistas inaccesibles, formularios incompletos y acciones que aparenten funcionar sin hacerlo.

Prioriza accesibilidad, claridad visual y rapidez operativa.

---

# 9. CONDICIONES DE INTEGRIDAD

No deben romperse las siguientes garantías:

- Una instalación por empresa.
- SQLite local sin compartir el archivo por SMB/NFS.
- Cuentas persistentes.
- Una cuenta activa por puesto.
- Evitar dobles cobros.
- Numeración fiscal consistente.
- Inmutabilidad de facturas emitidas.
- Encadenamiento fiscal.
- Auditoría protegida.
- Trabajos de impresión persistentes.
- Recuperación ante fallos.
- Copias de seguridad consistentes.
- Separación TEST/producción.
- Control de acceso por rol.
- Restricción de datos personales.
- Compatibilidad con futuras migraciones de base de datos.

No introduzcas SaaS, tenants, portal de clientes, agenda, reservas, bonos ni funciones fuera del alcance V1.

No amplíes silenciosamente el alcance fiscal más allá de los tipos y regímenes realmente soportados.

---

# 10. ESTRATEGIA DE EJECUCIÓN

## Fase A — Inventario real

Inspecciona:

- Modelos.
- Migraciones.
- URLs.
- Vistas.
- Formularios.
- Plantillas.
- Servicios.
- Permisos.
- Configuración.
- Comandos.
- Tests.

Genera una matriz de cobertura funcional.

Identifica operaciones ausentes, incompletas o inaccesibles.

## Fase B — Plan de mejoras

Clasifica cada hallazgo:

- CRÍTICO: seguridad, fiscalidad, corrupción de datos o cobros.
- ALTO: funcionalidad requerida incompleta.
- MEDIO: problemas operativos o UX relevantes.
- BAJO: coherencia visual o pequeñas mejoras.

Prioriza CRÍTICO y ALTO.

No añadas funcionalidades ajenas al alcance para incrementar artificialmente el número de características.

## Fase C — Implementación

Implementa las mejoras detectadas.

Cada cambio debe incluir las pruebas correspondientes.

Mantén las migraciones compatibles con instalaciones existentes.

No borres datos históricos para facilitar modificaciones.

## Fase D — Pruebas

Ejecuta:

- Tests unitarios.
- Tests de integración.
- Tests de permisos.
- Tests de formularios.
- Tests de persistencia.
- Tests fiscales locales.
- Tests de concurrencia SQLite.
- Tests de hardware simulado.
- Tests E2E Chromium.
- Tests de instalación y recuperación.

Incorpora pruebas positivas y negativas.

Los flujos E2E deben utilizar los mismos controles que utilizaría una persona.

Prueba explícitamente las operaciones de Superadmin.

## Fase E — Revisión visual

Inspecciona las pantallas principales con Chromium.

Comprueba:

- Escritorio.
- Tablet.
- Resoluciones estrechas.
- Legibilidad.
- Menús.
- Formularios.
- Modales.
- Estados vacíos.
- Errores.
- Flujo de cobro.
- Panel Superadmin.

Corrige defectos visuales que dificulten el uso.

## Fase F — Auditoría de cierre

Vuelve a contrastar cada requisito.

No utilices únicamente el recuento de pruebas como indicador de completitud.

---

# 11. ENTREGABLES OBLIGATORIOS

Debes producir:

1. Código corregido y funcional.
2. Migraciones necesarias.
3. Pruebas nuevas y existentes superadas.
4. `docs/FUNCTIONAL_COVERAGE.md`.
5. `docs/ROLE_PERMISSION_MATRIX.md`.
6. `docs/CRUD_COVERAGE.md`.
7. `docs/SETTINGS_COVERAGE.md`.
8. `docs/SUPERADMIN_COVERAGE.md`.
9. `docs/UI_REVIEW.md`.
10. `docs/FINAL_ACCEPTANCE.md`.

Cada matriz deberá contener:

- Requisito.
- Estado.
- Evidencia.
- Archivo de implementación.
- Ruta o servicio.
- Prueba.
- Observaciones.
- Bloqueos externos, si existen.

No etiquetes una función como completa sin evidencia verificable.

---

# 12. CRITERIOS DE FINALIZACIÓN

El trabajo se considerará finalizado cuando:

- Todas las funcionalidades del alcance V1 estén implementadas.
- Todos los módulos configurables tengan las operaciones necesarias.
- Los cuatro roles internos funcionen con herencia jerárquica.
- El Cliente esté correctamente modelado sin portal activo.
- El Superadmin disponga de todas sus operaciones reales.
- Todas las acciones autorizadas sean accesibles desde la interfaz.
- Todas las acciones restringidas estén protegidas en backend.
- No existan botones funcionalmente vacíos.
- Los formularios guarden y recuperen correctamente los datos.
- Los errores estén controlados.
- Las operaciones críticas tengan auditoría.
- Las pruebas automatizadas estén superadas.
- Las pruebas E2E cubran los flujos principales.
- Las migraciones funcionen sobre datos existentes.
- La instalación, actualización, backup y restauración sigan funcionando.
- La integridad fiscal y contable permanezca protegida.

Las verificaciones que requieren certificados oficiales, dispositivos físicos, personal real o equipos de destino deberán quedar en estado **BLOQUEADO EXTERNO**, con instrucciones precisas para resolverlas.

Nunca presentar simulaciones como validaciones oficiales.

---

# 13. INSTRUCCIÓN FINAL

**No te limites a auditar. Implementa y corrige.**

No reconstruyas BeautyTPV.

No elimines funcionalidades existentes.

No reduzcas la cobertura para conseguir pruebas verdes.

No introduzcas complejidad innecesaria.

Toma las decisiones técnicas razonables que permitan completar el alcance sin interrumpir continuamente el trabajo para solicitar confirmaciones.

Utiliza los agentes disponibles para trabajar de forma coordinada.

Realiza commits por módulos o fases verificables.

Al finalizar, entrega un resumen indicando:

- Funcionalidades revisadas.
- Problemas encontrados.
- Problemas corregidos.
- CRUD completados.
- Ajustes disponibles.
- Permisos verificados.
- Pantallas revisadas.
- Pruebas ejecutadas.
- Resultados.
- Commits generados.
- Bloqueos externos restantes.

**Resultado exigido: BeautyTPV V1 funcionalmente completo, coherente, seguro, mantenible y preparado para su validación final en un salón real.**

No declarar el producto apto para producción fiscal hasta superar los requisitos oficiales pendientes.