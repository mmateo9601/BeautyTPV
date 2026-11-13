# Manual de uso BeautyTPV

## Acceso y plano
Accede en `/acceso/` con usuario y PIN (6–12 dígitos). Los administradores usan contraseña para funciones elevadas. Los intentos fallidos provocan bloqueo temporal. El plano `/tpv/` es el inicio: cada sección agrupa puestos con código y estado escrito, además de color. Pulsa un puesto libre para crear una cuenta o uno ocupado para recuperarla. Volver al plano, cambiar de puesto o recargar conserva las líneas en SQLite.

## Cuenta y cobro
Busca un artículo por nombre o categoría y púlsalo para añadirlo. Guarda los cambios de cantidad; los descuentos requieren permiso. El precio y el IVA quedan capturados en la línea. Un encargado puede anular una cuenta sin emitir, pero nunca borrar una factura.

Abre antes un turno de caja si vas a recibir efectivo. En la cuenta introduce efectivo, tarjeta o ambos; su suma debe coincidir con el total. `Recibido` permite calcular el cambio orientativo. Para tarjeta confirma primero el pago en el datáfono externo y anota su referencia: BeautyTPV registra la confirmación, no realiza el cargo bancario. Confirma el cobro una vez. Ante un fallo de red revisa la cuenta/factura antes de reintentar. La clave idempotente protege el mismo envío.

## Caja
`Caja y turnos` permite abrir con fondo inicial, registrar ingresos o retiradas con motivo y cerrar con efectivo contado. Ingresos, retiradas y cierre requieren autorización. El cierre conserva esperado, contado y diferencia. El saldo incorpora únicamente la parte en efectivo de los cobros, no todo el dinero recibido antes del cambio.

## Catálogo y clientes
El administrador crea o edita servicios/productos, precios IVA incluido y tipo fiscal aplicable. Cambiar un artículo no cambia facturas ya emitidas. Los clientes tienen ficha comercial e historial de ventas, sin portal ni citas en V1. Recoge los datos mínimos necesarios y una base jurídica adecuada.

## Facturas y devoluciones
En Facturas consulta el documento, PDF y estado fiscal. `TEST / SIN VALIDEZ FISCAL PRODUCTIVA` indica pruebas. Un registro pendiente o rechazado no ha sido aceptado por AEAT. Una copia de impresión no repite el cobro ni abre el cajón. La rectificación genera un documento nuevo enlazado al original y requiere motivo y devolución registrada; el original permanece intacto.

## Informes y soporte
Los informes muestran ventas por fechas, cobros e IVA y permiten exportar CSV bajo permisos. Auditoría conserva las acciones relevantes. El Superadmin dispone de soporte protegido con diagnóstico, colas fiscal/impresión y operaciones técnicas auditadas. Las restauraciones y actualizaciones requieren procedimiento de mantenimiento, copia previa y verificación de secuencias fiscales.

## Teclado, táctil y fallos
Los controles tienen etiquetas, foco visible y objetivos táctiles. Usa Tab y Enter; el enlace inicial permite saltar al contenido. El plano se refresca con HTMX cada 20 segundos y funciona con formularios completos sin JavaScript. Bootstrap y HTMX se sirven localmente, sin conexión externa del navegador. Los errores se muestran en texto; si dos terminales cambian la misma cuenta, recarga para obtener su versión actual antes de continuar.

La verificación con AEAT y las pruebas físicas de impresora/cajón se describen únicamente con sus evidencias en RELEASE_REPORT.md. Este manual no constituye prueba de esos dispositivos ni de conformidad fiscal.


En Catálogo, Gestionar categorías permite crear, renombrar y eliminar categorías
sin artículos; las categorías utilizadas están protegidas. Los artículos se
retiran del catálogo desactivándolos, conservando sus snapshots históricos.

En Clientes, un Administrador con identidad confirmada puede exportar CSV y
eliminar una ficha sin historial. Empleados no pueden exportar ni borrar;
las fichas vinculadas a cuentas se conservan protegidas. El CSV neutraliza
fórmulas. Superadmin necesita además la autorización PII independiente.

Soporte permite elegir la impresora de un trabajo pendiente, descargar copias
cifradas, revocar autorizaciones, consultar logs saneados y solicitar subsanación
de un rechazo sin cambiar el registro original. El diagnóstico de red TCP443 se
activa mediante la casilla correspondiente; no envía una factura de prueba.
