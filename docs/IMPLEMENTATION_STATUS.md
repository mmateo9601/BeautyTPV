# Estado de implementación — 13-11-2026

Coordinador principal integra ocho especialistas de `.codex/agents/`: architect, backend, frontend, fiscal, hardware, security, qa, devops. Propietarios y contratos en CONTRACTS.md. Trabajo local; no SaaS ni tenants.

## Fase 0 — VERIFICADA LOCALMENTE
Inventario: únicamente especificación, agentes y prompt inicial. Cambio previo en PROMPT_INICIAL_CODEX.md preservado. Python 3.14.7; Django 5.2.19; entorno .venv. SQLite desde la primera migración y User personalizado.
Archivos: config/, manage.py, pyproject.toml, CI, docs/CONTRACTS.md, 3 ADR.
Comandos: manage.py check (0 incidencias), migrate (correcto), makemigrations --check --dry-run (sin cambios), pytest tests/test_bootstrap.py (1 passed), Ruff base limpio. Commit 1600918. CI configurada; no se atribuye ejecución remota.

## Fase 1 — integración verificada
Archivos: apps/accounts/, audit/, core/, support/, templates de acceso y soporte, configuración.
Seguridad: PIN hash, throttle persistente, roles, password elevada 10 minutos, autorización soporte temporal, scope PII aprobado por otro administrador, auditoría protegida con triggers. Se eliminó /admin/ para no abrir un acceso sin throttle. Sin usuarios/credenciales semilla.
Evidencia especialista: 37 tests security PASS, Ruff propio limpio. Smoke coordinador de pantallas detectó reverse de cola fiscal sin argumento y se corrigió. Support/backup 12 tests PASS informados por devops; repetición integrada final pendiente.

## Fase 2 — integración verificada
Archivos: layout/catalog/customers/pos, templates/static Bootstrap 5.3.8 y HTMX 2.0.8 locales con licencias. Plano A1/A2/A3/B1, cuentas persistentes, snapshots, versionado optimista, CRUD. Todos los templates compilan.
Evidencia: tests backend persistencia A1/A2 y snapshots PASS; E02 procesos/navegador PASS informado por qa. Suite E2E final pendiente.

## Fase 3 — integración verificada
Archivos: cash/pos/reports y migraciones, tests/test_backend.py. Pagos efectivo/tarjeta confirmada/mixto, caja/arqueo, idempotencia, informes netos tras devoluciones.
Evidencia coordinador: 7 tests backend PASS; pruebas QA dos procesos misma cuenta y tres terminales PASS. Se reforzó cierre de caja, copia de factura por propietario, CSV y triggers de agregados. No se guardan tarjetas.

## Fase 4 — integración verificada
Archivos: billing/, PDFs/QR, migraciones inmutables, tests fiscales. Emisión y rectificativa total con devolución conciliada. Se bloquean UPDATE/DELETE y nuevas líneas/pagos posteriores a emisión/cierre.
Evidencia: PDF probado por contenido; revisión visual coordinador pendiente. Regresiones nuevas tests/test_regressions.py: 4 PASS (caja obsoleta, inserción posterior, restore hold, movimiento/copia).

## Fase 5 — código local verificado; gate externo BLOQUEADO
Archivos: verifactu/, schemas/aeat oficiales con manifest SHA-256, docs/VERIFACTU_COMPLIANCE.md.
Huella: tres vectores oficiales AEAT; XSD de alta/rectificación/anulación/respuesta; SOAP mTLS real y outbox, rechazo/subsanación, estado duplicado para revisión; producción fail-closed. Evidencia: 11 tests fiscales PASS. Certificado y remisión oficial no disponibles; revisión experta y declaración responsable pendientes. No se afirma aceptación AEAT.

## Fase 6 — simulador verificado; gate físico BLOQUEADO
Archivos: hardware/, bridge, worker, ESC/POS TCP/USB/serie, spool y estado UNKNOWN ante entrega incierta. Copias sin cajón; fallo de impresión no repite venta.
Evidencia especialista: 14 tests hardware PASS. No hay impresora/cajón, modelo ni firmware: E14 físico pendiente.

