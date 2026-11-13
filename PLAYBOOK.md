# BeautyTPV — Playbook de implementación integral para Codex

**Versión:** 1.0 · **Fecha de especificación:** 13-11-2026 · **Estado inicial:** proyecto desde cero.

## 0. Mandato ejecutivo

Construir una **aplicación real y operativa**, no una demo, con Django + Bootstrap 5 + HTMX + SQLite, instalada **una vez por empresa**, con plano táctil por secciones y puestos, cuentas persistentes, venta y cobro, caja, hardware, facturación fiscal y administración técnica completa. El agente principal de Codex actuará como integrador y delegará trabajo a los agentes especializados definidos en `.codex/agents/`.

**Condición de entrega:** no declarar “terminado” sin recorrer y aprobar todos los criterios de aceptación y evidencias, incluidas pruebas con hardware real y entorno oficial de pruebas de AEAT. Si faltan impresora, cajón, certificado o acceso a AEAT, entregar todo el código, pruebas simuladas y lista precisa de bloqueos; **no afirmar** que el hardware real o la conformidad fiscal se han verificado.

### Decisiones no negociables
- Un solo negocio y una sola instalación: **no SaaS, no tenants, no suscripciones, no panel central multiempresa**.
- SQLite en V1 y ORM Django; arquitectura portable a PostgreSQL; sin SQL exclusivo de PostgreSQL.
- Servidor local en LAN; navegador en terminal o tablet; servicio/bridge local para dispositivos.
- Roles internos jerárquicos: **Empleado < Encargado < Administrador < Superadmin**. Cliente es **rol externo independiente**, sin acceso ni portal en V1; sí ficha de cliente e historial transaccional preparado para futuras citas.
- El Superadmin posee las capacidades operativas de roles inferiores y las de diagnóstico/configuración técnica. El soporte debe usar autorizaciones y trazabilidad para información personal. Ningún rol puede reescribir facturas fiscales emitidas.
- Pantalla inicial: plano por secciones (A: tres puestos; B: uno), con cuentas abiertas persistentes como mesas de un bar. Cambios de puesto y retorno sin perder datos.
- No exigir agenda, reservas, bonos ni portal de clientes en V1. Sí integrar clientes, historial de compras y facturas.
- Catálogo con servicios y productos, precios, impuestos configurables según reglas legales (sin asumir que todo lleva 21 %), descuentos autorizados, efectivo/tarjeta/pago mixto, devoluciones fiscalmente correctas, informes y auditoría.
- VERI*FACTU debe implementarse según la **documentación vigente de la AEAT**, con registros de alta/anulación, huellas, encadenamiento, QR, remisión SOAP/XML, estados y reintentos, trazabilidad, declaración responsable del productor y validación externa antes de producción.

## 1. Agentes y responsabilidades

Usar subagentes personalizados en `.codex/agents/` y orquestación central. Permitir paralelismo solo en módulos con interfaces pactadas.

| Agente | Propiedad principal | Entregables | Criterio de revisión |
|---|---|---|---|
| `architect` | Arquitectura, contratos y modelos transversales | ADRs, árbol repo, APIs internas, esquema de datos, políticas de concurrencia | Sin acoplamiento circular, coherencia con SQLite |
| `backend` | Django, catálogo, puestos, cuentas, cobros, caja, clientes | Migraciones, services, views, permisos y tests | Reglas de negocio y transacciones probadas |
| `frontend` | Bootstrap/HTMX, UI táctil, usabilidad | Templates, componentes, flujos accesibles, pruebas navegador | Flujos completos sin páginas simuladas |
| `fiscal` | Facturación y VERI*FACTU | Modelo fiscal, XML/SOAP, QR, encadenamiento, outbox, tests de contrato | Conforme a esquemas oficiales y pruebas AEAT |
| `hardware` | Impresión y cajón | Bridge ESC/POS, colas, diagnóstico, simulador y tests | Pruebas USB/Ethernet reales cuando disponibles |
| `security` | Autenticación, PIN, permisos, auditoría y RGPD | Threat model, controles, tests de seguridad | Sin escalada de privilegios, mínima exposición |
| `qa` | E2E, estrés SQLite, release | Suite CI, evidencias, matriz de aceptación, checklist | Falla la release si hay críticos |
| `devops` | Instalación local, backup, actualización, recuperación | Scripts, servicios, runbooks, paquete instalable | Instalación/restauración repetibles |

