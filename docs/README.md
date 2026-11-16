# Documentación de BeautyTPV

Índice canónico de la documentación0.1.0. El programa sigue instalado por empresa con SQLite local. Las guías describen código existente; no constituyen una declaración de conformidad fiscal ni de hardware físico probado.

Empiece por el manual de su rol. Para usar la DEMO sin terminal habitual, consulte Arranque DEMO. Para contribuir o distribuir, revise desarrollo, seguridad, avisos y la licencia AGPLv3.

## Manuales

| Documento | Contenido |
|---|---|
| [GUIA_USUARIO](manuales/GUIA_USUARIO.md) | Operativa diaria, cuentas y cobros |
| [GUIA_ADMINISTRADOR](manuales/GUIA_ADMINISTRADOR.md) | Configuración y gestión del salón |
| [GUIA_SUPERADMIN](manuales/GUIA_SUPERADMIN.md) | Soporte, dispositivos, mantenimiento y permisos |

## Arquitectura

| Documento | Contenido |
|---|---|
| [ARQUITECTURA](arquitectura/ARQUITECTURA.md) | Módulos y dependencias reales |
| [MODELOS_DATOS](arquitectura/MODELOS_DATOS.md) | 35 modelos propios, relaciones y conservación |
| [FLUJOS_NEGOCIO](arquitectura/FLUJOS_NEGOCIO.md) | Cuentas, venta, documentos y colas |
| [SEGURIDAD](arquitectura/SEGURIDAD.md) | Roles, elevación, PII y amenazas |
| [DECISIONES_TECNICAS](arquitectura/DECISIONES_TECNICAS.md) | Índice ADR y decisiones verificadas |

## Desarrollo

| Documento | Contenido |
|---|---|
| [GUIA_DESARROLLADOR](desarrollo/GUIA_DESARROLLADOR.md) | Incorporación al proyecto |
| [ENTORNO_DESARROLLO](desarrollo/ENTORNO_DESARROLLO.md) | Python, variables y perfiles |
| [PRUEBAS](desarrollo/PRUEBAS.md) | Servicios, permisos, Chromium y gates |
| [CONVENCIONES](desarrollo/CONVENCIONES.md) | Código, transacciones y documentación |
| [EXTENSIONES](desarrollo/EXTENSIONES.md) | Añadir funciones sin romper contratos |

## Integraciones

| Documento | Contenido |
|---|---|
| [VERIFACTU](integraciones/VERIFACTU.md) | Escenario fiscal implementado y límites externos |
| [HARDWARE](integraciones/HARDWARE.md) | ESC/POS, cajón, agentes y recuperación |
| [SQLITE](integraciones/SQLITE.md) | Persistencia, concurrencia y backups |

## Instalación y operaciones

| Documento | Contenido |
|---|---|
| [INSTALACION_WINDOWS](instalacion/INSTALACION_WINDOWS.md) | Instalación técnica y requisitos |
| [ARRANQUE_DEMO](instalacion/ARRANQUE_DEMO.md) | Accesos Windows y usuarios sintéticos |
| [DESPLIEGUE_LOCAL](instalacion/DESPLIEGUE_LOCAL.md) | Waitress, TLS y servicio local |
| [BACKUP_RESTORE](instalacion/BACKUP_RESTORE.md) | Copia, restauración offline y conciliación |
| [ACTUALIZACIONES](instalacion/ACTUALIZACIONES.md) | Preflight y rollback de código |
| [SOLUCION_PROBLEMAS](instalacion/SOLUCION_PROBLEMAS.md) | Diagnóstico por síntomas |

## Producto, calidad y propiedad

| Documento | Contenido |
|---|---|
| [FUNCIONALIDADES](FUNCIONALIDADES.md) | Características por rol/menú/estado |
| [DOCUMENTATION_AUDIT](DOCUMENTATION_AUDIT.md) | Auditoría de esta fase y evidencias |
| [OPCIONES_LICENCIA](legal/OPCIONES_LICENCIA.md) | AGPLv3 elegida y comparación histórica |
| [LICENSING_REPORT](legal/LICENSING_REPORT.md) | Verificación de licencia, metadatos y paquetes |
| [DEPENDENCY_LICENSES](legal/DEPENDENCY_LICENSES.json) | Inventario verificable de terceros |
| [manifest](screenshots/manifest.json) | Procedencia, tamaños y hashes de capturas |

