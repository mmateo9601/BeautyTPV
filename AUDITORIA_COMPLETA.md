# Auditoria integral de BeautyTPV

Referencia funcional: **4ce821e**. Correcciones y pruebas integradas en **7045b03**. El HEAD de partida0861517 solo cambiaba PROMPT_INICIAL_CODEX.md; se conserva ese cambio del usuario. Auditoria iniciada13-11-2026 y consolidada tras el cambio de fecha a14-11-2026. Los instantes exactos constan en JUnit y JSON.

## Dictamen

**697 pruebas aprobadas, 0 fallos, 0 errores y 0 omitidas; 202,53 s.** Incluye diez casos Chromium y pruebas de procesos independientes. Correcciones locales integradas y verificadas; **release productiva BLOQUEADA** por los gates externos enumerados al final.

El commit de referencia pasa112 pruebas en una copia aislada. Eso NO demostraba que todo el playbook estuviera completo. Se reprodujeron defectos adicionales, se corrigieron y se conectaron funcionalidades que no tenian flujo completo. Una primera integracion ampliada paso654 casos. El resultado definitivo se detalla al finalizar las verificaciones.

La produccion fiscal sigue **BLOQUEADA**: faltan certificado/autorizacion AEAT, remision y acuses oficiales, revision experta y declaracion responsable suscrita, impresora/cajon reales y validacion del equipo de destino. Ninguna respuesta sintetica representa una aceptacion AEAT.

## Metodo, alcance y estados

- Se leyeron AGENTS.md, PLAYBOOK.md y las ocho configuraciones especializadas. El arquitecto comunico ownership antes del paralelo. Algunos turnos se interrumpieron por cuota; el coordinador asumio e integro lo pendiente. [Contrato de auditoria](docs/audit/CONTRACTS_AUDIT.md).
- Se exporto el commit4ce821e con git archive y se ejecutaron sus pruebas sin modificarlo. La revision final combina codigo, formularios, permisos, servicios, transacciones, DB, colas y navegador.
- La matriz de denegaciones usa objetos reales. Un400,404, archivo o boton existente NO demuestra un flujo positivo: estos tienen pruebas separadas de formulario/HTTP/servicio/DB o Chromium.
- No se desactivaron triggers productivos ni se borraron pruebas para conseguir resultados verdes. Los errores transitorios de integracion se corrigieron y se repitieron sus casos.

| Estado | Significado |
|---|---|
| COMPLETO | Implementado y verificado en el escenario indicado |
| PARCIAL | Existe, pero falta alcance o cobertura local |
| PENDIENTE | No implementado |
| BLOQUEADO | Requiere certificado, dispositivo, firma, personas/equipo o servicio externo |

El alcance fiscal comprobado es IVA general S1/01, F1/F2 y rectificativa **total** R1/R5. No se anuncian como implementados devoluciones parciales, regimenes especiales/exenciones/IGIC/IPSI, integracion bancaria automatica, migracion PostgreSQL ni catalogo remoto de versiones. Agenda, bonos y portal Cliente estan fuera de V1. Una prueba local no acredita la adecuacion juridica de los impuestos de un negocio real.

## Inventario completo

Referencia: 62 rutas, 30 modelos, 205 funciones, 32 plantillas y 19 comandos. Actual: **75 rutas, 33 modelos, 274 funciones, 34 plantillas y 23 comandos**. El inventario cuenta funciones propias de aplicaciones/scripts; no cuenta cada parametrizacion de tests como una funcion de producto.

- [Inventario baseline](docs/audit/baseline/INVENTARIO.md) y [JSON](docs/audit/baseline/inventory.json).
- [Inventario final](docs/audit/final/INVENTARIO.md) y [JSON](docs/audit/final/inventory.json): todas las rutas/vistas, archivo/linea, roles, elevacion, metodos y plantillas; modelos/campos/FK/constraints; funciones/metodos/decoradores; formularios/enlaces/HTMX y comandos.
- [Indice de pruebas concretas](docs/audit/TEST_INDEX.md). El numero de casos incluye parametrizaciones, no equivale al numero de requisitos.
- El bridge de maquina usa terminal activa, Bearer con hash y nonce de lease. Es CSRF-exempt porque no usa cookies; eso NO lo convierte en publico. Los POST de usuario conservan CSRF.
- Las vistas con minimo ADMIN/SUPERADMIN exigen elevacion aunque no escriban elevated=True literalmente: el decorador aplica esa regla.