El **agente principal** coordina diseño y merges, prioriza dependencias, resuelve contradicciones y verifica el conjunto. Ningún subagente decide por sí mismo que el producto está terminado.

### Protocolo de coordinación
1. `architect` establece modelos/contratos, nombres y eventos antes de desarrollos paralelos.
2. Agentes trabajan en archivos propios; comunicar cambios de contrato al principal; evitar escrituras concurrentes sobre mismo archivo.
3. `security` revisa cada etapa; `qa` escribe tests antes o junto a la funcionalidad.
4. Cada etapa incluye migraciones, tests, revisión estática, demo manual y documentación.
5. Registrar en `docs/IMPLEMENTATION_STATUS.md`: objetivo, archivos modificados, comandos ejecutados, resultados, bloqueos y próxima etapa.
6. Rechazar mocks en producción; simuladores solo en entorno de pruebas y desarrollo.

## 2. Repositorio esperado

```text
beautytpv/
  AGENTS.md
  PLAYBOOK.md
  pyproject.toml
  .env.example
  config/                 # settings por entorno, urls, asgi/wsgi
  apps/
    accounts/             # User, roles, PIN, login, permisos
    core/                 # Config empresa, terminales, preferencias
    layout/               # Section, Station, estado derivado
    catalog/              # Category, Service/Product, impuestos
    customers/            # Customer, datos de facturación
    pos/                  # OpenTicket, TicketLine, intentos de cobro
    cash/                 # CashRegister, CashSession, movimientos, arqueo
    billing/              # Invoice, InvoiceLine, rectificativas, series
    verifactu/            # cadenas, outbox, XML, SOAP, QR, receipts
    hardware/             # rutas/colas impresión, bridge, diagnóstico
    reports/              # consultas y exportación
    audit/                # AuditEvent append-only
    support/              # Superadmin: salud, backup, logs, actualización
  templates/ static/ locale/
  tests/fixtures/ tests/e2e/
  scripts/                # instalar, iniciar, backup, restaurar, migrar, update
  docs/                   # ADRs, soporte, manual, fiscal, operación
  .codex/agents/
```

Mantener lógica crítica en servicios transaccionales, no dispersa en views ni JavaScript; usar `Decimal` para importes, UTC en persistencia y zona horaria configurable para presentación y fechas fiscales.

## 3. Modelo de datos mínimo (ampliable)

