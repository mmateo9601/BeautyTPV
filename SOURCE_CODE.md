# Licencia y código fuente correspondiente

BeautyTPV se licencia bajo **GNU Affero General Public License, versión 3 únicamente (`AGPL-3.0-only`)**. El texto íntegro y sin modificaciones está en [LICENSE](LICENSE). Esta elección se realiza por instrucción expresa del responsable del repositorio el 16-11-2026. Las condiciones vinculantes son las de LICENSE; este documento las explica y no añade restricciones.

## Qué permite y qué exige

- Se permite usar, estudiar, modificar y distribuir el programa, también comercialmente, cumpliendo AGPLv3.
- Al distribuir versiones cubiertas, conserve los avisos y la licencia, identifique sus modificaciones y proporcione el código fuente correspondiente mediante una de las modalidades admitidas por la licencia. No basta enlazar una rama que contenga otra versión.
- Si modifica el programa y permite que usuarios interactúen con esa versión remotamente por una red, ofrezca de forma visible a esos usuarios acceso al código fuente correspondiente de la versión utilizada, sin cargo, conforme a la sección 13. Esto también puede afectar a una instalación en LAN; no se limita a servicios públicos en Internet.
- El uso privado sin distribución ni el supuesto de interacción remota anterior no crea una obligación general de publicar cambios en GitHub.
- Enviar mejoras mediante pull request al repositorio original es **recomendado**, no una obligación adicional de la licencia. Tampoco obliga al mantenedor a aceptarlas o fusionarlas. No se exige inventar mejoras ni ceder su titularidad.

## Repositorio y entrega de fuentes

Repositorio de referencia, identificado por el remoto Git de este proyecto: [mmateo9601/BeautyTPV](https://github.com/mmateo9601/BeautyTPV). Esta referencia no afirma que un commit local ya esté publicado ni garantiza la disponibilidad futura del servicio.

Antes de distribuir o poner en red una versión modificada:

1. Identifique el commit y los cambios adicionales exactos del binario o instalación entregada.
2. Prepare fuente modificable completa, migraciones, plantillas, estáticos propios, configuración de ejemplo, dependencias declaradas e instrucciones/scripts necesarios para construir, instalar y ejecutar esa versión. Incluya el bridge/agente si forma parte de la entrega y la información de instalación cuando la licencia la exija.
3. Incluya LICENSE, avisos de terceros y sus textos. Revise las condiciones de cada componente realmente redistribuido.
4. Facilite ese código conforme a las secciones aplicables de AGPLv3. Para una versión modificada accesible por red, coloque la oferta visible en su interfaz y asegure que la descarga contiene esa misma versión. El repositorio remoto de otra versión o un enlace solo en documentación no reemplazan esa oferta.
5. Compruebe la descarga y conserve la correspondencia entre versión y fuentes durante los plazos que exija la modalidad elegida.

El ZIP de actualización y el wheel son artefactos distintos de una exportación completa del repositorio. Su mera generación no acredita por sí sola entrega del código correspondiente ni conformidad de un instalador completo. No publique `.env`, bases SQLite, copias de seguridad, datos de clientes, certificados, claves, tokens o registros operativos. Los datos de una empresa no se convierten en código fuente por utilizar el programa.

## Alcance, atribución y terceros

La licencia del proyecto cubre las obras originales de BeautyTPV para las que sus titulares conceden estos permisos. Se conservan los avisos de autoría existentes; cada contribuyente mantiene sus derechos. No se atribuye el copyright del software a una identidad deducida del nombre de usuario Git. El copyright de la Free Software Foundation que aparece en LICENSE corresponde al texto de la licencia, no a la autoría de BeautyTPV.

Las dependencias, Bootstrap, HTMX, fuentes y recursos oficiales mantienen sus condiciones propias. Los XSD/WSDL/PDF de AEAT y el esquema XMLDSig de W3C no se relicencian como AGPL por estar en el repositorio. Tampoco se relicencian firmware, drivers del sistema ni dispositivos. Consulte [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md) y el [inventario](docs/legal/DEPENDENCY_LICENSES.json).

La elección de licencia no altera los bloqueos de producción fiscal ni acredita aceptación AEAT, ni garantiza seguridad, ni prueba hardware físico. No se ofrecen garantías adicionales a las de la licencia ni soporte comercial implícito.

Fuentes primarias: [AGPLv3 oficial](https://www.gnu.org/licenses/agpl-3.0.html), especialmente secciones 4–6 y 13, y [FAQ GNU](https://www.gnu.org/licenses/gpl-faq.html). Para contribuir, siga [CONTRIBUTING](CONTRIBUTING.md).
