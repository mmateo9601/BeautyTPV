# Preparación del repositorio bajo AGPLv3

Fecha: 16-11-2026. Decisión explícita del usuario: **AGPLv3 estándar**, con contribuciones al repositorio recomendadas. Identificador: `AGPL-3.0-only`. No se añade ninguna obligación de PR, cesión de derechos ni cláusula de licencia propia.

| Comprobación | Estado | Evidencia |
|---|---|---|
| Texto oficial completo, sin modificar | COMPLETO | [LICENSE](../../LICENSE), descargado de GNU; [procedencia, tamaño y SHA256](AGPL_PROVENANCE.json) |
| Metadatos Python coherentes | COMPLETO | `pyproject.toml`: expresión SPDX y `license-files`; mínimo de build setuptools77, sin cambios en dependencias runtime |
| Integridad del producto y terceros | COMPLETO | [Inventario](DEPENDENCY_LICENSES.json): licencia/hashes del producto, 34 paquetes y dos componentes web; `license_inventory.py --verify` y auditor independiente |
| Wheel real | COMPLETO | [Verificación de paquete](../evidence/license-package-check.json): construcción aislada satisfactoria, `License-Expression` correcto y 42 archivos legales contrastados byte a byte |
| ZIP de actualización local | COMPLETO | El mismo JSON registra validación de hashes y presencia íntegra de LICENSE, THIRD_PARTY_NOTICES.md y SOURCE_CODE.md; los tres nombres raíz son exactos, no nuevos prefijos de directorio |
| Pruebas de regresión aplicables | COMPLETO | [JUnit](../evidence/license-tests.xml): **62 PASS en 7,51s**, un aviso conocido de override DATABASES. Incluye 20 casos nuevos de licencia, integridad, rutas y empaquetado |
| Documentación, enlaces y atribuciones | COMPLETO | [Auditoría ejecutable de esta modificación](../evidence/license-documentation-audit.json): 104 Markdown, 1249 enlaces, cero errores; README, contribuciones, desarrollo, instalación y release actualizados |
| Revisión de todo componente redistribuido | PARCIAL | Se conservan diez revisiones especiales del inventario y las revisiones de intérprete, herramientas, navegadores y recursos oficiales del artefacto concreto; elegir AGPL no las resuelve automáticamente |
| Publicación remota y release | PENDIENTE | Se preparó el repositorio local y artefactos de comprobación. No se hizo push, tag ni publicación pública |

## Alcance de las comprobaciones

Se utilizaron los ocho especialistas con contrato previo del arquitecto. Backend verificó metadatos/inventario; DevOps corrigió la exclusión de archivos legales del ZIP; frontend revisó las referencias vigentes; seguridad revisó contribuciones, privacidad y derechos; fiscal y hardware confirmaron las condiciones de recursos y componentes ajenos; QA creó pruebas independientes y el coordinador integró y verificó los artefactos.

Los controles dirigidos ejecutados abarcan `test_license_release.py`, `test_documentation_tools.py`, `test_backup.py`, `test_audit_ops.py` y `test_regressions.py`. Las primeras comprobaciones de integración detectaron una colocación incorrecta del bloque del auditor y una fixture sin dependencias; se corrigieron antes de repetir los 62 casos, sin retirar aserciones. Django check, revisión de migraciones, pip check y Ruff pasan.

La suite completa de **900 PASS y 14 Chromium** pertenece al cierre anterior de Fase 11; no se atribuye una nueva ejecución completa a este cambio. No se modifican modelos, migraciones, cobros, fiscalidad ni protocolos de hardware. El cambio de código productivo se limita a admitir los tres archivos legales exactos en actualizaciones, conservando los controles de rutas, hashes, destinos, backup y rollback.

La oferta del código correspondiente de una versión modificada distribuida o accesible por red debe cumplirse en esa entrega según [SOURCE_CODE](../../SOURCE_CODE.md); no se afirma que un commit local ya esté publicado o que se haya añadido una oferta a la interfaz de una instalación ajena. El wheel y el ZIP de actualización no se presentan como un instalador Windows completo.

## Reproducir la preparación

Desde la raíz y con el entorno instalado:

```powershell
.venv\Scripts\python.exe scripts\license_inventory.py --verify
.venv\Scripts\python.exe -m pytest -q tests/test_license_release.py tests/test_documentation_tools.py tests/test_backup.py tests/test_audit_ops.py tests/test_regressions.py
.venv\Scripts\python.exe -m pip wheel --no-deps --wheel-dir tmp/license-build/wheels .
.venv\Scripts\python.exe scripts\package_release.py --version 0.1.0 --output tmp/license-build/BeautyTPV-0.1.0.zip
.venv\Scripts\python.exe scripts\audit_documentation.py --output docs/evidence/license-documentation-audit.json --run-help
```

La construcción del wheel puede descargar herramientas de build en un entorno aislado. Los artefactos de comprobación se conservan en tmp, fuera del control de versiones; sus metadatos, hashes y verificaciones están en el JSON enlazado. Los textos legales propios incluidos en los hashes se conservan con bytes estables mediante `.gitattributes`, junto con los avisos originales de terceros.

Las atribuciones existentes se conservan sin inventar una identidad jurídica. Las dependencias y recursos de terceros, incluido XMLDSig W3C, mantienen sus condiciones propias. Certificado/acuses oficiales AEAT, declaración responsable suscrita y hardware físico siguen sin validación externa; la elección de licencia no modifica esos bloqueos.