- `CompanySettings` (singleton): razón social, NIF, domicilio, datos fiscales, moneda EUR, timezone, información de productor/software/versionado; credenciales fuera de BD cuando proceda.
- `User`: custom `AbstractUser` desde la primera migración, activo, rol interno, PIN hash, marca de último acceso; nunca texto plano.
- `Customer`: nombre, contactos, datos fiscales opcionales, consentimiento/base jurídica aplicable, relación futura opcional a cuenta externa; no crear cuenta externa en V1.
- `Section`, `Station`: nombre, orden, coordenadas opcionales y disponibilidad; restricciones para nombres/códigos únicos.
- `CatalogItem`: `SERVICE|PRODUCT`, activo, categoría, precio bruto/neto según política explícita, tipo de IVA, duración opcional (futuro), descripción fiscal.
- `OpenTicket`: estación, estado OPEN|PAYMENT_PENDING|CLOSED|CANCELLED, creador, timestamps, version entero; **una cuenta activa por puesto** vía restricción condicional compatible con SQLite.
- `TicketLine`: snapshot de descripción, cantidad, precio, tipo de IVA, descuento y orden; controles sobre valores negativos.
- `CashRegister`, `CashSession`: terminal/caja, apertura/cierre, saldo inicial, esperado, contado, diferencia, usuario, estado; no abrir dos sesiones simultáneas para misma caja.
- `CashMovement`: ingreso/retirada/ajuste con razón, autorizador y usuario; apéndice, no borrar.
- `Payment`: venta, método CASH|CARD|MIXED_COMPONENT, importe, referencia externa opcional, estado, idempotency_key; no almacenar datos completos de tarjetas.
- `Sale`: finalización única, ticket origen, total y desglose impuestos, empleado, cierre de cuenta.
- `InvoiceSequence`: serie + ejercicio + contador, con control de concurrencia y numeración legal.
- `Invoice`, `InvoiceLine`: snapshots inmutables, factura simplificada/completa/rectificativa, impuestos, cliente opcional según tipo, estado documental; vinculación a venta y rectificadas.
- `FiscalRecord`: alta/anulación/subsanación cuando aplique conforme especificación, registro anterior, huella, timestamp, payload canónico, estado.
- `FiscalOutbox` y `FiscalTransmission`: estado PENDING|SENDING|ACCEPTED|REJECTED|RETRY, intentos, respuestas oficiales, referencias; idempotencia.
- `Printer`, `PrintJob`, `HardwareEvent`: conexión local, tipo, estado y reintentos; secretos fuera de logs.
- `AuditEvent`: actor, acción, objeto, fecha, terminal, resultado, metadatos filtrados; inmutabilidad a nivel de aplicación, backups protegidos.
- `SupportSession`: superadmin, autorización/justificación, tiempo de validez, alcance, quién aprobó y auditoría.

### Integridad transaccional
**SQLite tiene un único escritor a la vez.** Usar operaciones cortas, `busy_timeout` y si se valida para la topología, WAL; NO confiar en `select_for_update` como bloqueo fila por fila en SQLite. Reservar y cerrar ventas mediante transacción `atomic`, actualización condicional/versionado optimista y claves idempotentes. Reintentar cuidadosamente el error `database is locked` sin duplicar cobros ni facturas. Hacer pruebas de concurrencia de dos terminales sobre la misma venta. Una caída después de facturar no puede regenerar numeración o documento. Nunca ejecutar la BD en un recurso de red compartido tipo SMB/NFS; el fichero SQLite reside en el servidor y solo Django accede a él.

## 4. Flujos funcionales obligatorios

### 4.1 Plano visual
- Página `/tpv/` por defecto, cuadrícula táctil de secciones A/B editable por admin; puesto libre/ocupado/en cobro, color + texto accesible.
- Click puesto libre: crear/reutilizar cuenta, guardar responsable; click ocupado: recuperar la misma cuenta.
- Añadir/quitar líneas (según autorización), cantidades, descuentos y notas; guardar sin emitir factura.
- Volver al plano y abrir otro puesto preservando cada estado; refresco HTMX, protección frente a doble clic.
- Cuentas interrumpidas recuperables tras reiniciar servidor; impedir borrar puesto con cuenta abierta.

### 4.2 Venta y caja
- Venta desde puesto, o venta rápida sin puesto si se configura; cliente opcional.
- Pago efectivo: recibido/cambio, apertura de cajón y movimiento de caja; tarjeta: registrar confirmación de datáfono externo, sin simular cobro bancario; mixto: desglose y conciliación.
- Validaciones: caja requerida si hay efectivo, saldo de pagos = total, nada de doble cobro, montos positivos, redondeo legal y distribución por IVA.
- Facturar correctamente al formalizar venta; si falla impresión no repetir cobro/factura; reimprimir copia identificada.
- Apertura/cierre de caja con arqueo y diferencias, informes por método de pago, cancelaciones y devoluciones con controles fiscales.
- Anular una cuenta aún no facturada no es anular una factura. Para operaciones ya emitidas, usar facturas rectificativas o flujos oficiales según corresponda, nunca delete.