## Fase 7 — integración en verificación final
Archivos: support/, scripts/, manuales instalación/backup/update. Backup API SQLite cifrado autenticado, restore offline con copia previa/hold; locks compartidos servidor/workers y exclusivos mantenimiento; actualización SHA-256 y rollback de código sin retroceder BD.
Evidencia devops: 12 tests PASS; instancia limpia con dependencias preinstaladas PASS. Coordinador ejecutando instalador completo en instancia temporal nueva, sin usuario, y arranque con workers. Restauración bloquea servicios de cobro, fiscal e impresión hasta conciliación.

## Fase 8 — en curso
QA convierte E01–E16 en tests servicio/procesos/navegador y matriz docs/ACCEPTANCE_MATRIX.md. Chromium instalado y lanzamiento verificado con permisos de proceso. CI instala Chromium antes de pytest. Coordinador ejecutará check, drift, migrate, pytest completo, Ruff, instalación/restore y revisión visual. Resultado final y limitaciones en RELEASE_REPORT.md.

## Reglas de evidencia
Las pruebas SOAP simuladas no son envíos oficiales. Los bytes ESC/POS y el simulador no son pruebas físicas. No se declara producto productivo conforme hasta superar gates externos. No se ejecutó migración a PostgreSQL.

## Cierre de verificación local

Suite integrada final: `pytest -q --junitxml=docs/evidence/final-tests.xml -o junit_family=xunit1` -> **112 passed, 2 warnings, 73.33 s**. Incluye tres E2E Chromium. Warnings identificados en RELEASE_REPORT.md; no errores. `check`0, drift0, `ruff check` limpio, `ruff format --check`192 archivos correctos. Capturas plano/tablet/PDF inspeccionadas por QA y coordinador.

Instalador completo `--no-user` sobre instancia temporal nueva EXIT0; arranque real con workers y HTTP/estáticos200; restore bloqueado con servicio activo, integrity_check tras parada OK y usuarios0. Scripts CLI backup/update paquete completo/restore EXIT0 sobre copia temporal; hold presente tras restore. Se incluye generador de ZIP con manifest/hash y excluye secretos/BD. Instalador fija dependencias mediante requirements.lock.txt.

Fases locales F1–F4 y F7 verificadas con los límites del informe. F5/F6 tienen implementación y tests locales, pero gates oficiales/físicos BLOQUEADOS. F8: E01–E16 auditados en matriz, tests software correctos; aceptación real/TLS/AEAT/hardware pendientes. Release productiva NO APROBADA. Reporte final completo disponible.


## Registro de commits por fase

| Fase | Commit |
|---|---|
| 0 contratos/base | 1600918 |
| 1 seguridad/soporte base | a6277bc |
| 2 plano/catalogo/clientes | 8eb0aa9 |
| 3 cobros/caja/informes | de69358 |
| 4 facturacion local | 4e253f2 |
| 5 protocolo fiscal (gate externo cerrado) | de6484c |
| 6 bridge hardware (gate fisico cerrado) | fc5ffbb |
| 7 instalacion/backup/update | fba8f9a |

Fase8 integra QA/E2E, correcciones finales CRUD y evidencias. En revision final
se conectaron categorias y exportacion/borrado controlados de clientes; pruebas
negativas verifican permisos, CSV seguro y retencion del historial. Los bytes
oficiales AEAT se conservan con .gitattributes y se contrastan contra su manifest.
Instalador final fijado a requirements.lock.txt ejecutado en segunda instancia
nueva: EXIT0, migraciones/check/estaticos correctos, sin usuarios predeterminados.


Resultado definitivo tras controles CRUD: **112 passed, 2 warnings, 73.33s**;
JUnit final contiene 112 casos, 0 errores, 0 fallos y 0 omitidos. Esquemas oficiales
contrastados byte a byte con manifest (12 tests fiscales en total); los archivos
se preservan sin conversion de finales de linea en Git. Ruff limpio192 archivos;
check0, migraciones sin drift. Ningun gate externo se presenta como superado.