## Claves de evidencia

| Clave | Pruebas / evidencia |
|---|---|
| BASE | [112 pruebas originales aisladas](docs/evidence/audit-baseline-tests.xml) |
| SEC | [Seguridad y regresiones](tests/test_audit_security.py), [suite inicial](tests/test_security.py) |
| URL | [Todas las rutas y roles, PII, CSRF y enlaces](tests/test_audit_matrix.py) |
| NEGOCIO | [Estados, notas, terminales, limites e informes](tests/test_audit_backend.py), [operativa original](tests/test_backend.py) |
| FORM | [POST positivos desde formularios hasta DB](tests/test_audit_forms.py) |
| FISCAL | [Fiscal ampliado](tests/test_audit_fiscal.py), [vectores/XSD/PDF originales](tests/test_fiscal.py) |
| HW | [Hardware/bridge ampliado](tests/test_audit_hardware.py), [original](tests/test_hardware.py) |
| OPS | [Operaciones ampliadas](tests/test_audit_ops.py), [backup/restore/update](tests/test_backup.py) |
| E2E | [Flujos navegador originales](tests/e2e/test_browser.py), [estados/roles/HTMX](tests/e2e/test_audit_ui.py), [Superadmin real](tests/e2e/test_audit_acceptance.py) |
| ACEPTACION | [E01-E16 de servicio](tests/test_acceptance.py), [procesos/concurrencia/caida real](tests/test_concurrency.py) |
| CONFIG | [Salud/configuracion](tests/test_audit_configuration.py), [regresiones integradas](tests/test_regressions.py) |
| RECOVERY | [Upgrade4ce821e, instalacion nueva y CLI real](docs/evidence/audit-upgrade-recovery.json) |
| CARGA | [Benchmark SQLite sintetico](docs/evidence/audit-sqlite-benchmark.json) |
| DEPS | [Consulta OSV de versiones fijadas](docs/evidence/audit-dependencies.json) |

## Matriz del playbook

La columna base refleja implementacion y evidencia, no mera presencia. El estado final se limita al escenario descrito y a las pruebas citadas. Los bloqueos externos se separan de los componentes locales.

