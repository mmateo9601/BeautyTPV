# Historial de cambios

Se registran cambios verificables del repositorio. `0.1.0` es la versión actual de los metadatos; no se atribuye un lanzamiento estable ni una fecha de publicación pública.

## Sin publicar — AGPLv3, 16-11-2026

- Licencia oficial GNU AGPLv3 (`AGPL-3.0-only`) por elección explícita; PR al repositorio recomendadas, no obligatorias.
- Metadatos SPDX, instrucciones de código correspondiente y contribuciones; avisos originales preservados y manifiesto verificable con hashes del producto.
- Corrección del ZIP de actualización para incluir tres archivos legales raíz exactos, sin permitir rutas anidadas bajo sus nombres; wheel con 42 textos legales comprobados.
- 62 pruebas dirigidas aprobadas; [informe de preparación](docs/legal/LICENSING_REPORT.md). No se publica release ni se modifica la versión 0.1.0.

## Sin publicar — Fase 11, documentación profesional

- Manuales de usuario, Administrador y Superadmin, capturas reales y un índice documental por perfiles.
- Arquitectura, modelos, flujos, seguridad, desarrollo, integraciones y operaciones Windows documentados desde código.
- Inventario verificable de licencias/avisos; en aquel cierre la licencia y el titular estaban pendientes y no se creó `LICENSE`. La elección posterior de AGPLv3 se registra arriba.
- Guías de colaboración, soporte, seguridad y proceso de release; no se publican tags/releases ni se cambia el comportamiento funcional.
- Auditoría documental y resultados actuales registrados en `docs/DOCUMENTATION_AUDIT.md`.

## 0.1.0 — evolución del repositorio, sin publicación estable declarada

| Revisión | Cambio verificable |
|---|---|
| `d9cbd68`, `4e67b44` | DEMO Windows aislada, Waitress localhost, accesos/BAT, usuarios aleatorios privados, TEST sin remisión, guías y pruebas |
| `12120e6`, `e2a2b30`, `5303f99` | Consolidación funcional: ajustes categorizados, orden/visibilidad, cajas, incidencias, revocación de sesiones y matrices |
| `5dc936a`, `7045b03` | Auditoría integral contra `4ce821e`, correcciones de seguridad/integridad/fiscal/operaciones y evidencias |
| `4ce821e` | Referencia de la implementación inicial por fases del playbook |

Las cifras de112/697/836/893 pruebas de informes anteriores pertenecen a sus ejecuciones históricas. El resultado de esta fase se encuentra en la auditoría documental y sus JUnit; no se transforma una cifra histórica en un resultado actual.

Producción fiscal y hardware físico conservan los gates externos documentados. Portal Cliente, agenda y reservas no se anuncian como funciones implementadas de V1.
