# Evidencias visuales de QA

Datos completamente sintéticos; entorno TEST, sin validez fiscal productiva.

- `floor-desktop.png`: plano real en Chromium, 1440×1000, secciones A y B.
- `ticket-tablet.png`: cuenta persistente con una manicura, viewport 900×1180;
  captura completa con catálogo, cliente, líneas, total y formulario de cobro.
- `invoice-test.pdf`: respuesta PDF real de `/facturas/1/pdf/` del E2E de efectivo.
- `invoice-test.png`: primera página del PDF, renderizada con Poppler a 1500 px.

Revisión visual QA: textos y cifras legibles, sin recortes ni solapamientos en estas
capturas; factura de una página, total 12,10 EUR, base 10,00 y cuota 2,10. El QR se
ha renderizado, pero **no se ha escaneado físicamente ni impreso en papel de 80 mm**.

Comandos de regeneración:

```powershell
.venv/Scripts/python -m pytest tests/e2e/test_browser.py -q --browser chromium
pdftoppm -f 1 -singlefile -scale-to 1500 -png docs/evidence/invoice-test.pdf docs/evidence/invoice-test
```

El navegador requiere permiso de lanzamiento de procesos en este host Windows.
Poppler avisó de fuentes de sustitución Symbol/ArialUnicode; la imagen final fue
inspeccionada visualmente y no muestra glifos rotos en el documento de prueba.