| ID | Playbook | Requisito y alcance comprobado | Base | Final | Evidencia |
|---|---|---|---|---|---|
| A01 |0,2,9 | Una instalacion por empresa, singleton y SQLite local; sin tenants/SaaS | COMPLETO | COMPLETO | NEGOCIO,RECOVERY; constraint single_company_installation |
| A02 |0,2 | Django, Bootstrap5 y HTMX locales, sin CDN necesario en operativa | COMPLETO | COMPLETO | E2E; static/vendor con licencias |
| A03 |0,5 | Cuatro roles internos; Cliente sin login/portal/citas en V1 | COMPLETO | COMPLETO | SEC,URL; User.Role |
| A04 |2,3 | Decimal, precio IVA incluido, redondeo por linea y desglose | COMPLETO | COMPLETO | NEGOCIO,ACEPTACION |
| A05 |2,3 | UTC y zona de empresa validada para fecha fiscal/presentacion/informes | PARCIAL | COMPLETO | CONFIG,FISCAL; CompanyTimezoneMiddleware |
| A06 |3,9 | Atomic corto, CAS, constraints y retry seguro de locked sin row locks | PARCIAL | COMPLETO | NEGOCIO,ACEPTACION; atomic_retry |
| A07 |9 | Benchmark y criterio documentado de evolucion PostgreSQL | PARCIAL | COMPLETO | CARGA; docs/POSTGRESQL_FUTURE.md |
| A08 |9 | Procedimiento futuro de migracion sin migrar ahora | COMPLETO | COMPLETO | docs/POSTGRESQL_FUTURE.md; SQLite sigue activo |
| P01 |4.1,6 | Inicio plano A1/A2/A3 y B1, tactil/accesible | COMPLETO | COMPLETO | E2E,NEGOCIO; bootstrap sin usuarios |
| P02 |4.1 | Crear/editar/eliminar secciones y puestos, impedir borrado con historial | PARCIAL | COMPLETO | NEGOCIO,FORM,CONFIG |
| P03 |4.1,E02 | Una cuenta activa por puesto y recuperar cada cuenta tras procesos nuevos | COMPLETO | COMPLETO | ACEPTACION,E2E |
| P04 |4.1 | Libre/ocupado/en cobro como estados persistidos, no solo etiqueta | PARCIAL | COMPLETO | NEGOCIO,E2E; prepare_payment/resume_ticket |
| P05 |4.1 | Agregar/quitar, cantidad, descuentos autorizados y versionado | COMPLETO | COMPLETO | NEGOCIO,FORM,URL |
| P06 |4.1 | Notas de linea desde interfaz hasta DB y recuperacion | PARCIAL | COMPLETO | NEGOCIO,E2E; limite500 y cuenta no editable en cobro |
| P07 |6.3 | Busqueda y categorias utilizables en la cuenta | PARCIAL | COMPLETO | NEGOCIO,E2E |
| P08 |4.1 | HTMX real, loading/error/doble envio y conflictos | PARCIAL | COMPLETO | E2E prueba HX-Request y DOM; ACEPTACION CAS/idempotencia |
| P09 |4.2 | Venta rapida opcional configurable y persistente por usuario/terminal | PENDIENTE | COMPLETO | NEGOCIO; quick_sale_enabled y quick_ticket |
| P10 |3,4.5 | Terminales, seleccion de acceso y contexto auditado | PENDIENTE | COMPLETO | SEC,E2E; Terminal, hash token y last_seen |
| V01 |4.2,E01 | Efectivo recibido/cambio, caja y solicitud de cajon | COMPLETO | COMPLETO | ACEPTACION,E2E,HW |
| V02 |4.2 | Tarjeta con referencia de confirmacion externa, sin PAN almacenado | COMPLETO | COMPLETO | NEGOCIO,E2E; no se simula cobro bancario |
| V03 |4.2,E04 | Mixto, suma exacta y caja solo por efectivo | COMPLETO | COMPLETO | ACEPTACION,NEGOCIO |
| V04 |4.2 | Caja abierta requerida para efectivo; se comprueba estado actual | COMPLETO | COMPLETO | NEGOCIO,ACEPTACION; rechaza objetos obsoletos |
| V05 |4.2,E05 | Doble clic/dos terminales: una venta/factura/alta/original | COMPLETO | COMPLETO | ACEPTACION; procesos misma y distinta clave |
| V06 |7.8 | Caida real despues de factura/spool, antes de commit y recuperacion | PARCIAL | COMPLETO | test_real_process_death_rolls_back_invoice_sequence_and_spool |
| V07 |4.2 | IDs/montos extremos/malformados no producen500 ni venta parcial | PARCIAL | COMPLETO | NEGOCIO,FISCAL; incluye total superior a capacidad del campo |
| V08 |4.2 | Abrir, cerrar, arqueo y diferencias persistentes | COMPLETO | COMPLETO | NEGOCIO,FORM,E2E |
| V09 |3,4.2 | Ingreso/retirada/ajuste IN/OUT con motivo y Manager ejecutor/autorizador | COMPLETO | COMPLETO | NEGOCIO,FORM; sin reescribir movimientos anteriores |
| V10 |3,4.2 | Historial caja/movimientos/ventas protegido incluso SQL REPLACE | PARCIAL | COMPLETO | NEGOCIO,CONFIG; triggers UPDATE/DELETE/INSERT |
| V11 |4.2,4.7 | Cancelacion de cuenta separada de factura, responsable/fecha/informe | PARCIAL | COMPLETO | FORM,NEGOCIO,RECOVERY; backfill desde AuditEvent, no fecha inventada |
| V12 |5 | Empleado ve caja activa y turnos propios, no cierres ajenos | PARCIAL | COMPLETO | FORM; superiores conservan supervision |
| C01 |4.3 | Clientes crear/leer/editar y borrar solo ficha sin historial | COMPLETO | COMPLETO | FORM,CONFIG; borrado Admin elevado, PROTECT |
| C02 |4.3 | Buscar nombre/telefono y consultar ficha/historial | COMPLETO | COMPLETO | FORM,E2E; enlaces factura ajena ocultos al empleado |
| C03 |4.3 | Exportacion controlada y CSV sin formulas de usuario | COMPLETO | COMPLETO | CONFIG; Admin elevado y PII independiente para tecnico |
| C04 |4.3 | Catalogo servicio/producto, categorias CRUD, precio/IVA/activo | COMPLETO | COMPLETO | FORM,E2E,CONFIG |
| C05 |4.3,E16 | Cambios de catalogo no alteran snapshots historicos | COMPLETO | COMPLETO | ACEPTACION,E2E,FORM |
| C06 |5 | Modelo comercial, base juridica y minimizacion de PII | COMPLETO | COMPLETO | customers.Customer/CustomerForm; SEC y export controlado |
| F01 |3,4.4 | F1/F2, datos obligatorios y umbral conservador soportado | COMPLETO | COMPLETO | FISCAL,E2E; sin cliente completo no supera400EUR |
| F02 |3,4.4 | Series distintas por tipo/ejercicio y numeracion transaccional | PARCIAL | COMPLETO | NEGOCIO,ACEPTACION,FORM; contador sin edicion web |
| F03 |4.4,E09 | Factura/lineas/cobros sellados, sin update/delete/replace/insert posterior | PARCIAL | COMPLETO | FISCAL,CONFIG,NEGOCIO |
| F04 |4.2,E15 | Rectificativa total R1/R5, original intacto, devolucion conciliada | COMPLETO | COMPLETO | FISCAL,FORM,ACEPTACION; caja cerrada/sin saldo rechazada |
| F05 |4.4 | WSDL/XSD oficiales fijados y fuentes tecnicas reconsultadas | COMPLETO | COMPLETO | FISCAL; 8 hashes fijados y4 reconsultados coincidentes |
| F06 |4.4 | Huella SHA256 exacta y cadena por instalacion | COMPLETO | COMPLETO | FISCAL;3 vectores oficiales alta inicial/encadenada/anulacion |
| F07 |4.4 | Verificar cadena contra XML/factura/identidad, no solo texto almacenado | PARCIAL | COMPLETO | FISCAL ampliado; rechaza manipulaciones |
| F08 |4.4 | XML validado y transporte SOAP mTLS preparado | PARCIAL | COMPLETO | FISCAL; XSD previo al envio y respuesta ligada a operacion/identidad |
| F09 |4.4 | Outbox en unidad de factura, worker separado y recuperable | COMPLETO | COMPLETO | FISCAL,ACEPTACION; red fuera de atomic financiero |
| F10 |4.4 | TiempoEsperaEnvio y exclusion concurrente por entorno | PENDIENTE | COMPLETO | FISCAL; FiscalEndpointState persistente y fencing |
| F11 |4.4,E07-E08 | Red/retry/rechazo/duplicados/aceptado con errores visibles y preservados | PARCIAL | COMPLETO | FISCAL,ACEPTACION; DUPLICATE_REVIEW no presume aceptacion |
| F12 |4.4 | Subsanacion preserva tipo/origen y flags S/X o S segun respuesta | PARCIAL | COMPLETO | FISCAL; ALTA/ANULACION y ACCEPTED_WITH_ERRORS |
| F13 |4.4 | Anulacion registral autorizada/auditada separada de devolucion | PARCIAL | COMPLETO | FISCAL,URL; confirmacion, motivo y sin registro previo |
| F14 |4.4 | PDF/QR preparados y copia identificada | COMPLETO | COMPLETO | FISCAL,E2E; lectura fisica se separa en H08 |
| F15 |4.4 | Certificado/modo/obligado configurables protegidos; clave fuera de DB | PARCIAL | COMPLETO | OPS,E2E; referencias externas, caducidad y key match |
| F16 |4.4 | Guard de produccion incluso si cambia empresa mutable a TEST | PARCIAL | COMPLETO | FISCAL; usa modo inmutable de factura/outbox |
| F17 |4.4 | Remision y acuses reales AEAT con certificado autorizado | BLOQUEADO | BLOQUEADO | No certificado/autorizacion; SOAP sintetico no satisface este punto |
| F18 |4.4 | Revision normativa/regimen real y declaracion responsable suscrita | BLOQUEADO | BLOQUEADO | Borrador no firmado; docs/DECLARACION_RESPONSABLE_TEMPLATE.md |
| H01 |4.5 | Drivers TCP/USB/serie, corte y QR preparados | COMPLETO | COMPLETO | HW; TCP loopback exacto, USB/serie sin prueba fisica |
| H02 |4.5 | Spool persistente, copias y fallo/config impresora no revierten venta | PARCIAL | COMPLETO | HW,ACEPTACION |
| H03 |4.5 | Intencion/eventos inmutables, UNKNOWN sin reenvio inseguro | PARCIAL | COMPLETO | HW; lease, ACK idempotente y guards de reemplazo |
| H04 |4.5 | Bridge remoto instalable por terminal sin SQLite compartida | PENDIENTE | COMPLETO | HW; HTTPS/Bearer, claim/ACK y journal previo a IO |
| H05 |4.5 | Routing al terminal de cobro, fallback local y permisos test/cajon | PARCIAL | COMPLETO | HW,NEGOCIO; copia sin cajon, TECHNICAL para pruebas/retry |
| H06 |4.5 | Encoding/codepage validado y texto sin inyeccion ESC/POS | PARCIAL | COMPLETO | HW; whitelist y snapshot de intencion |
| H07 |4.5 | Ticket F1/rectificativo con cliente/referencia/motivo | PARCIAL | COMPLETO | HW; contenido termico de tipos soportados |
| H08 |E14 | Papel80mm, escaneoQR, corte/cajon/modelo/firmware fisicos | BLOQUEADO | BLOQUEADO | No dispositivos; DONE solo significa transporte de bytes |
| H09 |4.5,7.6 | Instalacion/autoinicio de agente y TLS en terminal fisica | BLOQUEADO | BLOQUEADO | Comando preparado; equipo/CA de destino no disponibles |
| S01 |5 | PIN hash y rate limit persistente usuario/origen | PARCIAL | COMPLETO | SEC; coste equivalente y origen bloqueado sin crecimiento de filas |
| S02 |5 | Acceso tactil, terminal y password exacta; PIN nunca eleva | PARCIAL | COMPLETO | SEC,E2E; preserva espacios de contrasena |
| S03 |5 | Cuatro roles: backend y pantallas visibles autorizados | PARCIAL | COMPLETO | URL,SEC,E2E; toda ruta con politica explicita |
| S04 |5 | Superadmin administra Superadmin; Admin solo inferiores | PARCIAL | COMPLETO | SEC; recarga actor/destinatario y version, no flags obsoletos |
| S05 |5 | Elevacion y expiracion para toda administracion sensible | PARCIAL | COMPLETO | SEC; catalogo/plano incluidos; NaN/Infinity/bool no autorizan |
| S06 |5 | Cambio PIN/password/rol/actividad revoca sesion y concesiones | PARCIAL | COMPLETO | SEC,FORM; HMAC/auth_version, limpia flags al degradar |
| S07 |4.6 | Soporte temporal justificado con scope, aprobador y PII independiente | PARCIAL | COMPLETO | SEC,URL; sin bypass POST ni aprobacion propia PII |
| S08 |5 | CSRF, logoutPOST, cookies y secretos externos en produccion | COMPLETO | COMPLETO | URL,CONFIG; sin secret externo no arranca modo seguro |
| S09 |3,5 | Auditoria append-only, metadatos filtrados, digest y terminal | PARCIAL | COMPLETO | SEC; REPLACE bloqueado, contexto aislado |
| S10 |4.6 | Panel propio salud/version/DB/disco/migraciones/colas | PARCIAL | COMPLETO | CONFIG,E2E; datos medidos y supervision explicita |
| S11 |4.6 | Diagnostico DB/red sin envio/certificado/permisos/logs/export saneado | COMPLETO | COMPLETO | OPS,ACEPTACION,E2E; sin claves o PII innecesaria |
| S12 |4.6 | Usuarios/PIN/desbloqueo/dispositivos/terminales/ajustes funcionales | PARCIAL | COMPLETO | FORM,OPS,E2E; formularios positivos guardan DB |
| S13 |4.6 | Backup consistente/cifrado/descarga/politica y retencion | COMPLETO | COMPLETO | OPS,E2E,RECOVERY; error fiscal no suprime backup |
| S14 |4.6 | Restore asistido con confirmacion/mantenimiento y sin swap web de DB viva | PARCIAL | COMPLETO | E2E,RECOVERY; asistente verifica archivo y guia CLI offline |
| S15 |4.6,E12 | Restore en entorno nuevo, integridad/copia previa/hold/no duplicados | COMPLETO | COMPLETO | RECOVERY,ACEPTACION; conciliar antes de retirar hold |
| S16 |4.6 | Comprobar paquete/version/deps, backup previo y migraciones | PARCIAL | COMPLETO | OPS; preflight SHA/rutas/deps, staging y release metadata |
| S17 |4.6 | Rollback de codigo ante IO parcial, nunca retroceso fiscal automatico | PARCIAL | COMPLETO | OPS; BD preservada y hold si falla |
| S18 |4.6 | Workers/servicio medidos y reaccion a hijo muerto | PARCIAL | COMPLETO | OPS; heartbeat y cierre real del servidor temporal al matar worker |
| S19 |5,7.8 | Dependencias y vulnerabilidades publicas conocidas | PARCIAL | COMPLETO | DEPS;36 versiones consultadas,0 avisos; pip check limpio |
| S20 |5 | TLS/firewall/ACL/custodia de backups del equipo de destino | BLOQUEADO | BLOQUEADO | Configuracion preparada; no se ha validado ese despliegue externo |
| R01 |4.7 | Informes periodo/caja/metodo/servicio/empleado/IVA/documentos/anulaciones | PARCIAL | COMPLETO | NEGOCIO,FORM; filtros seleccionan operaciones completas y desglosan componentes |
| R02 |4.7 | CSV y conciliacion ventas/cobros/devoluciones/documentos | PARCIAL | COMPLETO | NEGOCIO,ACEPTACION; metodos/empleados/IVA netos y formulas neutralizadas |
| R03 |4.7 | Auditoria/incidencias segun rol y scopes de datos | PARCIAL | COMPLETO | URL,SEC,FORM; Empleado sin informes globales |
| Q01 |7-8 | Gates/migraciones/tests locales E01-E16 | PARCIAL | COMPLETO | JUnit final y pruebas ampliadas; limites externos separados |
| Q02 |7.8 | Instalador nuevo y upgrade preservando factura/cuentas/cadena | COMPLETO | COMPLETO | RECOVERY; cero usuarios semilla |
| Q03 |12 | Manuales/contratos/estado/release y matriz con bloqueos honestos | COMPLETO | COMPLETO | Este informe y docs/IMPLEMENTATION_STATUS.md, docs/RELEASE_REPORT.md |
| Q04 |7.0 | CI remota realmente ejecutada | BLOQUEADO | BLOQUEADO | Workflow preparado; no se publica ni atribuye una ejecucion externa |
| Q05 |7.8 | Aceptacion con propietario/encargado/empleado/Superadmin reales | BLOQUEADO | BLOQUEADO | Pruebas sinteticas no sustituyen personas del negocio |