### 4.3 Clientes y catálogo
- CRUD con búsqueda rápida por nombre/teléfono, protección PII y exportación controlada.
- Catálogo CRUD con servicios/productos, categorías, precios, impuestos, estado activo.
- Congelar descripción, precio e impuestos en líneas emitidas para que cambios futuros no alteren historial.

### 4.4 Facturación y VERI*FACTU
- Validar alcance legal vigente y versionar documentación normativa aplicable. Implementar esquema oficial actualizado, tipos de registros, reglas de encadenamiento, huella SHA-256 **según algoritmo/campos/orden de AEAT**, facturas y QR reglamentario.
- Identificar qué datos de factura/registro son obligatorios según tipo; series separadas cuando corresponda, fechas, impuestos y NIF.
- Construir XML validado con XSD oficial; SOAP por entorno TEST/PRODUCTION; certificados/autenticación segura; parseo de respuestas, duplicados, rechazos, subsanaciones y reintentos.
- Outbox persistente: registro generado en misma unidad transaccional que factura; trabajador separado para remisión. Recuperación tras reinicios y cortes de Internet.
- Impedir alteración/eliminación de documentos emitidos; auditoría y controles al hacer rectificativas. Verificación local de cadena con tests de vectores oficiales cuando estén disponibles.
- Generar PDF y ticket térmico con datos legales y QR exigido; probar impresión real, resolución y lectura del QR.
- Estados mostrados a usuario (pendiente, aceptado, incidencia) sin atribuir a la AEAT una aceptación inexistente.
- Configurar certificado, modo de comunicación y datos del obligado en área protegida; **no permitir facturación productiva sin validaciones fiscales completadas**.
- Incluir `docs/VERIFACTU_COMPLIANCE.md` con mapeo requisito→implementación→test→evidencia y declaración responsable para firma/publicación por productor, no declaración ficticia generada por IA.

**Fuentes de verdad:** sede electrónica AEAT, documentación técnica de sistemas informáticos de facturación/VERI*FACTU, WSDL/XSD, documentación de huellas y códigos QR, FAQ y cambios reglamentarios. No copiar algoritmos de terceros sin validarlos frente a fuente oficial.

### 4.5 Hardware
- Bridge local instalable con configuración por terminal; drivers USB/Ethernet ESC/POS; conexión a cajón por comando de impresora cuando compatible.
- Cola persistente de `PrintJob`; reintentos seguros sin facturas duplicadas; botón 'reimprimir copia'; tickets de prueba; cortes de papel y codificaciones.
- Si se imprime vía navegador como alternativa, documentar límites; impresora ESC/POS y cajón siguen siendo vía bridge de hardware.
- Operaciones de hardware autorizadas, registradas y con estado visible.

### 4.6 Superadmin **completo**
- Área `/soporte/` separada, no mero Django Admin: estado del servidor, versión app/BD, espacio disco, migraciones, estado backups, cola fiscal, dispositivos, servicio impresión, red y latencias (sin prometer métricas que no se midan).
- Diagnóstico con pruebas no destructivas: DB integrity check, test impresora/cajón autorizado, conectividad AEAT sin envío productivo de prueba, revisión de certificados (fecha de caducidad sin exponer clave), cola atascada, permisos y logs saneados.
- Gestión de parámetros técnicos, dispositivos, políticas de backup, recuperación de cola, usuarios/roles inferiores y desbloqueo de PIN bajo auditoría.
- Gestión de copias de seguridad cifradas, restauración asistida con confirmación/ventana de mantenimiento y pruebas periódicas de recuperación; advertir si restauración puede afectar secuencias fiscales y reconciliar antes de reanudar.
- Gestión de actualización: comprobación de versión, migraciones con backup previo, rollback del código **sin reescribir registros fiscales**, historial de actualizaciones, estado del servicio.
- Acceso de soporte bajo autorización/justificación/expiración; todo acceso PII auditado. MFA o autenticación reforzada para acciones críticas; no backdoors ni credenciales predeterminadas activas.
- Exportación de diagnósticos sin secretos ni datos personales innecesarios.

