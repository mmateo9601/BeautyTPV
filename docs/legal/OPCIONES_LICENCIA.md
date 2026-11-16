# Licencia principal: decisión pendiente

Revisión documental: 16-11-2026. El repositorio no tiene una licencia principal elegida ni un titular confirmado para redactar su aviso. **No se crea `LICENSE`, no se asigna MIT/GPL/Apache y no se declara BeautyTPV open source.** `NOASSERTION` en el manifiesto significa que esta fase no atribuye una licencia al producto.

La reutilización técnica del código y su documentación no concede por sí misma permisos de redistribución. La ausencia de licencia no equivale a dominio público; deben comprobarse los derechos del titular y de las contribuciones. Véase la explicación de [GitHub/Choose a License](https://choosealicense.com/no-permission/). Esta comparación sirve para preparar la decisión, no sustituye la revisión jurídica del caso.

## Alternativas

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
| Python, herramientas build y sistema operativo | Si se redistribuyen, inventariar sus versiones y bibliotecas incluidas. `setuptools>=75` es requisito de build; no se inventa una versión persistente cuando el build fue aislado |
| XSD/WSDL/documentos AEAT | Acceso público no significa licencia MIT ni autorización para cualquier uso de logos/textos. Conservar procedencia y comprobar condiciones del recurso |

La coexistencia de varios componentes no permite emitir un dictamen general de compatibilidad sin conocer el paquete final, las modificaciones, el modo de vinculación y la jurisdicción aplicable. El manifiesto marca las revisiones manuales; no constituye una aprobación legal ni un SBOM exhaustivo de todos los binarios del equipo.

## Datos necesarios para cerrar la decisión

1. Identificar al titular real y confirmar su autorización sobre código, documentación, capturas y contribuciones.
2. Elegir expresamente propietario/comercial, MIT, Apache 2.0, GPLv3 u otra opción tras revisar sus consecuencias.
3. Definir cómo se distribuye: repositorio autorizado, paquete de actualización, instalador con Python/navegador o instalación gestionada. Cada artefacto cambia el inventario necesario.
4. Resolver las revisiones señaladas, conservar avisos y, cuando corresponda, preparar acceso al código fuente de terceros.
5. Aprobar nombre del titular, años/datos del aviso y condiciones comerciales/soporte reales. No utilizar nombres o correos inventados.
6. Solo entonces redactar `LICENSE`, metadatos de licencia y avisos del producto coherentes; revisar contribuciones y contrato de distribución.

Hasta recibir esa elección, la documentación técnica queda preparada y la **autorización de distribución del producto sigue PENDIENTE del propietario**. No se publica una licencia por defecto ni se crea una release pública.