## Roles, scopes y pantallas

| Capacidad | Empleado | Encargado | Administrador | Superadmin |
|---|---|---|---|---|
| Plano/cuentas/agregar/cobrar | Si | Si | Si | Si, PII temporal en rutas sensibles |
| Caja | Activas y propias | Supervision | Todas | Todas |
| Reducir/quitar/descuento especial/anular/cerrar |403 | Si | Si | Si |
| Clientes/facturas | Comercial; facturas propias | Operativa | Operativa | PII aprobado por otro administrador activo |
| Informes |403 | Supervision | Globales | PII temporal |
| Catalogo/plano configurable |403 |403 | Elevada | Elevada |
| Empresa/series/equipo/auditoria |403 |403 | Elevada; solo inferiores | Elevada; gestiona Superadmin |
| Soporte/hardware/backup/versiones |403 |403 |403 | Elevada + alcance cuando corresponde |
| Bridge de maquina | Ninguna cookie basta | Igual | Igual | Tambien requiere token terminal |

El PIN no concede elevacion. Cambiar credenciales/rol/actividad revoca sesiones y concesiones; reactivar no resucita autorizaciones anteriores. PII exige otro aprobador, activo y con rango suficiente. El servicio sin request comprueba rol/estado/version persistidos; su entrada HTTP aporta elevacion. CLI de mantenimiento exige acceso OS/configuracion externa y lock exclusivo, no es un endpoint publico.

