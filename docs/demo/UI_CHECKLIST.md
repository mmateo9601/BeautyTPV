# Comprobación visual de BeautyTPV DEMO en Windows

Fecha: 15-11-2026. Este documento define el recorrido y los resultados esperados a partir del código actual. **No acredita ejecución manual**: el coordinador debe registrar las comprobaciones efectivamente realizadas y sus evidencias en `GUIA_WINDOWS_DEMO.md` o el informe de cierre. No se han modificado plantillas ni módulos funcionales.

## Preparación sin terminal habitual

1. Abrir **BeautyTPV DEMO** desde el escritorio. Debe aparecer el navegador en `http://127.0.0.1:8000/acceso/` o en el plano si hay sesión válida; nunca una dirección LAN o un sitio externo.
2. En primera ejecución, explicar que se prepara una base independiente y que puede tardar. Al finalizar, indicar la ubicación del archivo privado de credenciales y cómo volver a abrirlo. No mostrar contraseñas en mensajes de error, logs, argumentos de proceso ni capturas.
3. Las credenciales aleatorias pertenecen a `%LOCALAPPDATA%\BeautyTPV-DEMO\credenciales-demo.txt`, protegido por ACL del usuario actual y SYSTEM. Los nombres estables `demo_empleado`, `demo_encargado`, `demo_admin` y `demo_superadmin` no implican contraseñas predeterminadas. Confirmar los nombres con la semilla entregada.
4. La pantalla de identificación debe conservar etiquetas Usuario, PIN o contraseña, Acceder con contraseña y Terminal. Para Admin y Superadmin, introducir la contraseña generada y marcar **Acceder con contraseña**. Un PIN válido permite operativa pero no eleva privilegios.
5. No capturar ni versionar el archivo de credenciales. En una evidencia de acceso, dejar vacío el campo de contraseña o mostrarlo enmascarado.

## Recorrido de los cuatro roles

Usar sesiones separadas o cerrar sesión entre roles; no reutilizar una sesión elevada para demostrar acceso por PIN.

| Rol | Acceso y acciones positivas | Denegación / control esperado | Estado de esta revisión |
|---|---|---|---|
| Empleado | PIN; plano A/B; abrir A1, añadir Manicura DEMO, guardar nota, volver al plano y recuperar; abrir A2 sin perder A1; caja activa; cliente DEMO; cobro propio y copia | No Catálogo, Empresa, Equipo, informes globales ni Soporte. No cerrar turno, quitar/reducir líneas o aplicar descuento restringido | PENDIENTE de ejecución en la instancia preparada |
| Encargado | PIN; operativa de Empleado; descuento autorizado, movimientos y arqueo/cierre, informes e incidencias operativas | No configuración general, usuarios, dispositivos o soporte técnico | PENDIENTE |
| Administrador | Contraseña con modo contraseña; catálogo/categorías, secciones/puestos, configuración Salón/Fiscal/TPV, cajas y equipo inferior | No crear/editar Superadmin; no acceso técnico a `/soporte/` | PENDIENTE |
| Superadmin | Contraseña con modo contraseña; panel propio, diagnóstico, terminales, dispositivos, copias y cola fiscal | Elevación y autorización temporal siguen siendo obligatorias. Para información comercial PII exige otro aprobador Admin activo | PENDIENTE |

La jerarquía hereda capacidades operativas, no elimina la elevación ni los scopes. Si la elevación caducó, usar **Confirmar identidad** (`/elevar/`) e introducir la contraseña de la propia sesión. No utilizar el PIN para esta confirmación.

## Superadmin y datos protegidos

1. Acceder a `/soporte/` con contraseña. Ver estado del servidor, base de datos, versión, disco y colas reales de la DEMO.
2. En **Sesión de soporte**, escribir una justificación clara de al menos diez caracteres, seleccionar TECHNICAL y aprobar con `demo_admin` y su contraseña aleatoria. Comprobar que la autorización aparece con vencimiento.
3. Abrir **Terminales y bridge** y consultar la terminal DEMO; abrir **Dispositivos** y consultar la impresora SIMULATOR. Una prueba de ticket/cajón debe encolar un trabajo y terminar en estado simulado sin dispositivo físico ni red.
4. Para consultar clientes, cuentas, facturas o informes como Superadmin, crear **otra** autorización PII aprobada por `demo_admin`. TECHNICAL por sí sola no debe permitir esos accesos. No deshabilitar middleware para completar el recorrido.
5. Abrir **Certificado y entorno fiscal** en consulta: debe indicar TEST y referencias vacías. El perfil DEMO debe rechazar cambios que pretendan activar producción o certificados y debe mantener las defensas fiscales.
6. No activar **Medir conexión AEAT TCP443**. Si se solicita, la DEMO debe responder con un mensaje de desconexión intencionada sin realizar esa conexión. Consultar la cola no equivale a enviarla.

