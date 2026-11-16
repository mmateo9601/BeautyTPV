# Estado de implementación — 13-11-2026

> Corte vigente: Fase 11, 16-11-2026, **900 pruebas aprobadas**. Véase el apartado final y [auditoría documental](DOCUMENTATION_AUDIT.md). Las cifras y estados de apartados anteriores son históricos.

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


## Consolidación funcional V1 — cierre 14-11-2026

Estado vigente: [FINAL_ACCEPTANCE.md](FINAL_ACCEPTANCE.md). **836 PASS, 0 fallos/errores/omitidas, 288,21s; 14 Chromium**. JUnit: `evidence/consolidation-final-tests.xml`. Reemplaza las cifras históricas de112/697 como resultado actual, conservadas abajo para trazabilidad.

Implementación `e2a2b30`; contratos fasesA/B `5303f99`. Ajustes categorizados Salón/Fiscal/TPV y logo PNG seguro; datos impresos congelados; identidad fiscal protegida tras emitir; orden/visibilidad; CRUD cajas/terminal; incidencias con actuaciones protegidas; revocación de sesiones; verificación independiente de backup; diagnósticos y filtros reales. Clientes tienen servicio protegido también sin HTTP. Siete migraciones aditivas aplicadas sin drift. No se reconstruye ni borra historia.

Django check0, migrate sin pendientes, makemigrations sin cambios; Ruff limpio/283formateados; pip check limpio. Instalación nueva, upgrade desde4ce821e, backup/restoreCLI y actualización real de paquete en copias temporales PASS, con historia/huellas preservadas. Python/venv ya preparado; no se afirma máquina virgen. Dos avisos de pytest documentados, sin fallos. La primera integración detectó ambigüedad de filtro caja; corregida, E01 y suite repetidos sin quitar aserciones.

Matriz funcional, permisos de84rutas/servicios, CRUD, ajustes, Superadmin y revisión visual en los siete entregables exigidos. Inventario actual84rutas,35modelos,324funciones,38plantillas,23comandos. QA independiente reprodujo y verificó corrección de categoría oculta agregable y terminal obsoleta de caja. Capturas escritorio/tablet/estrecho inspeccionadas por frontend y coordinador; PDF revisado visualmente.

**BLOQUEADO EXTERNO:** certificado/autorización/acuses oficiales AEAT; revisión experta y declaración responsable firmada; dispositivos físicos/papel80mm/QR/cajón; TLS/LAN/autoarranque/custodia y conciliación real en destino; aceptación con personas del salón. CI remota no ejecutada. El guard productivo permanece activo. Fiscalidad: IVA S1/01,F1/F2,rectificación totalR1/R5; sin ampliación silenciosa. Logo de interfaz, sin promesa de raster ESC/POS. Versiones por paquete local verificado, sin feed remoto.


## DEMO Windows aislada — 15-11-2026

Preparada instancia independiente en C:/Users/mmate/AppData/Local/BeautyTPV-DEMO, SQLite demo.sqlite3, configuración/credenciales aleatorias con ACL usuario+SYSTEM. Principal db.sqlite3 sin cambios por hashSHA256. Accesos reales en C:/Users/mmate/Desktop: BeautyTPV DEMO, Detener BeautyTPV DEMO, Usuarios, Cambiar usuarios y Reinicializar. Guía vigente: GUIA_WINDOWS_DEMO.md.

Scripts raíz BAT/PS y scripts/windows_demo.py proporcionan preparación, dependencias, migraciones, identidad privada, doble inicio, procesoWindows/fecha de creación/intérprete hijo de venv, evento cooperativo de parada y archivo seguro de DEMO al reset. Waitress127.0.0.1:8000 con DEBUGFalse, sin firewall ni LAN. Nuevo config.demo_settings mantiene TEST fijo, envío fiscal retenido sin bloquear ventas, sin certificados/trabajadorfiscal y sin conexiones no-loopback. Simulador permitido exclusivamente con perfilDEMO explícito o desarrollo; producción no relajada. Solo se tocaron dos guards funcionales porque impedían usar simulador con DEBUGFalse: hardware.drivers y support.PrinterForm.

Ocho especialistas utilizados: arquitecto/seguridad/fiscal/hardware aportaron contratos/revisiones; algunos turnos agotaron cuota y el coordinador integró. Backend semilla, devops servidor, frontend checklist y QA independiente entregaron código/pruebas por propiedad. QA reprodujo hardlink antes de migrate: guard previo corregido. Arranque real detectó PID del redirectorvenv distinto del intérprete; se valida descendencia+nonce. PruebaBAT detectó que Start-Process -Wait espera todo el árbol; se espera solo al lanzador para devolver el control. Revisión visual detectó heartbeat espaciado que parecía STALE: corregido y probado sin simular salud.

