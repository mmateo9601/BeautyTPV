# Contrato documental de la Fase 11

Fecha: 15-11-2026. Base: repositorio existente tras la DEMO Windows. La versión de producto es `0.1.0` en `pyproject.toml`; no se crea una versión estable ni se publica un release. El propósito es documentar código y evidencias reales, sin modificar arquitectura ni comportamiento funcional.

## Propiedad exclusiva

| Responsable | Archivos propios |
|---|---|
| architect | `docs/arquitectura/ARQUITECTURA.md`, `docs/arquitectura/DECISIONES_TECNICAS.md`, este contrato |
| backend | `docs/arquitectura/MODELOS_DATOS.md`, `docs/arquitectura/FLUJOS_NEGOCIO.md`, cinco documentos de `docs/desarrollo/` |
| frontend | Tres manuales en `docs/manuales/`, `docs/screenshots/`, `scripts/capture_documentation.py` |
| security | `docs/arquitectura/SEGURIDAD.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`; no inventar responsables ni canales |
| fiscal | `docs/integraciones/VERIFACTU.md` |
| hardware | `docs/integraciones/HARDWARE.md` |
| devops | Seis documentos en `docs/instalacion/` y `docs/integraciones/SQLITE.md` |
| qa | `docs/DOCUMENTATION_AUDIT.md`, herramientas/pruebas documentales propias acordadas con el coordinador |
| coordinador | `README.md`, `docs/README.md`, `docs/FUNCIONALIDADES.md`, documentos legales e inventario de terceros, `CHANGELOG.md`, `RELEASE_PROCESS.md`, `.env.example`, `.gitignore`, `.editorconfig`, estado/release e integración |

Ningún propietario escribe archivos ajenos mientras su responsable esté activo. Los cambios de nombres de captura se comunican antes de enlazarlos. El coordinador integra y corrige tras la entrega. Cada agente aporta resultados verificables y comunica las comprobaciones efectivamente ejecutadas.

## Reglas de contenido

- Enlaces relativos desde cada documento a su destino real; las imágenes usan texto alternativo. `docs/README.md` es el índice canónico; los documentos históricos permanecen para trazabilidad, sin duplicar manuales completos.
- Los manuales nuevos explican la interfaz actual, roles, elevación y scopes. Operaciones de restauración/actualización reales son offline; la pantalla prepara/verifica y no ejecuta una consola arbitraria.
- Los comandos deben corresponder a argumentos reales de scripts/comandos existentes. No mostrar secretos de la instancia del usuario ni usar contraseñas fijas como ejemplo operativo.
- Capturas nuevas de una DEMO independiente: datos sintéticos, sin alterar la DEMO actual del usuario ni la SQLite principal. Escritorio1440×900, tablet820×1180 y móvil390×844 donde proceda. Conservar procedencia y parámetros de generación.
- Cada módulo distingue implementación local, validación externa pendiente y fuera de V1. Portal Cliente, agenda y reservas no están implementados. No ampliar fiscalidad ni prometer hardware físico probado.
- Fiscalidad productiva sigue bloqueada. Las fuentes normativas/licencias se citan desde fuentes oficiales; una consulta pública no acredita homologación ni prueba de remisión.
- No se crea `LICENSE`, copyright de titular inventado, etiqueta ni publicación. Licencia principal y titular siguen pendientes de decisión explícita. El inventario de dependencias debe conservar versión, origen, expresión/evidencia de licencia, hashes y revisiones pendientes.
- Los cambios de configuración del repositorio no borran datos ni reescriben historia Git. No añadir dependencias para documentos si las herramientas disponibles bastan.

## Gate de revisión

1. Trazar pantallas/rutas/modelos/servicios a código real y metadatos actuales.
2. Verificar enlaces locales, imágenes, dimensiones y render de Markdown/Mermaid.
3. Contrastar roles y comandos con código y pruebas; separar comandos leídos de los realmente ejecutados.
4. Revisar capturas sintéticas y ausencia de secretos.
5. Auditar licencias de paquetes, recursos, fuentes e iconos, sin atribuir licencia al producto por transitividad.
6. Mantener las pruebas existentes y registrar los resultados actuales; no reutilizar las cifras históricas como ejecución de esta fase.
7. Registrar bloqueos externos y decisiones del propietario; commits locales organizados, sin tags/releases públicos.
