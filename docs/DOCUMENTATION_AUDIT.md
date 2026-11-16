# Auditoría independiente de documentación — Fase 11

Fecha: 16-11-2026. Producto `0.1.0` según `pyproject.toml`. Se revisó documentación frente al código existente; este informe no declara un lanzamiento estable ni aprobación fiscal/legal. El coordinador integra el resultado global de pruebas en [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md) y [RELEASE_REPORT](RELEASE_REPORT.md).

## Resultado por requisito

| Requisito | Estado | Evidencia y alcance real |
|---|---|---|
| README e índice navegable | COMPLETO | [README principal](../README.md), [índice documental](README.md); enlaces locales verificados por `scripts/audit_documentation.py` |
| Manuales de empleado, Administrador y Superadmin | COMPLETO | [Usuario](manuales/GUIA_USUARIO.md), [Administrador](manuales/GUIA_ADMINISTRADOR.md), [Superadmin](manuales/GUIA_SUPERADMIN.md); procedimientos y restricciones contrastados con vistas, formularios y servicios |
| Arquitectura, datos, flujos y decisiones | COMPLETO | [Arquitectura](arquitectura/ARQUITECTURA.md), [modelos](arquitectura/MODELOS_DATOS.md), [flujos](arquitectura/FLUJOS_NEGOCIO.md), [decisiones](arquitectura/DECISIONES_TECNICAS.md); separación de trabajadores normales/DEMO y documentos inmutables real |
| Desarrollo, configuración y pruebas | COMPLETO | [Guía de desarrollo](desarrollo/GUIA_DESARROLLADOR.md), [entorno](desarrollo/ENTORNO_DESARROLLO.md), [pruebas](desarrollo/PRUEBAS.md); referencias a scripts/argumentos existentes y distinción desarrollo/DEMO/producción |
| Roles y seguridad | COMPLETO | [Seguridad](arquitectura/SEGURIDAD.md), [matriz](ROLE_PERMISSION_MATRIX.md), `accounts.permissions`, `SupportPIIMiddleware`, `support.services`; cuatro roles jerárquicos, contraseña elevada10min y autorización20min, PII de Superadmin por otro aprobador. No se afirma MFA independiente ni cifrado integral SQLite |
| Hardware y fiscalidad local | COMPLETO | [Hardware](integraciones/HARDWARE.md), [VERI*FACTU](integraciones/VERIFACTU.md); drivers/colas implementados, escenario fiscal explícito y TEST separado de aceptación oficial |
| Instalación y operaciones Windows | COMPLETO | [Instalación](instalacion/INSTALACION_WINDOWS.md), [DEMO](instalacion/ARRANQUE_DEMO.md), [despliegue](instalacion/DESPLIEGUE_LOCAL.md), [backup](instalacion/BACKUP_RESTORE.md), [updates](instalacion/ACTUALIZACIONES.md); restore/update reales son offline, no una consola web |
| Capturas reales e integridad | COMPLETO | [Manifest de capturas](screenshots/manifest.json):38PNG, procedencia Chromium/Waitress e instancia temporal independiente; hashes, dimensiones exactas y rol/ruta verificados por auditor. La revisión visual concreta corresponde también al coordinador |
| Render Markdown/Mermaid local | COMPLETO | [Evidencia del render](evidence/documentation-render.json):102 documentos, 13 diagramas Mermaid y 35 imágenes renderizadas sin errores locales; runtime externo documentado, sin dependencia añadida al producto |
| Render remoto GitHub | BLOQUEADO EXTERNO | No se publicó contenido ni se ejecutó el renderizador remoto. La sintaxis GFM y el render local no prueban por sí solos ese servicio externo |
| Enlaces, anclas, imágenes y estructura | COMPLETO | [Resultado ejecutable](evidence/documentation-audit.json); incluye documentos históricos, referencias Markdown, bloques de código, anclas y tablas. Los ejemplos/prefijos no se confunden con pantallas reales |
| Comandos de instalación/operación | COMPLETO |13invocaciones no mutantes `--help` en [auditoría JSON](evidence/documentation-audit.json), argumentos contrastados con argparse/PowerShell. No se ejecutaron restores/updates contra un negocio real como parte de la revisión documental; sus ensayos previos están en [evidencias](evidence/README.md) |
| Inventario de licencias y avisos | COMPLETO | [Manifest](legal/DEPENDENCY_LICENSES.json), [avisos](../THIRD_PARTY_NOTICES.md):34paquetes fijados y2componentes vendorizados; hashes del lock, bundles, textos originales y archivos vendor contrastados independientemente |
| Permisos legales de distribución | BLOQUEADO EXTERNO | Licencia principal `NOASSERTION`, titular y elección pendientes; no existe LICENSE inventado.10componentes requieren revisión adicional del artefacto final. El inventario no constituye dictamen de compatibilidad ni autorización de redistribución |
| Secretos y datos personales | COMPLETO | Capturas de datos sintéticos y credenciales excluidas según manifest; escaneo de asignaciones largas/llaves privadas sin valores en el informe. No se incorporan certificados ni secretos de la DEMO del usuario. Esto no equivale a un detector universal de PII |
| Funcionalidad y pruebas preservadas | COMPLETO | No se modificó runtime por esta fase documental. [Regresión actual](evidence/phase11-tests.xml): **900 PASS en 369,16s, 14 Chromium, cero fallos y dos avisos conocidos**. Las seis pruebas nuevas del auditor están incluidas; tras el parser final se repitieron seis PASS en 0,28s y QA obtuvo seis PASS en 0,30s |
| Ejecución CI remota y plataformas no probadas | BLOQUEADO EXTERNO | `.github/workflows/ci.yml` declara Ubuntu, mientras algunos tests DEMO usan WinAPI. Se documenta la limitación; no se atribuye una ejecución remota ni Windows10 físico no realizada |
| Acuses AEAT, declaración firmada y hardware físico | BLOQUEADO EXTERNO | Sin certificado/autorización/dispositivo disponible: no se confunden GET públicos de esquemas, SOAP sintético ni simulador con homologación o impresión/cajón reales |