### 4.7 Informes y operaciones
- Ventas por día/período, caja, método de pago, servicio, empleado, IVA, tickets/facturas, anulaciones/rectificativas y exportación CSV.
- Filtros de permisos y reconciliación contra cobros y facturas.
- Registro de eventos de auditoría y consola de incidencias para el admin según permisos.

## 5. Seguridad, roles y límites

| Capacidad | Empleado | Encargado | Admin | Superadmin |
|---|---|---|---|---|
| Plano, cuentas, añadir líneas, cobrar | Sí | Sí | Sí | Sí |
| Descuentos especiales, anular cuenta no emitida, arqueo/cierre | No | Sí | Sí | Sí |
| Informes globales, catálogo, usuarios inferiores | No | Parcial/supervisión | Sí | Sí |
| Datos fiscales de empresa, series autorizadas | No | No | Sí | Sí (auditar) |
| Backup, dispositivos, versiones, diagnóstico profundo | No | No | No | Sí |

- Jerarquía por rango interno + permisos específicos; comprobar **siempre** en servicios/views y scopes de datos, no solo templates.
- Solo Superadmin crea/mantiene perfiles de Superadmin; admin no puede modificar usuarios de nivel igual/superior; encargado solo supervisa acciones autorizadas.
- Cliente: modelo de ficha comercial, **futuro usuario externo** independiente de jerarquía operativa. Sin login/portal/citas en V1.
- PIN con hash Django, rate limiting y bloqueo temporal; pantalla táctil de selección de empleado. Inicio de sesión elevado para admin/superadmin, expiración, CSRF, cookies seguras, registros de sesión.
- Configuración por `ENV`, secrets fuera de repo, HTTPS en acceso remoto o LAN no confiable, firewall, backups cifrados; cumplir principios RGPD, retención y minimización.

## 6. Entregables de interfaz (funcionales)

1. Acceso por empleado y PIN; panel de administración elevado.
2. Plano táctil por secciones y puestos configurables.
3. Pantalla de cuenta abierta con carrito, búsqueda, categorías, descuentos y total.
4. Modal/pantalla de pago efectivo/tarjeta/mixto con cambio y comprobante.
5. Pantallas de caja: abrir, movimientos, arqueo y cerrar.
6. Catálogo de servicios/productos y configuración de precios/IVA.
7. Clientes e historial de ventas/facturas.
8. Facturas, rectificativas, estado VERI*FACTU y reimpresión.
9. Informes y auditoría.
10. Soporte Superadmin: salud, logs, backups, restauración, dispositivos, diagnósticos, usuarios, versión/actualización, cola fiscal.

Accesible con teclado y táctil; acciones con confirmación donde corresponda; mensajes reales de errores, empty states y loading; navegación rápida y persistencia.

## 7. Plan secuencial con gates (NO omitir fases)

### Fase 0 — Repositorio y contratos
- Inicializar repo, pyproject, lint/format/type checks razonables, pytest, Playwright, CI, settings y docs.
- Definir modelo, roles, rutas y contratos; diagramas/ADRs; identificar dependencias fiscales/hardware.
- Gate: CI base verde, `manage.py check`, migraciones limpias, ADRs aprobados.

### Fase 1 — Instalación, seguridad, Superadmin base
- SQLite, custom User, roles, PIN, autenticación elevada, audit log, `CompanySettings`, shell de `/soporte/`.
- Gate: tests de matriz de permisos y escalada, creación inicial sin contraseñas por defecto.

### Fase 2 — Plano y catálogo
- Secciones/puestos, catálogo, plano táctil HTMX, cuentas abiertas, carrito persistente.
- Gate: abrir A1→añadir→volver→abrir A2→volver A1: A1 permanece intacto, incluso tras reinicio.

