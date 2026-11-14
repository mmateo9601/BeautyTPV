# Aceptación final de la consolidación funcional V1

Fecha: 14-11-2026. Referencias: `4ce821e` (implementación original), `7045b03` (auditoría), `5dc936a` (entrada a esta consolidación). Contratos/prioridades en `CONSOLIDATION_CONTRACTS.md` y `consolidation/PLAN.md`. Participaron los ocho especialistas con propiedad exclusiva; QA verificó las aportaciones de forma independiente.

## Dictamen

**836 pruebas aprobadas, 0 fallos, 0 errores, 0 omitidas; 288,21 s.** Incluye 14 recorridos Chromium. Consolidación local implementada y verificada dentro del escenario V1 documentado; **producción fiscal BLOQUEADA EXTERNAMENTE**.

El escenario local soportado conserva una instalación por empresa, SQLite local, plano inicial, cuatro roles jerárquicos y cliente sin acceso propio. La producción fiscal no está aprobada. El alcance fiscal sigue IVA general S1/01, F1/F2 y rectificación total R1/R5: no se añaden regímenes ni devoluciones parciales.

## Entregables y comprobación por requisitos

| Requisito | Estado | Implementación y ruta/servicio | Prueba / evidencia | Observación |
|---|---|---|---|---|
| Funciones V1 y flujos persistentes | COMPLETO LOCAL | [FUNCTIONAL_COVERAGE](FUNCTIONAL_COVERAGE.md), apps y templates | JUnit definitivo + suites de servicio/HTTP/Chromium | Se distinguen pruebas negativas de operaciones positivas |
| CRUD y transiciones legales | COMPLETO LOCAL | [CRUD_COVERAGE](CRUD_COVERAGE.md) | Formularios, services y DB; guards SQL | No CRUD histórico fiscal/ventas/caja/auditoría |
| Ajustes organizados/completos | COMPLETO LOCAL | [SETTINGS_COVERAGE](SETTINGS_COVERAGE.md), core:settings | Tests backend/QA/UI | Logo UI seguro, snapshot de datos impresos |
| Herencia cuatro roles y controles especiales | COMPLETO LOCAL | [ROLE_PERMISSION_MATRIX](ROLE_PERMISSION_MATRIX.md), 84 rutas | Matriz cuatro roles, CSRF, elevación/PII y servicios sin request | Cliente no es usuario V1 |
| Operaciones Superadmin reales | COMPLETO LOCAL | [SUPERADMIN_COVERAGE](SUPERADMIN_COVERAGE.md), support:* | Formularios reales/DB, scope y logs auditados | Restore/update offline asistidos; no consola arbitraria |
| Navegación y pantallas | COMPLETO LOCAL | [UI_REVIEW](UI_REVIEW.md), templates/static | Chromium y capturas revisadas | Escritorio1280, tablet820, estrecho390 |
| Integridad fiscal/contable/concurrencia | COMPLETO LOCAL | billing/verifactu/pos/cash | Tests fiscales/XSD/SQL/rollback/doble cobro/procesos | No se modificaron facturas históricas |
| Migraciones sobre historia existente | COMPLETO LOCAL | manage.py migrate | [Upgrade](evidence/consolidation-upgrade-recovery.json) | Factura/huella/cuenta abierta originales preservadas |
| Instalación, backup y restore | COMPLETO LOCAL | install.py/backup.py/restore.py, support:restore_advisor | Mismo JSON, pruebas CLI reales | Entorno Python preparado; nueva instancia sin usuarios por defecto |
| Actualización y rollback código | COMPLETO LOCAL | support.updates.apply_update, scripts/update.py | [Paquete real](evidence/consolidation-update.json), test_audit_ops.py | Backup cifrado previo; rollback IO con DB preservada probado en suite |
| AEAT con certificado y acuses oficiales | BLOQUEADO EXTERNO | SOAP mTLS/outbox implementados; production_guard activo | No ejecución oficial | Ver procedimiento de desbloqueo abajo |
| Papel80mm, QR y cajón físicos | BLOQUEADO EXTERNO | Drivers/bridge/spool implementados | Simulador/TCP/API únicamente | Sin marca/modelo/firmware disponible |
| Despliegue destino/aceptación humana | BLOQUEADO EXTERNO | Runbooks y servicio preparados | Loopback/copia temporal no validan salón real | TLS/LAN/autoarranque/operadores pendientes |

## Problemas detectados y correcciones

Carencias de entrada: ajustes comerciales y preferencias, orden/visibilidad, cajas configurables, incidencias, revocación explícita y verificación independiente de backup. Se implementaron rutas, formularios, servicios con permisos, migraciones aditivas y navegación. Se añadieron mensajes útiles y filtros administrativos.