## Documentos profesionales de la raíz

[Portada](../README.md) · [Contribuciones](../CONTRIBUTING.md) · [Conducta](../CODE_OF_CONDUCT.md) · [Seguridad](../SECURITY.md) · [Soporte](../SUPPORT.md) · [Changelog](../CHANGELOG.md) · [Proceso de release](../RELEASE_PROCESS.md) · [Avisos de terceros](../THIRD_PARTY_NOTICES.md) · [Licencia](../LICENSE) · [Código correspondiente](../SOURCE_CODE.md).

La licencia principal es [AGPL-3.0-only](../LICENSE). Consulte [código fuente y obligaciones](../SOURCE_CODE.md): las PR son recomendadas, no obligatorias. Se conservan las atribuciones existentes sin inventar un titular consolidado. La versión declarada no implica publicación estable ni aprobación de todos los componentes de un instalador. Los textos de terceros mantienen sus condiciones propias.

## Árbol canónico

```text
docs/
  manuales/       GUIA_USUARIO, GUIA_ADMINISTRADOR, GUIA_SUPERADMIN
  arquitectura/   ARQUITECTURA, MODELOS_DATOS, FLUJOS_NEGOCIO, SEGURIDAD, DECISIONES_TECNICAS
  desarrollo/     GUIA_DESARROLLADOR, ENTORNO_DESARROLLO, PRUEBAS, CONVENCIONES, EXTENSIONES
  integraciones/  VERIFACTU, HARDWARE, SQLITE
  instalacion/    INSTALACION_WINDOWS, ARRANQUE_DEMO, DESPLIEGUE_LOCAL, BACKUP_RESTORE,
                  ACTUALIZACIONES, SOLUCION_PROBLEMAS
  legal/          OPCIONES_LICENCIA.md, DEPENDENCY_LICENSES.json, third-party/, upstream/
  screenshots/    PNG reales y manifest.json
  FUNCIONALIDADES.md
  DOCUMENTATION_AUDIT.md
  README.md
```

[Árbol completo de documentación y herramientas de esta fase](phase11/FILE_TREE.txt). Los nombres del árbol abreviado son archivos.md salvo que se indique otra extensión.

## Evidencias y archivo histórico

Los documentos anteriores se conservan por trazabilidad; no sustituyen los manuales canónicos ni convierten cifras históricas en pruebas actuales. Las auditorías, contratos y runbooks originales siguen accesibles. No se borran evidencias ni historia Git.

<details><summary>Índice del archivo documental previo y evidencias explicativas</summary>