La matriz URL usa PK reales, no meras404. Sus POST invalidos prueban permisos/no500, no exito de negocio: FORM y E2E aportan las operaciones positivas. Los enlaces visibles se abren y se contrastan con backend. Los alias billing:index/list son dos nombres de una pantalla, no dos funcionalidades.

## Flujos completos E01-E16

| Escenario | Software | Limite externo |
|---|---|---|
| E01 PIN->caja->A1->servicio->efectivo->factura/PDF/QR->cola/copia->informe->cierre | COMPLETO: navegador/DB y spool | BLOQUEADO papel/cajon real |
| E02 A1/A2, volver y recuperar con procesos/sesiones nuevos | COMPLETO | No se reinicio el PC del usuario |
| E03 tipos IVA/descuento/cliente/F1 | COMPLETO: calculos y navegador | Regimen real requiere experto |
| E04 mixto | COMPLETO: componentes/cuadre | Banco/datafono real no verificado |
| E05 doble cobro | COMPLETO: procesos misma/diferente clave | No certifica capacidad LAN |
| E06 impresora caida | COMPLETO: transporte/configuracion, copia y UNKNOWN | BLOQUEADO dispositivo fisico |
| E07 red/AEAT caida | COMPLETO: fallo de red identificado y outbox intacto | BLOQUEADO entorno oficial |
| E08 rechazo/subsanacion | COMPLETO: SOAP sintetico validado XSD, origen intacto | BLOQUEADO acuse/rechazo AEAT real |
| E09 inmutabilidad/rectificacion | COMPLETO: ORM/SQL/REPLACE | Revision normativa externa pendiente |
| E10 empleado sin cierre/informes/soporte | COMPLETO:403 y servicios | Aceptacion humana no realizada |
| E11 jerarquia/elevacion/soporte auditado | COMPLETO: matriz y formularios | Responsable real pendiente |
| E12 backup/restore | COMPLETO: BD emitida y CLI, hold sin duplicados | BLOQUEADO conciliacion acuses reales |
| E13 tres y seis procesos SQLite | COMPLETO: coherencia y benchmark local | Sin umbral comercial certificado |
| E14 80mm/QR/cajon | Solo bytes/protocolo verificados | BLOQUEADO fisico |
| E15 devolucion total R1/R5 | COMPLETO: HTTP/DB/caja/IVA/metodos | BLOQUEADO envio y devolucion bancaria reales |
| E16 cambio de precios | COMPLETO: snapshot historico | Sin bloqueo adicional por esa prueba |

