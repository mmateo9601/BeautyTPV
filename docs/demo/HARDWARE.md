# Revisión de hardware para la DEMO Windows

Revisión estática del 14-11-2026. Propiedad limitada a este documento: no se modificaron módulos funcionales, impresoras ni bases de datos.

## Comportamiento existente comprobado en código

- `apps/hardware/drivers.py::send` acepta `SIMULATOR` únicamente si `settings.DEBUG` y `settings.HARDWARE_SIMULATOR` son verdaderos. Devuelve la longitud del payload, sin conexión TCP/USB/serie ni escritura a dispositivo.
- `apps/support/forms.py::PrinterForm.clean` exige las mismas dos condiciones al configurar una impresora simulada. `Printer.clean` valida configuración, pero no contiene ese guard.
- `apps/hardware/services.py::process_job` reclama la intención persistente mediante actualización condicional, entrega fuera de la transacción y registra estado/evento/auditoría. Con simulador permitido puede finalizar `DONE`, que acredita consumo simulado de bytes, no papel ni cajón físicos.
- `hardware_worker` consume trabajos de impresora habilitada con `terminal` nula. La impresora DEMO debe ser fallback local sin terminal para que este worker la procese. El navegador puede seguir seleccionando una terminal para atribuir operaciones.
- `apps/hardware/agent.py` rechaza expresamente `SIMULATOR`: no se necesita ni debe iniciarse bridge remoto para esta DEMO.
- Copias no abren cajón y una intención `UNKNOWN` no se reenvía automáticamente; estos controles deben conservarse.

## Alternativas revisadas y decisión de integración

El perfil DEMO puede usar `DEBUG=True` y `HARDWARE_SIMULATOR=True` exclusivamente en su configuración aislada, servido por Waitress y ligado a `127.0.0.1`. Esto permite usar los guards y formularios actuales sin cambiar el producto. La petición prohíbe DEBUG en instalaciones productivas; no se debe trasladar este perfil ni sus secretos/datos sintéticos a producción. Mantener configuración productiva y bloqueos fiscales intactos.

Si se decide exigir `DEBUG=False` también a la DEMO, activar solo `HARDWARE_SIMULATOR=True` no basta: el worker fallará y el formulario denegará el simulador. Haría falta una excepción explícita de perfil DEMO en ambos guards, con pruebas que mantengan el rechazo productivo. No se recomienda monkeypatch de drivers, cambiar temporalmente settings compartidos ni inventar estados `DONE` al margen del servicio.

El coordinador eligió esta segunda alternativa: `config.demo_settings` con DEBUG falso, un flag explícito `LOCAL_DEMO_ONLY` y corrección mínima de ambos guards a cargo del coordinador. El driver deberá rechazar cualquier transporte distinto de SIMULATOR mientras ese perfil esté activo. Así se evita que una configuración desde el panel conecte accidentalmente una impresora física; no se modifica el funcionamiento productivo fuera de ese perfil. La revisión estática precedente describe el comportamiento de entrada; la prueba de los guards corregidos corresponde al cierre integrado.

## Validación a realizar por el coordinador

Crear impresora `SIMULATOR` habilitada, sin terminal, en SQLite DEMO. Ejecutar venta TEST, comprobar factura/alta única y trabajo persistente; permitir al worker procesarlo y confirmar evento de simulación/estado. Probar ticket técnico y cajón desde Superadmin elevado con autorización TECHNICAL. No iniciar workers fiscales ni realizar llamadas a AEAT.

Esta revisión no ejecutó esos recorridos; sus resultados reales deben figurar en la guía/evidencia del coordinador. **Impresora física, papel80mm, QR impreso, corte y apertura real de cajón: BLOQUEADO EXTERNO.**

## Cierre integrado del coordinador

La decisión final y pruebas reales están en ../GUIA_WINDOWS_DEMO.md y ../evidence/windows-demo-smoke.json. Perfil config.demo_settings con DEBUG=False, guards específicos de simulación, transportes físicos rechazados y remisión bloqueada. Factura TEST/spool simulado verificados, cero FiscalTransmission. Se preservan límites externos; esta sección supersede recomendaciones preliminares que no se adoptaron.
