# Avisos de terceros — BeautyTPV

Este documento identifica componentes reales del repositorio y del entorno fijado. **No concede una licencia al producto BeautyTPV**, cuyo titular/licencia principal siguen pendientes. Los avisos originales mantienen sus propios titulares, no inventados para este proyecto.

## Procedencia y verificación

- [Manifiesto JSON](docs/legal/DEPENDENCY_LICENSES.json):34paquetes Python fijados,2vendors, herramientas e intérprete observado.
- [Lock](requirements.lock.txt) y [opciones pendientes](docs/legal/OPCIONES_LICENCIA.md).
- Textos originales agregados por paquete en `docs/legal/third-party/`: cada bloque indica origen y SHA256 de sus bytes. El manifiesto incluye además el SHA256 del archivo agregado.
- Las rutas de origen son lógicas de site-packages; no se exponen rutas privadas del usuario. La comparación del lock normaliza CRLF a LF; licencias/vendor se preservan sin conversión en .gitattributes.
- No es un dictamen jurídico ni un SBOM completo de cada DLL/browser del equipo. La aprobación de redistribución requiere revisar el artefacto concreto.

```powershell
.venv\Scripts\python.exe scripts\license_inventory.py
.venv\Scripts\python.exe scripts\license_inventory.py --verify
```