La prueba de caida termina un subproceso con os._exit91 despues de crear factura y spool, antes del commit. El siguiente proceso verifica cero ventas/altas/trabajos, cuenta PAYMENT_PENDING y linea preservadas. El reintento crea una factura con numero1. No se desactivan triggers para probarlo.

## Defectos encontrados y corregidos

- [Seguridad](docs/audit/SECURITY_FINDINGS.md): sesiones que sobrevivian a resetPIN/promocion, actores/destinatarios obsoletos, bypass PII por POST, elevacion incompleta, REPLACE de auditoria, throttling y passwords con espacios. El coordinador limpia ademas flags Django al degradar y limita historico cerrado ajeno al Empleado.
- [Fiscal](docs/audit/FISCAL_FINDINGS.md): cadena verificada parcialmente, sin espera/fencing de endpoint, guard segun empresa mutable, estados cortos, correccion equivocada de ANULACION/aceptados con errores, fecha/version/productor y reemplazos SQL. La anulacion registral tiene confirmacion y motivo, no devuelve una venta.
- [Hardware](docs/audit/HARDWARE_FINDINGS.md): configuracion invalida podia abortar venta, permisos tecnicos incompletos, intencion mutable, leases con falso DONE, F1 incompleta y ausencia de routing/bridge remoto. Se limita encoding para impedir convertir Unicode en controles ESC/POS.
- [Operaciones](docs/audit/OPS_FINDINGS.md): rollback no cubria IO parcial, dependencias sin preflight, version hardcode, workers muertos con web aparentemente sana, errores fiscales que impedian backup y falta de terminales/referencias/desbloqueo.
- [Interfaz](docs/audit/FRONTEND_FINDINGS.md): HTML de informes dentro de title, edicion de cuentas cerradas/en cobro, notas/categorias/venta rapida sin flujo, secciones sin mantenimiento y funciones tecnicas sin enlace. Se corrigio tambien el menu fuera del viewport en720px y se comprobo en navegador.
- [Backend/coordinador](docs/audit/BACKEND_FINDINGS.md): estados, notas, quicksale, inputs/extremos, limite agregado del total, reportes y cancelaciones sin fecha. La migracion recupera fecha/actor solo desde auditoria verificable; sin evidencia hay aviso, no una fecha fabricada.

