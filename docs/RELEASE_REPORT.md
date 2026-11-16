# Informe de release — BeautyTPV 0.1.0

## Fase 11: documentación profesional y licencias — 16-11-2026

Coordinación de los ocho especialistas con contratos previos en [phase11/CONTRACTS.md](phase11/CONTRACTS.md). El índice vigente es [README.md](README.md), con tres manuales, cinco documentos de arquitectura, cinco de desarrollo, tres de integraciones y seis de instalación/operaciones. Los documentos históricos se conservan y remiten a las guías canónicas.

Capturas: 38 PNG reales de Chromium/Waitress en DEMO temporal independiente (33 escritorio1440x900, dos tablet820x1180 y tres móvil390x844); procedencia y hashes en [manifest](screenshots/manifest.json). Sin uso de credenciales ni base de la DEMO habitual, sin remisiones AEAT. Renderización local de 102 documentos, 13 diagramas Mermaid y 35 referencias a imágenes: cero errores; no se atribuye render remoto de GitHub.

Inventario de terceros: 34 paquetes coincidentes con el lock y dos componentes web; textos originales y hashes preservados. Diez paquetes requieren revisión especial, además de intérprete/build/navegadores/recursos oficiales cuando se distribuyan. Licencia principal, titular, condiciones comerciales y canal de soporte pendientes; no se crea LICENSE ni se publican etiquetas/releases. Documentos y tooling opcional no añaden dependencias del producto.

Gates de integración ejecutados: Django check sin incidencias; makemigrations sin deriva; pip check sin requisitos rotos; Ruff limpio y 341 archivos formateados. Regresión completa: **900 PASS, cero fallos/errores/omitidas, 369,16s, 14 Chromium**; [JUnit actual](evidence/phase11-tests.xml). Dos avisos conocidos: override DATABASES en fixture de restore y fixture Playwright como método de instancia. Tras el ajuste final del parser documental: seis pruebas dirigidas PASS en0,28s. El resultado de enlaces/rutas/hashes/comandos está en [auditoría documental](DOCUMENTATION_AUDIT.md).

Sin cambios en apps/, config/, templates/, static/, pyproject.toml ni requirements.lock.txt respecto de3ee0168. La base principal conserva SHA256 caae59a09ef5f6b8047ede4638ec4564dcac0bd6889c01103306713df6c8e36d, igual al corte anterior. Manuales/capturas/runbooks registrados en commit a3873c4; el cierre legal/tooling/evidencias se registra en el commit que incorpora este informe. Solo documentación, capturas, herramientas documentales, pruebas del auditor y configuración de higiene del repositorio. No se alteran datos fiscales ni bloqueos productivos.

Bloqueos externos: certificado/autorización/acuse oficial AEAT, revisión fiscal y declaración responsable suscrita, impresora/cajón/papel/QR físicos, equipo destino/TLS/LAN/aceptación con personas, CI remota y comprobación del render remoto GitHub. La documentación los distingue de la validación software local. La decisión de licencia del propietario y revisión jurídica de redistribución siguen pendientes.


## DEMO Windows aislada — 15-11-2026

Preparada instancia independiente en C:/Users/mmate/AppData/Local/BeautyTPV-DEMO, SQLite demo.sqlite3, configuración/credenciales aleatorias con ACL usuario+SYSTEM. Principal db.sqlite3 sin cambios por hashSHA256. Accesos reales en C:/Users/mmate/Desktop: BeautyTPV DEMO, Detener BeautyTPV DEMO, Usuarios, Cambiar usuarios y Reinicializar. Guía vigente: GUIA_WINDOWS_DEMO.md.