## Cobro y persistencia

| Paso | Control humano | Evidencia esperada |
|---|---|---|
| Apertura | Caja y turnos → fondo inicial sintético → Abrir turno | Turno abierto persistido; el principal no cambia |
| Cuenta | Plano → A1 → servicio y producto → nota → Guardar | Cantidades, nota y total sobreviven al retorno y recarga |
| Preparar cobro | Preparar cobro y bloquear edición | Estado «en cobro», edición bloqueada; permite volver a editar de forma explícita |
| Efectivo | Total exacto, recibido superior, turno DEMO, confirmar cobro | Cambio correcto, una venta/factura/alta, puesto libre, spool simulado |
| Tarjeta / mixto | Referencia inventada identificada como DEMO; reparto exacto | Registro de confirmación externa, no operación bancaria; caja solo por efectivo |
| Factura | Consultar detalle/PDF/reimprimir copia | Aviso TEST visible, QR y desglose; copia no cobra ni abre cajón |
| Fiscal | Panel Superadmin → Cola fiscal | Registro TEST pendiente, sin aceptación inventada ni FiscalTransmission generado por la DEMO |
| Caja/informes | Encargado → informes y arqueo/cierre | Importes conciliados; movimientos y facturas no editables retrospectivamente |
| Reinicio | Detener por acceso directo, iniciar de nuevo | Mismas cuentas abiertas, credenciales y datos; no nueva semilla destructiva |

Los pagos de tarjeta y los datos de cliente son sintéticos; no introducir datos personales, tarjetas reales ni certificados. DONE del simulador no es una prueba de impresión física o apertura de cajón.

## Revisión visual y del lanzador

- Escritorio 1280×720 y anchura estrecha: textos legibles, navegación accesible, formularios sin solapamiento ni desplazamiento horizontal accidental. El scroll del menú debe permitir llegar a Equipo, Auditoría y Soporte.
- Estados vacíos, errores de credencial, formularios inválidos y acceso denegado deben mostrar una explicación. La validación no puede reemplazarse con alertas de éxito genéricas.
- El inicio habitual mediante acceso directo debe ser silencioso salvo preparación o error; no dejar una consola permanente. Mostrar errores en diálogo con la ruta del log y una acción concreta.
- Si falta Python/dependencias, el mensaje debe explicar qué componente falta y remitir a la guía; no cerrar una ventana inmediatamente sin feedback ni instalar paquetes silenciosamente.
- Si 8000 pertenece a otro servicio, informar sin cerrarlo. Si ya existe esta DEMO, reutilizar solo la identidad verificada y abrir el navegador, sin segundo servidor.
- La parada exitosa debe indicar que la DEMO se detuvo. Si ya estaba parada, decirlo sin error alarmista. Un PID obsoleto o un timeout no debe provocar la terminación de un proceso ajeno.
- La apertura del archivo de credenciales debe ser una acción explícita o estar explicada en el primer inicio para no confundir la ventana de texto con la aplicación. Evitar abrirlo en cada arranque.
- La reinicialización debe exigir confirmación literal y explicar que afecta exclusivamente a la DEMO; detener primero. La recuperación de credenciales no debe borrar ventas ni reinicializar la base.

## Evidencia mínima para el cierre

Registrar Windows probado, ubicaciones reales de los dos `.lnk`, dirección y PID propios, HTTP y estáticos, doble inicio, puerto ajeno, parada/reinicio y permanencia de un Python independiente. Para la navegación, registrar rol, pantalla/acción, resultado y captura saneada cuando aporte información. Diferenciar ejecución automatizada Chromium de comprobación manual mediante acceso directo. Mantener pendientes las validaciones que no se hayan ejecutado; no extrapolar a Windows 10 y Windows 11 sin probar ambos.

## Ejecución del coordinador, 15-11-2026

Se ejecutó Chromium contra Waitress real con los cuatro usuarios generados y scopes correctos. Acceso, navegación por roles, cobro efectivo, cambio, factura TEST y simulador comprobados; capturas revisadas. Persistencia A2 comprobada tras reinicio. Los apartados pendientes del checklist original que describen más acciones (p.ej., descuentos, cierre, copia o interacción humana táctil) no se atribuyen a esta sesión: mantienen la cobertura de las suites existentes y quedan como guía para el usuario. Evidencia concreta: ../evidence/windows-demo-browser.json y GUIA_WINDOWS_DEMO.md. Accesos y BAT reales ejecutados; sin envíos AEAT ni hardware físico.