### Fase 3 — Cobros, caja y ventas
- CashRegister/CashSession, cobros mixtos, idempotencia, cancelaciones y cierre/arqueo.
- Gate: tests de sumas, IVA, cambio, bloqueo de dobles cobros, simulación de usuarios simultáneos.

### Fase 4 — Facturación local inmutable
- Series, facturas simplificadas/completas/rectificativas, PDFs, QR placeholder **solo en test** hasta verificación fiscal, persistencia y auditoría.
- Gate: facturas inmutables, numeración y relaciones con ventas verificadas.

### Fase 5 — VERI*FACTU de verdad
- XSD/WSDL actuales, huella encadenada, outbox, firma/autenticación cuando aplique, transporte y respuestas, gestión fallos/red.
- Gate: XSD oficial, vectores, pruebas del entorno AEAT (si credenciales disponibles), compliance trace y revisión experta. No pasar a producción con fiscal incompleto.

### Fase 6 — Hardware
- Bridge instalado, cola impresión y cajón, reimpresiones, diagnósticos Superadmin, simuladores.
- Gate: pruebas automatizadas con simulador + checklist de pruebas físicas con impresora/cajón; registrar marca/modelo/firmware.

### Fase 7 — Superadmin operativo completo
- Backups/restauración, actualizaciones, monitorización, logs saneados, gestión dispositivos, recuperación de colas y herramientas soporte.
- Gate: restaurar BD desde backup en entorno nuevo, migrar versión y diagnosticar fallo de impresora/AEAT.

### Fase 8 — Integración E2E y release
- E2E desde PIN→plano→servicio→cobro→factura→QR→impresión→cajón→informe→cierre.
- Tests de interrupción, pérdida de red, reinicio en cobro, bloqueo SQLite, integridad fiscal, aislamiento de permisos, recuperación backups y vulnerabilidades.
- Gate: evidencias adjuntas, instalador probado desde cero, manuales, test operativo con propietario/encargado/empleado/superadmin.

## 8. Escenarios E2E obligatorios

- **E01:** abrir turno, cobrar manicura en A1 en efectivo, imprimir, verificar caja y factura, liberar A1.
- **E02:** abrir A1 y A2, cuentas independientes, persistir tras reinicio y volver a cada una.
- **E03:** añadir producto con IVA diferente y descuento autorizado; factura con desglose correcto.
- **E04:** pago mixto, suma exacta y caja actualizada solo por parte en efectivo.
- **E05:** doble clic en cobrar / dos terminales: una venta, un número fiscal, un registro de alta, ningún duplicado.
- **E06:** caída de impresora: venta/factura intactas, trabajo pendiente y reimpresión controlada.
- **E07:** caída de Internet/AEAT: registro encadenado conservado y remisión diferida con resultado visible.
- **E08:** error AEAT: estado y respuesta preservados, corrección/subsanación válida sin adulterar origen.
- **E09:** factura emitida: intento de edición/eliminación bloqueado; rectificación correcta.
- **E10:** empleado intenta cierre, informes o soporte: 403; encargado solicita autorización válida.
- **E11:** admin intenta crear Superadmin: denegado; Superadmin con sesión elevada realiza diagnóstico auditado.
- **E12:** backup/restauración verificada y controlada; no reenvíos/duplicados después.
- **E13:** tres sesiones cliente/terminal simultáneas: cuentas y cierres consistentes con SQLite; límites de capacidad documentados.
- **E14:** comprobante real legible a 80 mm, QR legible, cajón abre en efectivo y no en pago con tarjeta (salvo política explícita).
- **E15:** anulación/devolución posterior a factura mediante flujo fiscal correcto, saldo e informes conciliados.
- **E16:** cambios de precios no alteran factura histórica.

## 9. Requisitos para SQLite y evolución futura

