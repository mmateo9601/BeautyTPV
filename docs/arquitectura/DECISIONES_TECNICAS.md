# Decisiones técnicas y registros ADR

Fecha de contraste: 15-11-2026. Estos registros describen decisiones observables en el código `0.1.0`; no crean una nueva arquitectura, un release estable ni una aprobación fiscal. El [contrato de Fase 11](../phase11/CONTRACTS.md) limita esta fase a documentación y verificación.

## Registros iniciales conservados

| ADR | Decisión | Lectura actual |
|---|---|---|
| [001 — Instalación y módulos](../ADRs/001-installation-and-modules.md) | Instalación independiente, Django/Bootstrap/HTMX/SQLite y límites modulares | Implementada; no hay tenants ni portal Cliente |
| [002 — SQLite e idempotencia](../ADRs/002-sqlite-and-idempotency.md) | Archivo local, transacciones cortas, constraints, CAS e idempotencia | IMMEDIATE/timeout configurados; WAL no se activa en el código actual |
| [003 — Fiscal y hardware](../ADRs/003-fiscal-and-hardware-gates.md) | Documentos inmutables, outbox/spool y gates externos | Implementación local existente; conformidad y pruebas físicas siguen bloqueadas externamente |

Los estados «pendiente» de los ADR iniciales pertenecen a su momento de redacción. Para conocer qué comprobaciones se ejecutaron después, consultar [IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md), [RELEASE_REPORT.md](../RELEASE_REPORT.md) y la auditoría documental actual. No se reescribe la historia de esas decisiones para atribuir aprobaciones retroactivas.

## ADR 004 — Unidad de cobro persistente e idempotente

**Estado:** implementado, contrastado en código. **Fuente:** [pos/services.py](../../apps/pos/services.py), [core/transactions.py](../../apps/core/transactions.py), [billing/services.py](../../apps/billing/services.py).

**Contexto.** Doble clic, dos terminales o una interrupción no deben crear más ventas, números fiscales ni originales de impresión para la misma formalización.

**Decisión.** `checkout` recibe actor, cuenta, pagos y clave idempotente. Normaliza y valida importes; guarda una huella de la petición. La clave repetida devuelve la venta existente solamente si coincide la huella. La cuenta utiliza versión/CAS y constraints. Venta, pagos, factura, número, alta/outbox e intención de impresión participan en la unidad atómica. `atomic_retry` reintenta la unidad completa después del rollback por busy/locked, hasta cuatro intentos y sin asumir bloqueos de fila SQLite.

**Consecuencias.** La red y los dispositivos no participan dentro de la transacción financiera. Un error de impresión no repite cobro. Reintentar con otros datos requiere corregir el conflicto, no reutilizar silenciosamente una clave. El datáfono se confirma externamente: no hay transacción bancaria integrada que pueda reintentarse automáticamente.

**Evidencia verificable.** `tests/test_concurrency.py` incluye procesos reales y muerte antes del commit; `tests/test_acceptance.py` comprueba venta/factura/alta únicas. La cifra actual de ejecuciones se informa en la auditoría de cierre, no se inventa en este ADR.

## ADR 005 — Historia emitida protegida y correcciones por nuevos registros

**Estado:** implementado en el escenario fiscal soportado. **Fuente:** [billing/models.py](../../apps/billing/models.py), [billing/services.py](../../apps/billing/services.py), migraciones de `billing`, `pos`, `cash`, `audit`, `verifactu` y `hardware`.

**Contexto.** Cambiar catálogo, empresa o credenciales no puede reescribir la historia económica ni fiscal.

**Decisión.** Facturas y líneas son snapshots emitidos; sus datos comerciales impresos también se congelan. Hay controles ORM y triggers SQLite contra modificaciones/borrados/reemplazos de registros históricos protegidos. La devolución soportada genera una rectificativa total y una operación compensatoria, nunca borra el original. Anular una cuenta no emitida, rectificar una venta y anular un registro fiscal son operaciones distintas.

**Consecuencias.** No se ofrece CRUD genérico de facturas, cobros confirmados o auditoría. El NIF y la identificación de instalación no se reasignan después de emitir mediante el servicio de ajustes. Una base copiada o un sistema operativo comprometido no se autentican solo con triggers locales: hacen falta custodia y evidencias externas.

**Evidencia verificable.** `tests/test_audit_fiscal.py`, `test_consolidation_documents.py`, `test_consolidation_backend.py` y pruebas de integridad SQL. El ámbito fiscal sigue siendo el documentado en [VERIFACTU.md](../integraciones/VERIFACTU.md), sin regímenes especiales ni devoluciones parciales anunciados.

## ADR 006 — Efectos externos persistentes con entrega incierta explícita

**Estado:** implementado localmente; validación externa pendiente. **Fuente:** [verifactu/services.py](../../apps/verifactu/services.py), [hardware/services.py](../../apps/hardware/services.py), [hardware/bridge.py](../../apps/hardware/bridge.py), [hardware/agent.py](../../apps/hardware/agent.py).

**Contexto.** Un timeout puede ocurrir después de que AEAT o una impresora hayan recibido datos. «Reintentar» no debe significar renumerar ni abrir de nuevo el cajón sin comprobar el resultado.

**Decisión.** Outbox y spool se persisten. Fiscal utiliza lease/CAS, fencing y espera por endpoint; conserva transmisiones/respuestas y estados. Hardware distingue fallo anterior al envío de `UNKNOWN` por entrega incierta; las copias son explícitas y no abren cajón. El agente remoto escribe un journal antes del I/O y recupera ACK sin repetir bytes automáticamente.