## Comprobaciones independientes y correcciones

Resultado final: **COMPLETO, cero errores, 102 Markdown, 1205 enlaces, 38 capturas, 61 referencias de rutas y 13 comandos de ayuda**. Se ejecutó el auditor contra el árbol completo. La primera pasada encontró20referencias pendientes:17enlaces dirigidos a este informe todavía no creado y3referencias que necesitaban distinguir su alcance. `/hardware/` es un prefijo `include` real sin vista índice; `/admin/` está mencionado expresamente como ruta **no publicada** y su ausencia se confirma con resolver; `/jobs/<id>` es el handler del bridge local8766, no una URL de Django. El auditor conserva estas distinciones con evidencia de código; no oculta rutas de pantalla desconocidas.

La adaptación inicial al esquema de licencias descubrió que `notice_bundle` es un objeto y no una ruta textual. Se corrigió el auditor para verificar `file`, SHA256 del bundle y cada bloque original por longitud/hash, además de los2vendors y el lock normalizado. Este error de integración no se atribuye al producto.

Las6pruebas adversariales de [test_documentation_tools.py](../tests/test_documentation_tools.py) comprueban enlaces/anclas ausentes, imagen sin alternativa, fence incompleto, headings duplicados, referencias, pipes dentro de código, alteración de hash/dimensiones/procedencia de capturas, bundle de licencia manipulado y asignación de secreto sin divulgarlo. Primera ejecución: **6PASS,0,46s**; resultado integrado actual registrado por el coordinador.

## Reproducción segura

Desde la raíz, en el entorno Python existente:

```powershell
.venv\Scripts\python.exe scripts\audit_documentation.py --output docs/evidence/documentation-audit.json --run-help
.venv\Scripts\python.exe scripts\license_inventory.py --verify
.venv\Scripts\python.exe -m pytest -q tests/test_documentation_tools.py
```

El auditor no abre SQLite de negocio ni ejecuta órdenes destructivas. Resolver URL verifica existencia, no autorización por sí sola; los permisos se contrastan con código y la matriz de tests existente. Los enlaces HTTP externos no se solicitan automáticamente: las fuentes primarias fiscales y legales se revisaron separadamente y están citadas en sus documentos.

No se borraron datos del usuario, no se alteró su historial Git ni se generaron tags/releases públicos. Las decisiones del titular y las validaciones externas anteriores permanecen explícitamente pendientes, con instrucciones en [licencias](legal/OPCIONES_LICENCIA.md) y [proceso de release](../RELEASE_PROCESS.md).
