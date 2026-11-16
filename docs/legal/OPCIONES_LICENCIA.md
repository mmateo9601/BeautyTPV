# Licencia elegida: GNU AGPLv3

Decisión expresa del responsable del repositorio: 16-11-2026. BeautyTPV adopta **GNU Affero General Public License, versión 3 únicamente (`AGPL-3.0-only`)**. El [texto íntegro](../../LICENSE) se obtuvo de [GNU](https://www.gnu.org/licenses/agpl-3.0.txt) y no contiene cláusulas añadidas.

Se permite usar, modificar y distribuir el software, incluso comercialmente, sujeto a la licencia. La entrega de código fuente correspondiente al distribuir y la oferta a usuarios remotos de versiones modificadas se rigen por AGPLv3, especialmente secciones 4–6 y 13. **Enviar mejoras mediante PR al repositorio original es recomendado, no obligatorio**, conforme a la opción elegida por el usuario. No se ha añadido una condición upstream a una licencia estándar.

El alcance, las fuentes de la versión exacta, las atribuciones y el procedimiento de distribución se explican en [SOURCE_CODE](../../SOURCE_CODE.md). Cada contribuyente conserva sus derechos; no se deduce una identidad jurídica del nombre Git ni se inventa un copyright consolidado. Los componentes de terceros mantienen sus condiciones y avisos. La elección de AGPL no constituye revisión jurídica del instalador final ni validación fiscal.

## Comparación conservada para referencia

| Opción | Uso y redistribución en términos generales | Obligaciones y consecuencias | Qué debe decidir el propietario |
|---|---|---|---|
| Propietario/comercial | Los permisos se conceden mediante un acuerdo redactado para el producto; pueden limitar instalaciones, distribución o modificaciones | Definir derechos, mantenimiento, actualizaciones, garantías, protección de datos, jurisdicción y tratamiento de contribuciones; mantener obligaciones independientes de terceros | Titular, modalidad comercial, alcance autorizado, condiciones de soporte y contratos |
| MIT | Permite amplios usos, modificación y redistribución, incluso comercial | Conservar el aviso de copyright y permiso; incluye exclusión de garantías. No obliga por sí sola a publicar modificaciones | Aceptar reutilización amplia, atribución y la ausencia de una concesión de patentes expresa como la de Apache |
| Apache 2.0 | Permisiva, con concesión de copyright y patentes bajo sus condiciones | Entregar licencia, conservar avisos pertinentes, identificar cambios y reproducir NOTICE cuando exista; las marcas no quedan licenciadas automáticamente | Revisar patentes, avisos, marcas y política de contribuciones |
| GPLv3 | Permite uso y distribución comercial con condiciones de copyleft al transmitir obras cubiertas | La distribución de objetos/binarios exige cumplir las vías de entrega del código fuente correspondiente; preservar licencia/avisos y derechos de receptores | Determinar qué constituye obra cubierta/combinación y si encaja con el modelo de distribución deseado |

Fuentes de los términos: [MIT, OSI](https://opensource.org/license/mit), [Apache 2.0, ASF](https://www.apache.org/licenses/LICENSE-2.0), [GPLv3, GNU](https://www.gnu.org/licenses/gpl-3.0.html). Las licencias son textos versionados; una traducción explicativa no reemplaza sus términos originales. Elegir GPLv3 no significa prohibir vender el programa, y elegir una licencia permisiva no elimina las obligaciones de terceros.

## Dependencias: no hay compatibilidad automática

El inventario técnico está en [THIRD_PARTY_NOTICES](../../THIRD_PARTY_NOTICES.md), el [manifiesto verificable](DEPENDENCY_LICENSES.json) y los textos originales agregados en `third-party/`. Versiones, metadatos, hashes y avisos se obtuvieron de las distribuciones instaladas que coinciden con `requirements.lock.txt`; no se instaló ninguna dependencia nueva.

| Caso real | Revisión requerida antes de distribuir |
|---|---|
| Bibliotecas MIT/BSD/Apache/ZPL y Bootstrap MIT/HTMX 0BSD | Cumplir sus propios textos/avisos; no aplicarles la licencia principal de BeautyTPV por transitividad |
| `certifi` MPL-2.0 | Revisar archivos cubiertos y obligaciones de acceso a su fuente al distribuir ejecutables; no asumir que MPL relicencia automáticamente todo el producto. [FAQ oficial Mozilla](https://www.mozilla.org/en-US/MPL/2.0/FAQ/) |
| `cryptography` y `packaging`, licencias alternativas | Elegir una alternativa permitida y conservar los avisos pertinentes; revisar bibliotecas binarias incorporadas |
| `python-slugify` y `text-unidecode` | Los pins ya existen; comprobar si se distribuyen/necesitan. `text-unidecode` ofrece alternativas Artistic/GPL en su texto; no resolver esa elección mediante un classifier abreviado |
| Fuentes de `reportlab` | El wheel contiene Bitstream Vera y DarkGarden (GPL-2.0-or-later); no describir todo su contenido como BSD ni suponer una excepción de incrustación no revisada |
| `lxml`, `pillow` y sus wheels | Los avisos enumeran componentes, codecs, recursos y condiciones adicionales. Revisar el artefacto concreto, no solo el nombre del paquete |
| Playwright, Node y Chromium | Conservar avisos del driver y revisar el navegador/build que se vaya a empaquetar. Los navegadores descargados fuera del repo no están incluidos en este inventario binario completo |
| Python, herramientas build y sistema operativo | Si se redistribuyen, inventariar sus versiones y bibliotecas incluidas. `setuptools>=77` es requisito de build; no se inventa una versión persistente cuando el build fue aislado |
| XSD/WSDL/documentos AEAT | Acceso público no significa licencia MIT ni autorización para cualquier uso de logos/textos. Conservar procedencia y comprobar condiciones del recurso |

La coexistencia de varios componentes no permite emitir un dictamen general de compatibilidad sin conocer el paquete final, las modificaciones, el modo de vinculación y la jurisdicción aplicable. El manifiesto marca las revisiones manuales; no constituye una aprobación legal ni un SBOM exhaustivo de todos los binarios del equipo.

## Preparación y obligaciones al distribuir

1. Conservar LICENSE, avisos de autoría y condiciones de terceros; comprobar derechos sobre cada aportación.
2. Entregar el código correspondiente de la versión exacta mediante las modalidades de AGPLv3 aplicables. Una PR es un mecanismo de colaboración, no un sustituto de esta obligación.
3. Para versiones modificadas con interacción remota por red, incluida LAN, ofrecer ese código sin cargo a esos usuarios, de forma visible en la interfaz, según la sección 13.
4. Revisar el artefacto concreto: dependencias, fuentes, componentes nativos y herramientas que realmente se redistribuyen. Las diez revisiones especiales del inventario no se declaran aprobadas por elegir AGPL.
5. Definir por separado contactos reales, atribuciones consolidadas y condiciones de soporte si se ofrecen; no son garantías concedidas por la licencia.

No se modifica el texto de GNU ni se crean obligaciones de aportar al upstream, comprar soporte o ceder derechos. Tampoco se publica una etiqueta o release automáticamente.