Scripts raíz BAT/PS y scripts/windows_demo.py proporcionan preparación, dependencias, migraciones, identidad privada, doble inicio, procesoWindows/fecha de creación/intérprete hijo de venv, evento cooperativo de parada y archivo seguro de DEMO al reset. Waitress127.0.0.1:8000 con DEBUGFalse, sin firewall ni LAN. Nuevo config.demo_settings mantiene TEST fijo, envío fiscal retenido sin bloquear ventas, sin certificados/trabajadorfiscal y sin conexiones no-loopback. Simulador permitido exclusivamente con perfilDEMO explícito o desarrollo; producción no relajada. Solo se tocaron dos guards funcionales porque impedían usar simulador con DEBUGFalse: hardware.drivers y support.PrinterForm.

Ocho especialistas utilizados: arquitecto/seguridad/fiscal/hardware aportaron contratos/revisiones; algunos turnos agotaron cuota y el coordinador integró. Backend semilla, devops servidor, frontend checklist y QA independiente entregaron código/pruebas por propiedad. QA reprodujo hardlink antes de migrate: guard previo corregido. Arranque real detectó PID del redirectorvenv distinto del intérprete; se valida descendencia+nonce. PruebaBAT detectó que Start-Process -Wait espera todo el árbol; se espera solo al lanzador para devolver el control. Revisión visual detectó heartbeat espaciado que parecía STALE: corregido y probado sin simular salud.

Regresión completa893PASS374,87s,14Chromium,2avisos conocidos; después del ajuste final únicamente de heartbeat, suite DEMO58PASS75,03s. Ruff302limpio, check0, drift0. Evidencias: windows-demo-final-tests.xml, windows-demo-guard-tests.xml, windows-demo-smoke.json, windows-demo-browser.json y windows-demo-reset.json. Inicio/parada/dobleinicio/puertoajeno/Pythonajeno/reinicio, BAT/lnk reales, HTTP200/estáticos y cuentaA2 persistente pasan. Reset y rotación explícitos pasan solo en instancia temporal. Navegación realcuatroroles y scopes, cobro12,10/cambio7,90/facturaTEST/spoolDONEsimulado; transmisionesfiscales0. Capturas revisadas: acceso/plano/cobro/factura/soporte; herramienta nativa no inicializó kernel, no se atribuye inspección manual humana.

Equipo real: Windows11Pro10.0.26300/Python3.14.7. Windows10 sin máquina adicional probada. Fiscal productivo, certificado/acuse oficial, impresora/cajón físicos y despliegue LAN siguen BLOQUEADOS EXTERNAMENTE. La DEMO queda en ejecución para el usuario, sin credenciales en repositorio/informe.


## Consolidación funcional V1 — cierre 14-11-2026

Estado vigente: [FINAL_ACCEPTANCE.md](FINAL_ACCEPTANCE.md). **836 PASS, 0 fallos/errores/omitidas, 288,21s; 14 Chromium**. JUnit: `evidence/consolidation-final-tests.xml`. Reemplaza las cifras históricas de112/697 como resultado actual, conservadas abajo para trazabilidad.

Implementación `e2a2b30`; contratos fasesA/B `5303f99`. Ajustes categorizados Salón/Fiscal/TPV y logo PNG seguro; datos impresos congelados; identidad fiscal protegida tras emitir; orden/visibilidad; CRUD cajas/terminal; incidencias con actuaciones protegidas; revocación de sesiones; verificación independiente de backup; diagnósticos y filtros reales. Clientes tienen servicio protegido también sin HTTP. Siete migraciones aditivas aplicadas sin drift. No se reconstruye ni borra historia.

Django check0, migrate sin pendientes, makemigrations sin cambios; Ruff limpio/283formateados; pip check limpio. Instalación nueva, upgrade desde4ce821e, backup/restoreCLI y actualización real de paquete en copias temporales PASS, con historia/huellas preservadas. Python/venv ya preparado; no se afirma máquina virgen. Dos avisos de pytest documentados, sin fallos. La primera integración detectó ambigüedad de filtro caja; corregida, E01 y suite repetidos sin quitar aserciones.