## Auditoría integral posterior a 4ce821e — 14-11-2026

Esta sección sustituye las cifras históricas de cierre de 112 pruebas como estado actual. Informe rector: [AUDITORIA_COMPLETA.md](../AUDITORIA_COMPLETA.md); inventario y hallazgos en `audit/`.

**697 PASS, 0 fallos, 0 errores, 0 omitidas, 202,53 s**, incluidos diez Chromium y pruebas de procesos independientes. Evidencia: [audit-final-tests.xml](evidence/audit-final-tests.xml). Dos avisos: override DATABASES en prueba aislada; deprecación de fixture del plugin pytest para pytest10. Django check sin incidencias; migrate sin pendientes; makemigrations sin drift; Ruff check limpio y format241; pip check limpio. Referencia aislada4ce821e:112PASS.

Correcciones en accounts/audit, core/layout/pos/cash/reports, billing/verifactu, hardware, support/scripts, config y templates/static. Nuevas migraciones y regresiones cubren revocación de sesiones/PII/elevación, estados/notas/venta rápida/terminales, informes y cancelaciones, integridad SQL, control fiscal de espera/leases/correcciones, bridge remoto y entrega incierta, preflight/rollback, supervisión de workers y restauración asistida.

Upgrade real desde la referencia conserva factura/huella/cuenta abierta; backup cifrado y restore CLI pasan con retención presente. Instalación en instancia nueva pasa sin usuarios predeterminados, usando entorno Python ya preparado. Benchmark1/3/6procesos:100ventas,0errores,p95 0,1792/0,7839/1,8796s. OSV consulta36versiones:0avisos conocidos en esa respuesta, sin garantía de ausencia de vulnerabilidades. Evidencias JSON en `evidence/audit-*.json`.

**Gates externos BLOQUEADOS:** certificado/autorización y acuses oficiales AEAT; revisión normativa y declaración responsable suscrita; impresora/cajón/QR físicos; equipo destino/TLS/LAN/autoarranque y conciliación con acuses reales; aceptación con personas del negocio. CI remota no ejecutada. No aprobar producción ni retirar el guard fiscal. Alcance fiscal local: IVA general S1/01, F1/F2 y rectificativa total R1/R5; sin devoluciones parciales ni regímenes especiales.

Commit de integración de la auditoría: `7045b03` (código, migraciones y pruebas). La documentación y evidencias se registran en el commit de cierre posterior.

## Consolidación funcional V1 — Fases A/B (14-11-2026)

Base `5dc936a`/`7045b03`, 697 casos históricos. Se leyó la nueva petición, AGENTS, PLAYBOOK, auditoría y ocho configuraciones. Arquitecto fijó contratos antes del paralelo; agentes con propiedad exclusiva: backend core/catalog/layout/cash/pos, frontend templates/static, security accounts, fiscal revisión/regresiones, hardware hardware, devops support, QA aceptación/matriz independiente. Coordinador configura/integración/docs/scripts y asume módulos entregados.

Inventario constató faltas de ajustes comerciales/logo/preferencias, orden y visibilidad, cajas configurables, incidencias y revocación explícita. Priorización y contrato: `consolidation/PLAN.md`, `CONSOLIDATION_CONTRACTS.md`. No se reconstruye ni elimina historial; apertura de caja Employee previa preservada, cierre/movimientos Manager. Matrices de cierre se completan al integrar.

Comprobación intermedia: Django check0, drift0, Ruff limpio276archivos. Especialistas verificaron revocación83PASS y hardware44PASS antes de integrar los nuevos campos. Las primeras pruebas durante escritura de modelos detectaron columnas aún sin migraciones; se repitieron tras generar las migraciones. QA independiente detectó ocultación de categoría insuficiente y terminal obsoleta en caja, asignadas para corrección; no se reducen aserciones. Aún no es gate final.