QA independiente reprodujo categoría oculta aún agregable y terminal desactivada aceptada desde objeto obsoleto: corregidos con recarga/validación en DB y pruebas negativas/positivas. Se corrigieron también errores de integración de template y codificación antes del gate final. El primer intento de pruebas durante escritura de modelos carecía aún de migraciones; se repitió tras integrarlas, sin eliminar aserciones.

El formulario histórico de configuración se adapta al nuevo guard: su prueba de éxito conserva installation_number ya emitido y las nuevas pruebas negativas verifican que cambiarlo se rechaza. No se desactiva el guard para conservar una expectativa incompatible con el contrato aprobado.

## Comandos y resultados

| Comprobacion | Resultado |
|---|---|
| pytest -q --junitxml=docs/evidence/consolidation-final-tests.xml -o junit_family=xunit1 | 836 PASS; 14 Chromium; 288,21s |
| manage.py check | 0 incidencias |
| manage.py makemigrations --check --dry-run | Sin cambios |
| manage.py migrate --noinput | Aplicadas7migraciones nuevas; sin pendientes |
| ruff check . | Limpio |
| ruff format --check . | 283 archivos correctos |
| pip check | Sin dependencias incompatibles |
| Upgrade4ce821e, instalador nuevo y CLI backup/restore | PASS; hashes/historia/cuenta preservados; hold presente; usuarios predeterminados0 |
| Paquete completo update en copia temporal | PASS; preflight/backup/migrate/check/collectstatic y huellas preservadas |
| git diff/show --check de fuentes (CRLF reconocido; XML crudo excluido) | Sin errores |

Dos avisos: override DATABASES en prueba aislada de restore y deprecacion de fixture del plugin pytest para pytest10. Sin fallos ni omitidas. Primera integracion:835PASS+1FAIL por texto ambiguo del filtro caja; opciones corregidas sin cambiar aserciones, E01 repetido1PASS y suite completa836PASS. Evidencia anterior conservada como consolidation-integration-before-fix.xml. Poppler emitio avisos de fuentes Symbol/ArialUnicode al revisar el PDF; EXIT0 y salida visual legible sin recortes. No se afirma lectura QR fisica.

Evidencias: [JUnit final](evidence/consolidation-final-tests.xml), [QA independiente](evidence/consolidation-qa-tests.xml), [inventario completo](consolidation/inventory/INVENTARIO.md), informes especialistas en `consolidation/`. El recuento de casos incluye parametrizaciones; cada matriz enlaza implementación, ruta y prueba, no considera completo un botón por existir.

## Bloqueos externos y forma precisa de resolverlos

1. **AEAT:** aportar certificado y clave externos autorizados del obligado, validar su correspondencia/caducidad; ejecutar entorno oficial de pruebas con remisión/acuse, red caída, rechazo/subsanación, duplicados y conciliación; conservar evidencias sin secretos. Revisión experta del régimen y declaración responsable del productor suscrita/publicada. No basta reconsultar XSD/WSDL públicos. Solo después podrá tramitarse la aprobación productiva; este trabajo no retira el guard.
2. **Hardware:** facilitar impresora y cajón compatibles, registrar marca/modelo/firmware/conexión/codepage. Verificar legibilidad80mm/acentos/euro, lectura QR independiente, corte, un pulso en efectivo, ninguno en tarjeta/copia, caída/reinicio y UNKNOWN sin duplicado. Adjuntar evidencia según HARDWARE.md. DONE de spool solo indica transporte, no papel.
3. **Equipo/LAN:** instalar servicio y agentes con cuentas OS limitadas, TLS/CA de confianza, firewall/ACL, custodia de claves/copias y autoarranque. Probar terminales reales y recuperación/conciliación fiscal con acuses. SQLite permanece en disco del servidor, nunca SMB/NFS.
4. **Personas/CI:** propietario, Encargado, Empleado y Superadmin deben ejecutar aceptación en el centro; CI remota no ejecutada en esta sesión. Registrar operadores/fecha/evidencias antes de aprobar el despliegue.

## Commits

- `5303f99`: contratos, inventario y prioridades de fases A/B.
- `e2a2b30`: implementacion de módulos, siete migraciones, formularios, UI y pruebas; commit de cierre posterior registra matrices/evidencias.

No se declara validación oficial ni física por simulación. Las limitaciones de logo (UI), versiones (paquete local verificado) y fiscalidad (escenario explícito) están visibles en matrices y manuales.

Nota de evidencia: el XML de la primera integración conserva el traceback original de pytest, incluido un espacio al final de una línea `E`. Se conserva sin alterar la salida. La revisión de whitespace de fuentes excluye los XML generados; no es un defecto de código ni un fallo adicional de pruebas.