Los errores transitorios de integracion (columnas antes de migrar, import Decimal, import pytest, fixtures sin elevacion/productor actual y conexiones de inspeccion Windows sin cierre explicito) se corrigieron y repitieron. No se atribuyen al baseline ni se han suprimido sus assertions.

## Simulaciones, datos ficticios y codigo provisional

- Empresas/credenciales/referencias de tests son sinteticas, en DB temporales. El driver QA exige DB explicita y BEAUTYTPV_TEST_PROCESS=1. No se activa al instalar/iniciar el producto.
- SIMULATOR requiere desarrollo/configuracion explicita; agente remoto no simula. Transporte SOAP inyectado requiere TESTING=True. No hay aceptacion AEAT inventada en operativa.
- Instalacion real no crea usuarios/PIN/password semilla. El catalogo real empieza vacio y los datos iniciales de empresa requieren configuracion. TEST no otorga validez fiscal.
- No se hallaron TODO/FIXME/NotImplemented en los flujos productivos revisados. El pass del guard PII maneja deliberadamente una denegacion; no es una implementacion vacia.
- Campos informativos legacy de software no reemplazan application_version/release.json. Campos opcionales futuros no se presentan como pantallas V1.
- El programa no promete las extensiones no implementadas enumeradas en el alcance. Una funcionalidad fuera del escenario fiscal soportado no puede activarse afirmando conformidad.