- `db.sqlite3` exclusivamente en disco local fiable del servidor. Copias mediante API de backup SQLite o procedimiento consistente; no copiar fichero vivo sin garantías.
- Afinar `busy_timeout`, WAL si encaja con servicio, transacciones breves, pool/conexiones no excesivas; tests reales con varios procesos.
- No depender de bloqueo por fila. Serializar reservas fiscales de manera compatible con SQLite y probar caída intermedia.
- Diseñar índice, constraints e idempotencia; realizar benchmark que establezca cuándo migrar a PostgreSQL (p. ej., aumento de escrituras simultáneas y bloqueo observado).
- Documentar procedimiento de exportación, migración y comparación de datos; **no ejecutar migración ahora**.

## 10. Criterios de 'DONE' y prohibiciones

**DONE** solo cuando:
- Instalación y primer arranque documentados, repetibles y sin credenciales inseguras.
- Todos los flujos definidos funcionan end-to-end con usuarios reales y datos persistentes.
- Pruebas automatizadas y E2E pasan, sin errores críticos ni TODOs en flujos obligatorios.
- Roles y panel Superadmin funcionan con controles y trazas.
- Facturas se generan y mantienen sin edición; integración fiscal validada contra documentación y entorno oficial con evidencias disponibles.
- Hardware real probado **cuando se proporciona**; si no, no se marca hardware como verificado físicamente.
- Backup/restauración, actualización, recuperación de incidentes y manuales disponibles.
- Se entrega `docs/RELEASE_REPORT.md` que marque **VERIFICADO / NO VERIFICADO / BLOQUEADO** por requisito, sin ocultar limitaciones.

**Prohibido:** sustituir impresión real por `window.print()` como única solución, fingir respuestas AEAT, borrar facturas emitidas, suprimir tests, crear credenciales de superadmin por defecto, almacenar tarjetas o PIN en claro, marcar integraciones no verificadas como listas, convertirlo en SaaS.

## 11. Comandos orientativos de desarrollo y verificación

Estos comandos deben existir mediante scripts/Makefile y estar documentados; adaptar a la estructura final:

```bash
python -m venv .venv
source .venv/bin/activate  # en Windows: .venv\Scripts\activate
pip install -e '.[dev]'
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
pytest -q
ruff check .
ruff format --check .
python manage.py runserver
```

## 12. Documentación final requerida

`README.md`, `docs/INSTALL.md`, `docs/USER_MANUAL.md`, `docs/SUPERADMIN.md`, `docs/SECURITY.md`, `docs/HARDWARE.md`, `docs/VERIFACTU_COMPLIANCE.md`, `docs/BACKUP_RESTORE.md`, `docs/UPDATE.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/RELEASE_REPORT.md`, `docs/ADRs/` y `.env.example`.

## 13. Arranque para agente principal Codex

1. Lee `AGENTS.md`, este `PLAYBOOK.md` y `.codex/agents/`.
2. Haz inventario del repositorio; si está vacío, inicialízalo. Asigna `architect` para contratos y `security`/`fiscal` para riesgos.
3. Divide la implementación siguiendo las fases y asigna subagentes; ejecuta tareas independientes en paralelo, pero integra secuencialmente cambios que toquen modelos compartidos.
4. Implementa código ejecutable, tests y scripts. No te detengas después del plan; continúa hasta los gates de cada fase.
5. Mantén al día `docs/IMPLEMENTATION_STATUS.md` y utiliza PRs/commits pequeños. Si no hay herramientas externas, produce exactamente las evidencias locales posibles y documenta los bloqueos.
6. Antes de finalizar, ejecuta la suite, audita el árbol de proyecto, prueba instalación desde cero y presenta el informe de release con lo validado y lo no validado.

## 14. Referencias oficiales a revisar al implementar

- AEAT técnica: https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu/informacion-tecnica.html
- AEAT FAQs/requisitos: https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu.html
- Django DB/SQLite: https://docs.djangoproject.com/en/5.2/ref/databases/
- Codex subagentes: https://learn.chatgpt.com/docs/agent-configuration/subagents

**Esta especificación define alcance y gates; no supone que el código esté ya implementado.**