**Consecuencias.** `DONE` indica transporte completado, no comprobación de papel. Un duplicado fiscal en revisión no se convierte en aceptación inventada. La recuperación puede exigir al operador conciliar acuses/dispositivo antes de actuar.

**Evidencia verificable.** `tests/test_audit_fiscal.py`, `test_audit_hardware.py`, `test_consolidation_hardware.py`; gates de AEAT/papel/QR/cajón en [RELEASE_REPORT.md](../RELEASE_REPORT.md).

## ADR 007 — Jerarquía operativa con elevación y soporte por alcance

**Estado:** implementado. **Fuente:** [accounts/permissions.py](../../apps/accounts/permissions.py), [accounts/middleware.py](../../apps/accounts/middleware.py), [support/services.py](../../apps/support/services.py).

**Contexto.** Heredar tareas operativas no justifica acceso técnico ilimitado a clientes ni decisiones basadas en sesiones antiguas.

**Decisión.** Cuatro roles internos por rango; el servicio recarga rol/actividad/versión del actor. Las vistas administrativas requieren elevación. Soporte temporal tiene motivo, aprobador, vencimiento y scopes distintos. PII comercial exige elevación y aprobación independiente; el scope técnico no la sustituye. Cambios de credenciales/rol/actividad y revocación explícita invalidan sesiones/concesiones.

**Consecuencias.** Un Superadmin puede recibir403 en una ruta sensible aunque herede la capacidad operativa. No es un error de menú que deba resolverse ocultando permisos. Cliente es una ficha comercial, no un quinto rol interno con login. El acceso directo al ORM por código confiable/administrador OS no es un endpoint público.

**Evidencia verificable.** [ROLE_PERMISSION_MATRIX.md](../ROLE_PERMISSION_MATRIX.md), `tests/test_audit_matrix.py`, `test_audit_security.py`, `test_consolidation_security.py` y servicios sin HTTP probados.

## ADR 008 — DEMO Windows aislada y sin transporte fiscal

**Estado:** implementado para la demostración local. **Fuente:** [demo_settings.py](../../config/demo_settings.py), [windows_demo.py](../../scripts/windows_demo.py), [demo_server.py](../../scripts/demo_server.py), [demo_seed.py](../../scripts/demo_seed.py).

**Contexto.** Permitir revisar el producto sin una terminal permanente ni credenciales predeterminadas, sin afectar una empresa existente.

**Decisión.** DEMO tiene marcador/configuración/SQLite/estáticos y secretos externos propios, ACL del usuario y SYSTEM, cuatro usuarios aleatorios y seed sintético. Waitress escucha exclusivamente127.0.0.1:8000, con DEBUG falso. El perfil fija TEST, retiene remisión y bloquea red no-loopback. Solo permite simulador; no inicia el scheduler fiscal. La parada valida PID/creación, descendencia del intérprete Windows y nonce; señala un evento propio sin matar Python por nombre. Reset archiva solo la carpeta marcada y genera otra.

**Consecuencias.** No equivale al despliegue LAN ni a pruebas oficiales/físicas. La excepción HTTP/cookies sin Secure de loopback y la habilitación explícita del simulador no cambian el perfil productivo. No deben copiarse la base o las credenciales DEMO a una instalación real.

**Evidencia verificable.** [GUIA_WINDOWS_DEMO.md](../GUIA_WINDOWS_DEMO.md), `tests/test_windows_demo.py`, `test_demo_seed.py`, `test_demo_server.py`, `test_demo_profile.py` y evidencias Windows del cierre anterior. Esta fase vuelve a comprobar lo que atribuya a su propia ejecución.

## ADR 009 — Recuperación offline y evolución de almacenamiento

**Estado:** recuperación implementada; PostgreSQL futuro. **Fuente:** [support/operations.py](../../apps/support/operations.py), [support/updates.py](../../apps/support/updates.py), [POSTGRESQL_FUTURE.md](../POSTGRESQL_FUTURE.md).

**Contexto.** Restaurar una copia o actualizar código mientras existen escritores puede perder historia y reenviar efectos externos ya completados.

**Decisión.** Entry points oficiales adquieren lock de ciclo de vida. Restore/update offline requieren exclusivo. La copia se verifica y cifra; restore deja hold hasta conciliación fiscal y de impresión. Update valida paquete/dependencias, hace backup y migra; rollback revierte código, preserva la base vigente y deja retención si falla. El venv no se revierte automáticamente.

**Consecuencias.** La web asiste y verifica, no intercambia una SQLite viva. PostgreSQL no se activa en V1: los triggers y detalles de concurrencia requieren revisión específica, comparación de importes/secuencias/huellas y aceptación antes de migrar. No basta cambiar ENGINE.

**Evidencia verificable.** `tests/test_backup.py`, `test_audit_ops.py`, `test_concurrency.py` y evidencias de upgrade/restore/paquetes registradas en el informe de release.

## Decisiones que siguen fuera de esta documentación

- La licencia principal elegida el 16-11-2026 es AGPL-3.0-only, con PR recomendadas. El texto estándar no exige enviar mejoras al upstream; condiciones comerciales y titularidad consolidada no se inventan. Consulte [decisión de licencia](../legal/OPCIONES_LICENCIA.md).
- Certificados/autorización del obligado, declaración responsable suscrita, pruebas oficiales AEAT y comprobaciones físicas se resuelven con recursos y responsables externos.
- No se implementan agenda, reservas, bonos, portal Cliente ni SaaS. Las futuras extensiones no deben representarse en diagramas como servicios activos.

Cuando se modifique una decisión, crear un ADR con contexto, alternativas, decisión, consecuencias, código afectado y prueba de aceptación; enlazar el registro anterior y actualizar este índice. No cambiar su estado a «validado externamente» por la existencia de un archivo, mock o botón.