No se instalan paquetes. `--fetch-missing` descarga optativamente solo el aviso fijado de [pySerial v3.5](https://raw.githubusercontent.com/pyserial/pyserial/v3.5/LICENSE.txt), ausente en los archivos instalados de su wheel; el texto queda conservado en el repositorio.

## Dependencias Python fijadas

| Paquete | Versión | Licencia / evidencia | Avisos preservados | Revisión especial |
|---|---|---|---|---|
| asgiref | 3.13.0 | BSD-3-Clause | [Texto original](docs/legal/third-party/asgiref.txt) | Revisar condiciones del artefacto al distribuir |
| certifi | 2026.10.23 | MPL-2.0 | [Texto original](docs/legal/third-party/certifi.txt) | MPL-2.0: revisar obligaciones de los archivos cubiertos y acceso a su fuente. |
| cffi | 2.1.1 | MIT-0 | [Texto original](docs/legal/third-party/cffi.txt) | Revisar condiciones del artefacto al distribuir |
| charset-normalizer | 3.5.2 | MIT | [Texto original](docs/legal/third-party/charset-normalizer.txt) | Revisar condiciones del artefacto al distribuir |
| colorama | 0.4.6 | BSD-3-Clause (texto local) | [Texto original](docs/legal/third-party/colorama.txt) | Revisar condiciones del artefacto al distribuir |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause | [Texto original](docs/legal/third-party/cryptography.txt) | Apache-2.0 OR BSD-3-Clause; revisar tambien OpenSSL/bibliotecas incluidas en el wheel. |
| Django | 5.2.19 | BSD-3-Clause | [Texto original](docs/legal/third-party/django.txt) | Revisar condiciones del artefacto al distribuir |
| greenlet | 3.5.6 | MIT AND PSF-2.0 | [Texto original](docs/legal/third-party/greenlet.txt) | Revisar condiciones del artefacto al distribuir |
| idna | 3.20 | BSD-3-Clause | [Texto original](docs/legal/third-party/idna.txt) | Revisar condiciones del artefacto al distribuir |
| iniconfig | 2.3.1 | MIT | [Texto original](docs/legal/third-party/iniconfig.txt) | Revisar condiciones del artefacto al distribuir |
| lxml | 6.1.3 | BSD-3-Clause | [Texto original](docs/legal/third-party/lxml.txt) | LICENSES.txt enumera licencias/componentes adicionales, recursos y binarios; revisar el wheel exacto. |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | [Texto original](docs/legal/third-party/packaging.txt) | Revisar condiciones del artefacto al distribuir |
| pillow | 13.0.0 | MIT-CMU | [Texto original](docs/legal/third-party/pillow.txt) | MIT-CMU declarada; los codecs/binarios del wheel pueden tener avisos adicionales. |
| playwright | 1.65.1 | Apache-2.0 | [Texto original](docs/legal/third-party/playwright.txt) | Incluye driver Node y ThirdPartyNotices. Los navegadores descargados tienen sus propios avisos; no se redistribuyen aqui. |
| pluggy | 1.7.0 | MIT | [Texto original](docs/legal/third-party/pluggy.txt) | Revisar condiciones del artefacto al distribuir |
| pycparser | 3.12 | BSD-3-Clause | [Texto original](docs/legal/third-party/pycparser.txt) | Revisar condiciones del artefacto al distribuir |
| Pygments | 2.21.0 | BSD-2-Clause | [Texto original](docs/legal/third-party/pygments.txt) | Revisar condiciones del artefacto al distribuir |
| pypdf | 7.1.0 | BSD-3-Clause | [Texto original](docs/legal/third-party/pypdf.txt) | Revisar condiciones del artefacto al distribuir |
| pyserial | 3.5 | BSD-3-Clause (licencia upstream v3.5) | [Texto original](docs/legal/third-party/pyserial.txt) | Revisar condiciones del artefacto al distribuir |
| pytest | 9.2.0 | MIT | [Texto original](docs/legal/third-party/pytest.txt) | Revisar condiciones del artefacto al distribuir |
| pytest-django | 4.14.0 | BSD-3-Clause (metadatos/texto local) | [Texto original](docs/legal/third-party/pytest-django.txt) | Revisar condiciones del artefacto al distribuir |
| pytest-playwright | 0.10.0 | Apache-2.0 (texto local) | [Texto original](docs/legal/third-party/pytest-playwright.txt) | Revisar condiciones del artefacto al distribuir |
| python-slugify | 9.1.3 | MIT | [Texto original](docs/legal/third-party/python-slugify.txt) | Pin existente sin dependencia directa en pyproject; revisar necesidad y text-unidecode transitivo. |
| pyusb | 1.3.1 | BSD-3-Clause (texto local) | [Texto original](docs/legal/third-party/pyusb.txt) | Revisar condiciones del artefacto al distribuir |
| qrcode | 8.2 | BSD-3-Clause (texto local; revisar classifiers) | [Texto original](docs/legal/third-party/qrcode.txt) | Los classifiers incluyen Other/Proprietary; el texto LICENSE concreto es la evidencia de sus condiciones BSD. |
| reportlab | 5.1.0 | BSD-3-Clause + licencias de fuentes (revisar) | [Texto original](docs/legal/third-party/reportlab.txt) | Incluye fuentes Bitstream Vera y DarkGarden GPL-2.0-or-later; no tratar todo el wheel como BSD. |
| requests | 2.34.2 | Apache-2.0 | [Texto original](docs/legal/third-party/requests.txt) | Revisar condiciones del artefacto al distribuir |
| ruff | 0.17.5 | MIT | [Texto original](docs/legal/third-party/ruff.txt) | Revisar condiciones del artefacto al distribuir |
| sqlparse | 0.6.1 | BSD-3-Clause (texto local) | [Texto original](docs/legal/third-party/sqlparse.txt) | Revisar condiciones del artefacto al distribuir |
| text-unidecode | 1.3 | Artistic OR GPL (revisar texto exacto) | [Texto original](docs/legal/third-party/text-unidecode.txt) | Licencia dual Artistic/GPL: elegir y cumplir la alternativa pertinente antes de redistribuir. |
| tzdata | 2026.6 | Apache-2.0 | [Texto original](docs/legal/third-party/tzdata.txt) | Metadatos Apache-2.0 y avisos de datos IANA; conservar ambos textos. |
| urllib3 | 2.8.0 | MIT | [Texto original](docs/legal/third-party/urllib3.txt) | Revisar condiciones del artefacto al distribuir |
| waitress | 3.0.2 | ZPL-2.1 | [Texto original](docs/legal/third-party/waitress.txt) | Revisar condiciones del artefacto al distribuir |
| whitenoise | 6.12.0 | MIT | [Texto original](docs/legal/third-party/whitenoise.txt) | Revisar condiciones del artefacto al distribuir |

`runtime-direct`/`development-direct` en JSON describen dependencias declaradas en pyproject; `locked-transitive-or-tool` no decide por sí solo si se redistribuye ese paquete. No se han añadido ni retirado pins en esta fase. Los componentes de desarrollo no se convierten por ello en dependencias necesarias del TPV final.

## Recursos incluidos y externos

| Recurso | Estado y licencia | Evidencia / condición |
|---|---|---|
| Bootstrap5.3.8 | MIT, vendorizado | [LICENSE](static/vendor/bootstrap/LICENSE), hashes de CSS/JS en manifiesto |
| HTMX2.0.8 | 0BSD, vendorizado | [LICENSE](static/vendor/htmx/LICENSE), hashes del JS en manifiesto |
| CSS/JS/plantillas de BeautyTPV y marca textual B | Código del producto, licencia principal pendiente | No se les asigna automáticamente la licencia del framework |
| Iconos del menú | Caracteres Unicode de las plantillas, sin paquete de iconos o fuente descargada en static | Revisar el motor/fuente del equipo si se empaqueta un entorno completo |
| Inter, Segoe UI y Georgia referenciadas en CSS | Referencias a familias del sistema/fallback; no se redistribuyen archivos .ttf/.woff propios en static | No afirmar una licencia de una fuente no incluida |
| Fuentes de ReportLab | Incluidas en el wheel, con licencias propias | [Avisos completos](docs/legal/third-party/reportlab.txt); Bitstream Vera/DarkGarden requieren revisión separada |
| XSD/WSDL AEAT | Recursos oficiales con procedencia y manifest de hashes | [Manifest](schemas/aeat/manifest.json); no se atribuye licencia MIT ni conformidad por descarga pública |
| Capturas de documentación | Chromium real, datos sintéticos de DEMO independiente | [Procedencia](docs/screenshots/manifest.json); no imágenes generadas artificialmente ni datos del salón |
| Navegadores Playwright/Chromium | Descargados fuera del repositorio; no incluidos como binarios aquí | Revisar licencia/avisos del build exacto si se redistribuyen; driver/Node sí tienen avisos preservados |

## Intérprete y herramientas observados

- pip: 26.2.1. [Avisos](docs/legal/third-party/pip.txt). Herramienta local, no dependencia runtime del producto.
- setuptools: versión pendiente del entorno build. Sin versión/artefacto persistente que atribuir. Requisito build no instalado persistentemente; version del entorno build aislado no inventada.
- Python: 3.14.7. [Avisos](docs/legal/third-party/python.txt). Si se redistribuye Python o un instalador completo, revisar tambien sus bibliotecas incorporadas y terminos originales.

## Revisión manual antes de distribuir

La comprobación visual documental utilizó Marked del runtime externo de Codex y un bundle temporal Mermaid11.12.2. No se incluyen estos motores en el producto ni en su lock; la herramienta opcional recibe sus rutas explícitamente. Su procedencia está registrada en [documentation-render-runtime.json](docs/evidence/documentation-render-runtime.json). Revisar sus avisos propios si se decide redistribuirlos.

Diez paquetes tienen observaciones especiales en el manifiesto; también requieren revisión intérprete, build aislado, browsers y recursos oficiales. Prestar atención a MPL2.0(certifi), duales/Artistic/GPL, fuentes de ReportLab, binarios/codecs y avisos del driver Playwright. No se marca compatibilidad universal con una licencia principal aún no elegida.

La licencia principal, titular, condiciones comerciales y canal de soporte se deciden por el propietario. Véanse [OPCIONES_LICENCIA](docs/legal/OPCIONES_LICENCIA.md) y [RELEASE_PROCESS](RELEASE_PROCESS.md). No se ha creado LICENSE ni publicado una release.
