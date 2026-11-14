# Consolidación funcional V1 — inventario y prioridades

Referencia de entrada: `5dc936a`, correcciones de auditoría `7045b03`, especificación en [REQUEST.md](REQUEST.md). No reconstruir ni borrar historial. Las 697 pruebas anteriores son una referencia de regresión, no prueba de estas nuevas capacidades.

## Fase A/B: hallazgos iniciales verificables

| Prioridad | Carencia de entrada | Actuación | Propietario |
|---|---|---|---|
| ALTO | Empresa solo tiene identidad fiscal y formulario único; faltan comercial/contacto/logo/preferencias | Ajustes categorizados, imagen raster segura, moneda EUR, validación de identidad tras emitir | backend/core |
| ALTO | CashRegister solo tiene nombre, sin configuración accesible | Alta/edición/actividad/terminal, proteger sesiones abiertas e historial | backend/cash |
| ALTO | Sin incidencias persistentes ni actuaciones/resolución | Modelo y transiciones autorizadas, pantalla operativa y técnica, auditoría | devops/support |
| ALTO | Sin revocación explícita de sesiones | Servicio auth_version y concesiones, POST elevado accesible | security/accounts, devops/support |
| MEDIO | Categorías solo nombre; catálogo/puestos sin orden configurable | Visibilidad/orden y consumidores TPV reales | backend/catalog/layout/pos |
| MEDIO | Comportamientos de corte/cajón sin preferencias | Flags validados e intención persistente, sin alterar trabajos anteriores | hardware |
| MEDIO | Listados administrativos básicos sin filtros suficientes | Navegación, búsqueda, filtros y estados vacíos | backend/devops + frontend |
| MEDIO | Cobertura documental no distingue todas las operaciones CRUD/configuración | Siete matrices con implementación, ruta, prueba y límite | coordinador + QA |
| CRÍTICO preventivo | Cambiar datos de empresa no debe alterar documentos/huellas emitidos ni quitar guard fiscal | Regresión fiscal, bloqueo cambio de obligado/instalación tras emitir | fiscal + backend |

## Gates de ejecución

A/B: contratos antes de escrituras paralelas; propiedad exclusiva por módulos. C: migraciones compatibles y pruebas positivas/negativas junto a cada operación. D: integración, servicios, formularios, cuatro roles, fiscal local, procesos SQLite y hardware simulado. E: Chromium escritorio/tablet/estrecho con revisión visual. F: matrices de cierre, instalación/upgrade/restore y commits verificables.

Los gates AEAT, firma del productor, dispositivos físicos y despliegue/personas de destino son BLOQUEADO EXTERNO. No activar producción con evidencias sintéticas.
