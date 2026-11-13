# Hardware ESC/POS y cajón

Estado: implementación y pruebas automatizadas; NO VERIFICADO físicamente. No se ha conectado ninguna impresora ni cajón. DONE significa bytes entregados al driver, no confirmación física de papel o apertura.

## Instalación y operación

Los dispositivos se configuran por Superadmin en soporte. Tipos: TCP (dirección y puerto, normalmente 9100), USB (VID/PID y endpoint de salida), SERIAL (puerto COM y velocidad en campo port), SIMULATOR solo con DEBUG y HARDWARE_SIMULATOR habilitados. Instalar driver/libusb compatible para PyUSB; permisos OS mínimos para dispositivo y base SQLite local. La base de datos nunca se comparte por SMB/NFS.

El bridge recomendado es un servicio local que ejecuta `python manage.py hardware_worker`; `--once` procesa una tanda y termina. Solo accede a impresoras habilitadas de la configuración local. No abre puertos ni ejecuta shell. La cuenta del servicio y ACL del servidor son su autenticación; no utiliza credenciales predeterminadas. El operador no debe tener acceso de escritura a configuración técnica.

Como alternativa de activación local: generar secreto aleatorio fuera del repositorio en BEAUTYTPV_BRIDGE_TOKEN (mínimo 32 caracteres), ejecutar `python manage.py hardware_bridge --port 8766`. Escucha exclusivamente 127.0.0.1. POST `/jobs/<id>` con `Authorization: Bearer ...` y cuerpo vacío procesa solo trabajo ya persistido. No acepta comandos, payloads ni direcciones de dispositivo proporcionadas por HTTP. No exponer directamente; para otro host se requiere transporte TLS y política explícita. No está permitido mover el fichero SQLite a red para un bridge remoto; los dispositivos Ethernet se alcanzan desde servidor.

## Cola y recuperación

El cobro solo encola bytes de impresión en su transacción; no realiza I/O. Un original por factura; copias explícitas identificadas COPIA nunca abren el cajón. Sin impresora configurada el original permanece PENDING. Asignar impresora habilitada y reintentar desde soporte. Se preserva la factura aunque falle el hardware.

El worker reclama PENDING mediante UPDATE condicional y lease; escribe fuera de atomic. Fallo antes de conectar → FAILED, reintento autorizado seguro. Fallo o interrupción durante escritura → UNKNOWN: puede haberse impreso o abierto el cajón. Lease vencido también pasa a UNKNOWN y nunca se reenvía automáticamente. Revisar físicamente y, si procede, solicitar COPIA sin cajón. Nunca repetir el cobro. El transporte TCP/USB/serie no confirma papel físicamente.

Los payloads usan ESC/POS inicialización, página CP858 predeterminada, QR nativo, corte y pulso ESC p. Texto de usuario elimina controles para impedir inyección ESC/POS. Verificar tabla de caracteres, ancho 80mm, comandos QR/corte y pin de cajón en manual del fabricante. No usar pulso incorrecto ni conectar cajón incompatible.

## Seguridad y diagnóstico

Reimpresión requiere rol interno. Tests de impresora/cajón y reintentos requieren SUPERADMIN y sesión elevada en HTTP, más auditoría. Cajón automático exclusivamente con pago CASH real de la venta; tarjeta no abre. La copia desactiva siempre cajón. Configurar firewall para que solo servidor llegue al puerto impresora. No almacenar datos de tarjeta.

Comandos de verificación: `pytest -q tests/test_hardware.py`, `python manage.py hardware_worker --once`. El simulador no crea aceptación AEAT ni prueba física.

## Checklist físico pendiente E14

Registrar fecha, operador, marca, modelo, firmware, conexión, VID/PID/endpoint o dirección, codepage, ancho y cajón compatible. Verificar: ticket 80 mm legible, acentos y euro, importes e impuestos, QR leído con lector independiente, corte, efectivo abre una vez, tarjeta no abre, copia no abre, desconexión antes/durante envío, recuperación UNKNOWN y reinicio worker sin doble apertura. Adjuntar fotos y evidencias sin datos personales. Gate físico BLOQUEADO hasta disponer de dispositivos.