Matriz funcional, permisos de84rutas/servicios, CRUD, ajustes, Superadmin y revisión visual en los siete entregables exigidos. Inventario actual84rutas,35modelos,324funciones,38plantillas,23comandos. QA independiente reprodujo y verificó corrección de categoría oculta agregable y terminal obsoleta de caja. Capturas escritorio/tablet/estrecho inspeccionadas por frontend y coordinador; PDF revisado visualmente.

**BLOQUEADO EXTERNO:** certificado/autorización/acuses oficiales AEAT; revisión experta y declaración responsable firmada; dispositivos físicos/papel80mm/QR/cajón; TLS/LAN/autoarranque/custodia y conciliación real en destino; aceptación con personas del salón. CI remota no ejecutada. El guard productivo permanece activo. Fiscalidad: IVA S1/01,F1/F2,rectificación totalR1/R5; sin ampliación silenciosa. Logo de interfaz, sin promesa de raster ESC/POS. Versiones por paquete local verificado, sin feed remoto.

## Registro histórico previo a la consolidación

## Auditoría integral posterior a 4ce821e — 14-11-2026

Esta sección sustituye las cifras históricas de cierre de 112 pruebas como estado actual. Informe rector: [AUDITORIA_COMPLETA.md](../AUDITORIA_COMPLETA.md); inventario y hallazgos en `audit/`.

**697 PASS, 0 fallos, 0 errores, 0 omitidas, 202,53 s**, incluidos diez Chromium y pruebas de procesos independientes. Evidencia: [audit-final-tests.xml](evidence/audit-final-tests.xml). Dos avisos: override DATABASES en prueba aislada; deprecación de fixture del plugin pytest para pytest10. Django check sin incidencias; migrate sin pendientes; makemigrations sin drift; Ruff check limpio y format241; pip check limpio. Referencia aislada4ce821e:112PASS.

Correcciones en accounts/audit, core/layout/pos/cash/reports, billing/verifactu, hardware, support/scripts, config y templates/static. Nuevas migraciones y regresiones cubren revocación de sesiones/PII/elevación, estados/notas/venta rápida/terminales, informes y cancelaciones, integridad SQL, control fiscal de espera/leases/correcciones, bridge remoto y entrega incierta, preflight/rollback, supervisión de workers y restauración asistida.

Upgrade real desde la referencia conserva factura/huella/cuenta abierta; backup cifrado y restore CLI pasan con retención presente. Instalación en instancia nueva pasa sin usuarios predeterminados, usando entorno Python ya preparado. Benchmark1/3/6procesos:100ventas,0errores,p95 0,1792/0,7839/1,8796s. OSV consulta36versiones:0avisos conocidos en esa respuesta, sin garantía de ausencia de vulnerabilidades. Evidencias JSON en `evidence/audit-*.json`.

**Gates externos BLOQUEADOS:** certificado/autorización y acuses oficiales AEAT; revisión normativa y declaración responsable suscrita; impresora/cajón/QR físicos; equipo destino/TLS/LAN/autoarranque y conciliación con acuses reales; aceptación con personas del negocio. CI remota no ejecutada. No aprobar producción ni retirar el guard fiscal. Alcance fiscal local: IVA general S1/01, F1/F2 y rectificativa total R1/R5; sin devoluciones parciales ni regímenes especiales.

## Evidencias históricas de la implementación inicial


Fecha: 13-11-2026. Instalación local independiente por empresa. Django 5.2.19 + Bootstrap 5.3.8 + HTMX 2.0.8 + SQLite; Python 3.14.7 en Windows.

**Resultado: implementación local ejecutable y verificada; release fiscal productiva BLOQUEADA.** No se declara conformidad AEAT ni hardware físico verificado. El modo productivo está cerrado en código; los comprobantes TEST llevan aviso de falta de validez fiscal productiva.

## Comprobaciones del coordinador