## Dependencias y limites de seguridad

[OSV API oficial](https://google.github.io/osv.dev/api/) se consulto para36 versiones Python/npm fijadas:0 avisos conocidos en esa respuesta. [JSON](docs/evidence/audit-dependencies.json). pip check sin incompatibilidades. No certifica ausencia de vulnerabilidades desconocidas, estado del SO/firmware ni versiones futuras.

Secretos fuera del repositorio; sin campos de PAN o bytes de clave privada PEM en DB. Un administrador del SO capaz de cambiar codigo/esquema/ficheros no esta aislado por los roles aplicativos; se requieren backups y evidencias externas.

## SQLite medido

100 ventas sinteticas:1proceso10ventas,3procesos30,6procesos60. Errores0, cantidades venta/factura iguales y cadena valida. p95 del flujo completo0.1792/0.7839/1.8796s. No incluye LAN, AEAT ni una jornada sostenida.

Criterio interno para revisar capacidad/migracion: errores locked persistentes o p95 superior a2s con carga representativa, tras descartar IO externo dentro de atomic/configuracion incorrecta. No es un limite oficial ni una certificacion comercial de seis terminales. Los agentes no comparten el fichero SQLite por SMB/NFS.

## Comandos y resultados

| Comando / comprobacion | Resultado final |
|---|---|
| pytest -q --junitxml=docs/evidence/audit-final-tests.xml -o junit_family=xunit1 | 697 PASS, 0 FAIL, 0 ERROR, 0 SKIP; 202,53 s |
| manage.py check | 0 incidencias |
| manage.py makemigrations --check --dry-run | Sin cambios |
| manage.py migrate --noinput | Sin migraciones pendientes |
| ruff check . | All checks passed |
| ruff format --check . | 241 archivos correctos |
| pip check | Sin dependencias incompatibles |
| Upgrade desde4ce821e, backup/restore CLI e instalacion nueva | PASS; integridad/huellas preservadas, hold presente, sin usuarios iniciales |
| git diff --check | Sin errores de whitespace |

Dos avisos de la suite: override DATABASES en prueba aislada de restore, y fixture del plugin pytest depreciada para pytest10. No hay fallos ni omisiones. Poppler emitio avisos de fuentes Symbol/ArialUnicode al renderizar la evidencia; salida EXIT0 y revision visual del PDF sin texto recortado. El menu se reviso a720px y390px; el footer permanece accesible. Capturas y PDF contienen datos sinteticos.

- [JUnit baseline](docs/evidence/audit-baseline-tests.xml):112 casos originales aislados.
- [JUnit final](docs/evidence/audit-final-tests.xml):evidencia definitiva del conjunto auditado.
- [Upgrade/instalacion/CLI recovery](docs/evidence/audit-upgrade-recovery.json).
- [Benchmark](docs/evidence/audit-sqlite-benchmark.json).
- [Captura tecnica sintetica](docs/evidence/audit-superadmin.png).

## Bloqueos exactos antes de produccion

1. Certificado/autorizacion del obligado: falta remision mTLS y acuses/duplicados/subsanaciones oficiales. Reconsultar WSDL/XSD publicos no equivale a enviar una factura.
2. Revision experta del regimen/datos reales, productor identificado y declaracion responsable firmada/publicada. El borrador no esta suscrito.
3. Impresora/cajon/modelo/firmware: falta papel80mm, escaneo QR, USB/Ethernet/serie, corte y apertura real.
4. Equipo/LAN: falta TLS de confianza, firewall/ACL, autoarranque de servidor/agente y custodia/restore con acuses reales. La preparacion del software y loopback no validan ese equipo.
5. Personas del negocio para aceptacion operativa y CI remota no ejecutada en esta auditoria.

**No declarar DONE productivo ni retirar el guard fiscal con estas pruebas locales.** Los bloqueos externos no se han sustituido por simulaciones.