Regresión completa893PASS374,87s,14Chromium,2avisos conocidos; después del ajuste final únicamente de heartbeat, suite DEMO58PASS75,03s. Ruff302limpio, check0, drift0. Evidencias: windows-demo-final-tests.xml, windows-demo-guard-tests.xml, windows-demo-smoke.json, windows-demo-browser.json y windows-demo-reset.json. Inicio/parada/dobleinicio/puertoajeno/Pythonajeno/reinicio, BAT/lnk reales, HTTP200/estáticos y cuentaA2 persistente pasan. Reset y rotación explícitos pasan solo en instancia temporal. Navegación realcuatroroles y scopes, cobro12,10/cambio7,90/facturaTEST/spoolDONEsimulado; transmisionesfiscales0. Capturas revisadas: acceso/plano/cobro/factura/soporte; herramienta nativa no inicializó kernel, no se atribuye inspección manual humana.

Equipo real: Windows11Pro10.0.26300/Python3.14.7. Windows10 sin máquina adicional probada. Fiscal productivo, certificado/acuse oficial, impresora/cajón físicos y despliegue LAN siguen BLOQUEADOS EXTERNAMENTE. La DEMO queda en ejecución para el usuario, sin credenciales en repositorio/informe.

Implementación DEMO registrada en commit `4e67b44`; documentación y evidencias en el commit de cierre posterior.

## Fase 11: documentación profesional y licencias — 16-11-2026

Coordinación de los ocho especialistas con contratos previos en [phase11/CONTRACTS.md](phase11/CONTRACTS.md). El índice vigente es [README.md](README.md), con tres manuales, cinco documentos de arquitectura, cinco de desarrollo, tres de integraciones y seis de instalación/operaciones. Los documentos históricos se conservan y remiten a las guías canónicas.

Capturas: 38 PNG reales de Chromium/Waitress en DEMO temporal independiente (33 escritorio1440x900, dos tablet820x1180 y tres móvil390x844); procedencia y hashes en [manifest](screenshots/manifest.json). Sin uso de credenciales ni base de la DEMO habitual, sin remisiones AEAT. Renderización local de 102 documentos, 13 diagramas Mermaid y 35 referencias a imágenes: cero errores; no se atribuye render remoto de GitHub.

Inventario de terceros: 34 paquetes coincidentes con el lock y dos componentes web; textos originales y hashes preservados. Diez paquetes requieren revisión especial, además de intérprete/build/navegadores/recursos oficiales cuando se distribuyan. Licencia principal, titular, condiciones comerciales y canal de soporte pendientes; no se crea LICENSE ni se publican etiquetas/releases. Documentos y tooling opcional no añaden dependencias del producto.

Gates de integración ejecutados: Django check sin incidencias; makemigrations sin deriva; pip check sin requisitos rotos; Ruff limpio y 341 archivos formateados. Regresión completa: **900 PASS, cero fallos/errores/omitidas, 369,16s, 14 Chromium**; [JUnit actual](evidence/phase11-tests.xml). Dos avisos conocidos: override DATABASES en fixture de restore y fixture Playwright como método de instancia. Tras el ajuste final del parser documental: seis pruebas dirigidas PASS en0,28s. El resultado de enlaces/rutas/hashes/comandos está en [auditoría documental](DOCUMENTATION_AUDIT.md).

Sin cambios en apps/, config/, templates/, static/, pyproject.toml ni requirements.lock.txt respecto de3ee0168. La base principal conserva SHA256 caae59a09ef5f6b8047ede4638ec4564dcac0bd6889c01103306713df6c8e36d, igual al corte anterior. Manuales/capturas/runbooks registrados en commit a3873c4; el cierre legal/tooling/evidencias se registra en el commit que incorpora este informe. Solo documentación, capturas, herramientas documentales, pruebas del auditor y configuración de higiene del repositorio. No se alteran datos fiscales ni bloqueos productivos.

Bloqueos externos: certificado/autorización/acuse oficial AEAT, revisión fiscal y declaración responsable suscrita, impresora/cajón/papel/QR físicos, equipo destino/TLS/LAN/aceptación con personas, CI remota y comprobación del render remoto GitHub. La documentación los distingue de la validación software local. La decisión de licencia del propietario y revisión jurídica de redistribución siguen pendientes.