- [Matriz de aceptación E01–E16](ACCEPTANCE_MATRIX.md)
- [ADR 001 — Instalación independiente y límites de módulos](ADRs/001-installation-and-modules.md)
- [ADR 002 — Concurrencia e integridad SQLite](ADRs/002-sqlite-and-idempotency.md)
- [ADR 003 — Fiscalidad y efectos externos verificables](ADRs/003-fiscal-and-hardware-gates.md)
- [Auditoría operativa y correcciones integradas](audit/BACKEND_FINDINGS.md)
- [Inventario de implementación](audit/baseline/INVENTARIO.md)
- [Contrato de auditoria](audit/CONTRACTS_AUDIT.md)
- [Inventario de implementación](audit/final/INVENTARIO.md)
- [Auditoría fiscal técnica contra 4ce821e](audit/FISCAL_FINDINGS.md)
- [Auditoría integral de interfaz](audit/FRONTEND_FINDINGS.md)
- [Auditoria hardware — referencia 4ce821e](audit/HARDWARE_FINDINGS.md)
- [Auditoría operativa contra 4ce821e](audit/OPS_FINDINGS.md)
- [Verificación transversal](audit/QA_FINDINGS.md)
- [Auditoría de seguridad de BeautyTPV](audit/SECURITY_FINDINGS.md)
- [Indice de pruebas auditables](audit/TEST_INDEX.md)
- [Copias cifradas y recuperación](BACKUP_RESTORE.md)
- [Consolidación backend: ajustes, catálogo, plano y caja](consolidation/BACKEND.md)
- [Consolidación fiscal — revisión independiente](consolidation/FISCAL.md)
- [Consolidación de dispositivos y preferencias de impresión](consolidation/HARDWARE.md)
- [Inventario de implementación](consolidation/inventory/INVENTARIO.md)
- [Consolidación operativa de soporte](consolidation/OPS.md)
- [Consolidación funcional V1 — inventario y prioridades](consolidation/PLAN.md)
- [QA independiente de consolidación V1](consolidation/QA.md)
- [BEAUTYTPV — PROMPT MAESTRO DE CONSOLIDACIÓN FUNCIONAL Y EVOLUCIÓN V1](consolidation/REQUEST.md)
- [Consolidación de seguridad](consolidation/SECURITY.md)
- [Indice de pruebas de consolidacion](consolidation/TEST_INDEX.md)
- [Contratos de consolidación funcional V1](CONSOLIDATION_CONTRACTS.md)
- [Contratos de integración BeautyTPV V1](CONTRACTS.md)
- [CRUD y transiciones por modulo](CRUD_COVERAGE.md)
- [Borrador para el productor — NO SUSCRITO](DECLARACION_RESPONSABLE_TEMPLATE.md)
- [Contrato de ejecución DEMO Windows](demo/CONTRACTS.md)
- [Revisión fiscal de la DEMO Windows](demo/FISCAL.md)
- [Revisión de hardware para la DEMO Windows](demo/HARDWARE.md)
- [Verificación independiente del lanzador DEMO Windows](demo/QA.md)
- [Revisión de seguridad — DEMO Windows](demo/SECURITY.md)
- [Servidor dedicado para BeautyTPV DEMO Windows](demo/SERVER.md)
- [Comprobación visual de BeautyTPV DEMO en Windows](demo/UI_CHECKLIST.md)
- [Evidencias visuales de QA](evidence/README.md)
- [Aceptación final de la consolidación funcional V1](FINAL_ACCEPTANCE.md)
- [Cobertura funcional V1](FUNCTIONAL_COVERAGE.md)
- [Fase 1 - Instalacion, seguridad y soporte base](gates/PHASE_1.md)
- [Fase 2 - Plano, catalogo y cuentas](gates/PHASE_2.md)
- [Fase 3 - Cobros, caja y ventas](gates/PHASE_3.md)
- [Fase 4 - Facturacion local inmutable](gates/PHASE_4.md)
- [Fase 5 - VERI*FACTU: implementacion local; gate oficial BLOQUEADO](gates/PHASE_5.md)
- [Fase 6 - Hardware: simulador verificado; gate fisico BLOQUEADO](gates/PHASE_6.md)
- [Fase 7 - Soporte operativo, backup, restore y actualizaciones](gates/PHASE_7.md)
- [Fase 8 - Integracion E2E y release condicionada](gates/PHASE_8.md)
- [BeautyTPV DEMO en Windows 10/11](GUIA_WINDOWS_DEMO.md)
- [Hardware ESC/POS y cajón](HARDWARE.md)
- [Estado de implementación — 13-11-2026](IMPLEMENTATION_STATUS.md)
- [Instalación local](INSTALL.md)
- [Contrato documental de la Fase 11](phase11/CONTRACTS.md)
- [Evolución futura de SQLite](POSTGRESQL_FUTURE.md)
- [Informe de release — BeautyTPV 0.1.0](RELEASE_REPORT.md)
- [Matriz de roles, permisos, rutas y servicios](ROLE_PERMISSION_MATRIX.md)
- [Seguridad y operación local](SECURITY.md)
- [Ajustes disponibles y restricciones](SETTINGS_COVERAGE.md)
- [Operación Superadmin](SUPERADMIN.md)
- [Operaciones reales de Superadmin](SUPERADMIN_COVERAGE.md)
- [Revisión de interfaz de BeautyTPV V1](UI_REVIEW.md)
- [Actualización verificada y rollback](UPDATE.md)
- [Manual de uso BeautyTPV](USER_MANUAL.md)
- [Trazabilidad fiscal — BeautyTPV](VERIFACTU_COMPLIANCE.md)

</details>

Evidencias de ejecución en [evidence/README](evidence/README.md). Las capturas actuales se consultan desde los manuales y el manifest; los JUnit/JSON de cada fase indican exactamente su alcance. La publicación/renderización remota en GitHub no se da por verificada sin publicarla.