| Comprobación | Resultado | Evidencia / alcance |
|---|---|---|
| Inventario, contratos y ocho especialistas | VERIFICADO | CONTRACTS.md, ADRs, agentes architect/backend/frontend/fiscal/hardware/security/qa/devops utilizados con propietarios exclusivos |
| Django check | VERIFICADO | `manage.py check`: 0 incidencias |
| Migraciones | VERIFICADO | `migrate --noinput` aplicado; `makemigrations --check --dry-run`: sin cambios |
| Suite completa | VERIFICADO: 112 PASS, 73,33 s | evidence/final-tests.xml. Dos avisos: override DATABASES en prueba aislada y deprecación de fixture del plugin pytest para versión10; sin fallos |
| Análisis estático | VERIFICADO | `ruff check .` limpio y `ruff format --check .`: 192 archivos formateados |
| Instalador en instancia nueva | VERIFICADO | `scripts/install.py --instance-dir <temporal nuevo> --no-user`: EXIT0, pip editable, SQLite nuevo, migraciones, bootstrap, check y collectstatic. Segunda instancia nueva con requirements.lock.txt también EXIT0. Entorno Python/venv ya preparado; no se afirma máquina virgen ni instalación de SO |
| Arranque y workers | VERIFICADO | `scripts/service.py --development`: HTTP200 acceso, Bootstrap232111 bytes y HTMX51250 bytes; servidor/workers activos impiden lock exclusivo de restore; parada controlada de procesos y integrity_check OK; usuarios semilla0 |
| Backup/restore real por CLI | VERIFICADO | `backup.py` y `restore.py --offline --confirm "RESTORE OFFLINE"`: EXIT0 en instancia sintética, copia cifrada y marcador de retención presentes; E12 adicional conserva facturas/cadena y bloquea duplicados |
| Paquete completo y actualización real | VERIFICADO LOCAL | ZIP con release.json y SHA256 validado; `update.py --offline` aplicado a copia temporal completa del código, migrate/check/collectstatic EXIT0. Rollback de código sin revertir BD probado además por tests; no se actualizó un negocio real |
| Interfaz y PDF | VERIFICADO VISUAL LOCAL | evidence/floor-desktop.png, ticket-tablet.png e invoice-test.png/PDF: revisados por QA y coordinador; sin solapamientos. PDF de una página con QR, snapshots y desglose |
| CI | NO VERIFICADO REMOTO | Workflow incluido con Chromium; no se afirma ejecución en GitHub |
| Seguridad despliegue | VERIFICADO CONFIGURACIÓN / PENDIENTE EQUIPO | Diagnóstico producción: sin errores, avisos W005/W021 por no activar HSTS para subdominios/preload. Decisión dependiente del dominio del negocio. TLS/proxy/firewall/arranque automático en destino no se han instalado ni validado |

## E01–E16

El detalle requisito→test→límite está en [ACCEPTANCE_MATRIX.md](ACCEPTANCE_MATRIX.md).

| Escenario | Estado de software | Validación externa |
|---|---|---|
| E01 efectivo, caja, factura, cola, liberar puesto | VERIFICADO servicio + navegador | Impresión/cajón físicos BLOQUEADOS |
| E02 A1/A2 independientes y persistentes | VERIFICADO procesos nuevos + navegador | Reinicio completo de SO NO VERIFICADO |
| E03 varios IVA y descuento autorizado | VERIFICADO servicio + CRUD navegador/F1 | Configuración de impuestos reales por negocio pendiente |
| E04 mixto y caja solo efectivo | VERIFICADO | Datáfono/banco real NO VERIFICADO |
| E05 doble cobro | VERIFICADO dos procesos: venta/factura/alta únicas | Carga/LAN real mayor NO VERIFICADA |
| E06 impresora caída | VERIFICADO simulador/errores, copia sin recobro | Dispositivo físico BLOQUEADO |
| E07 Internet/AEAT caída | VERIFICADO fallo de red simulado, outbox intacto | Entorno oficial BLOQUEADO |
| E08 rechazo y subsanación | VERIFICADO SOAP sintético validado XSD y origen conservado | Rechazo/subsanación oficiales BLOQUEADOS |
| E09 inmutabilidad y rectificación | VERIFICADO ORM/SQL y sellado de nuevas líneas/pagos | Revisión fiscal externa pendiente |
| E10 empleado denegado | VERIFICADO 403 y permisos de servicios | Aceptación con empleados reales NO VERIFICADA |
| E11 jerarquía, elevación y soporte auditado | VERIFICADO, PII requiere aprobación independiente temporal | Aceptación con responsable real NO VERIFICADA |
| E12 backup/restauración sin duplicados | VERIFICADO BD emitida + CLI + hold | Conciliación de acuses AEAT reales BLOQUEADA |
| E13 tres terminales | VERIFICADO tres procesos SQLite locales | Sin certificación de capacidad sostenida |
| E14 80mm, QR escaneado, cajón | SOLO SOFTWARE VERIFICADO: ESC/POS/QR/corte y políticas de cajón | BLOQUEADO FÍSICO completo |
| E15 devolución fiscal y conciliación | VERIFICADO rectificativa total, caja/IVA/métodos netos y rechazo caja obsoleta | Remisión y devolución bancaria reales BLOQUEADAS |
| E16 precio histórico | VERIFICADO snapshots y cambio de catálogo desde navegador | Sin bloqueo adicional identificado por estas pruebas |

## Fiscal y hardware: gates que impiden producción

1. No se ha proporcionado certificado ni autorización del obligado para remisión oficial AEAT. Ningún fixture representa aceptación real. Transporte mTLS, reintentos, respuesta validada XSD/identidad y cadena están preparados; deben ejecutarse y conservarse evidencias oficiales.
2. Falta revisión experta de los tipos de operación soportados, subsanaciones/rectificaciones y configuración fiscal aplicable; falta declaración responsable firmada/publicada por el productor. VERIFACTU_COMPLIANCE.md identifica fuentes oficiales, hashes y correspondencias. No se genera una firma ni declaración ficticia.
3. No se ha proporcionado impresora/cajón ni marca/modelo/firmware: falta imprimir 80mm, escanear QR real, USB/Ethernet, corte y apertura física. HARDWARE.md contiene el checklist.
4. Falta aceptación operativa con propietario, encargado, empleado y Superadmin reales en el equipo destino, además de TLS y arranque automático. Los datos usados aquí son sintéticos.

## Límites funcionales explícitos

- Facturación y hardware en TEST/simulador no autorizan facturar en producción. La activación exige evidencia y revisión; no hay conmutador web que eluda el gate.
- Devolución implementada: rectificación total de una factura; no devolución parcial ni conciliación bancaria automática.
- Tarjeta: confirmación de datáfono externo y referencia; no se simula cobro bancario ni se almacenan números de tarjeta.
- Actualización por paquete local/hash de canal confiable; no hay catálogo remoto ni autoactualización desde Internet. El SHA256 verifica integridad; no constituye firma digital de productor.
- Ensayo de concurrencia: tres procesos locales y dos sobre una misma venta. No establece capacidad comercial máxima. SQLite permanece en disco local del servidor, nunca SMB/NFS.
- Restaurar conserva backup previo y bloquea emisión/remisión/impresión hasta conciliación. El comando de retirada de hold registra hash del informe; no valida automáticamente su veracidad ni sustituye revisión AEAT.

## Arranque por el responsable

Siga [INSTALL.md](INSTALL.md). El instalador solicita el primer Superadmin de forma interactiva; no hay usuario, PIN ni contraseña predeterminados. Cree un Administrador operativo, configure empresa/catálogo/PIN y dispositivos. El acceso técnico a PII por Superadmin exige aprobación de otro administrador.

Documentos: README.md, USER_MANUAL.md, SUPERADMIN.md, SECURITY.md, HARDWARE.md, BACKUP_RESTORE.md, UPDATE.md, VERIFACTU_COMPLIANCE.md, IMPLEMENTATION_STATUS.md y ADRs.
