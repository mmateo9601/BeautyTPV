# Contratos de integración BeautyTPV V1

Estado: contrato inicial de Fase 0, 13-11-2026. Cambios coordinados por principal; ningún agente modifica archivos de otro propietario.

## Propiedad de archivos

| Propietario | Archivos exclusivos |
|---|---|
| Principal | config/, manage.py, pyproject.toml, .env.example, CI, apps/__init__.py, docs/IMPLEMENTATION_STATUS.md y RELEASE_REPORT.md; integración y commits |
| architect | docs/CONTRACTS.md, docs/ADRs/ |
| security | apps/accounts/, apps/audit/, tests/test_security.py, docs/SECURITY.md |
| backend | apps/core/, apps/layout/, apps/catalog/, apps/customers/, apps/pos/, apps/cash/, apps/reports/, tests/test_operations.py |
| fiscal | apps/billing/, apps/verifactu/, tests/test_fiscal.py, docs/VERIFACTU_COMPLIANCE.md y documentación/esquemas fiscales |
| hardware | apps/hardware/, tests/test_hardware.py, docs/HARDWARE.md |
| frontend | templates/, static/, docs/USER_MANUAL.md |
| devops | apps/support/, scripts/, tests/test_backup.py, README.md, docs/INSTALL.md, BACKUP_RESTORE.md, UPDATE.md, SUPERADMIN.md |
| qa | tests/e2e/, tests/test_acceptance.py, tests/test_concurrency.py, docs/ACCEPTANCE_MATRIX.md |

Cada propietario crea apps.py, __init__.py, migrations/ y tests de su módulo. Principal ejecuta y puede integrar correcciones una vez concluida la entrega del propietario. Nunca ejecutar makemigrations global concurrentemente: cada propietario limita etiquetas o el principal genera al integrar.

## Dependencias y tipos

Django 5.2 LTS; Bootstrap 5 y HTMX vendorizados para LAN sin Internet. SQLite desde primera migración; User personalizado antes de migrate. Usuario Django settings.AUTH_USER_MODEL y FK con referencia string. Importaciones de servicios cruzados dentro de funciones para evitar ciclos; no efectos externos en transacciones.

Rutas de módulos: accounts, audit, core, layout, catalog, customers, pos, cash, billing, verifactu, hardware, reports, support bajo apps/. URLs del proyecto usan include. Todos los POST llevan CSRF. Servicios públicos reciben actor explícito y validan permisos; no confiar en template.

Importes Decimal a dos decimales; precio de catálogo IVA incluido. Cantidad Decimal(10,3), descuento porcentaje Decimal(5,2), impuesto porcentaje Decimal(5,2). Redondear cada total de línea ROUND_HALF_UP a céntimo; base = bruto/(1+tasa/100) redondeada a céntimo; cuota = bruto-base. Sumar importes de línea por tipo fiscal. No floats ni asumir 21%.

## Seguridad y auditoría

apps.accounts.models.User(AbstractUser): role CharField con EMPLOYEE, MANAGER, ADMIN, SUPERADMIN; pin_hash; métodos set_pin(pin), check_pin(pin). create_superuser fija SUPERADMIN sin password predeterminado. Roles por rango, nunca por is_staff solamente.

apps.accounts.permissions.require_role(user, minimum): lanza django.core.exceptions.PermissionDenied si inactivo/anónimo/rango insuficiente; mínimo como string anterior. Helpers view y permisos específicos se construyen sobre esta función. ADMIN solo gestiona usuarios de rango inferior; SUPERADMIN gestiona SUPERADMIN. Cliente no es User.role ni tiene login.

apps.audit.services.record(actor, action, target='', metadata=None): crea AuditEvent append-only, fecha UTC, actor nullable solo para eventos de sistema. Metadatos filtrados por allowlist sin PIN/password/certificados/tarjeta ni PII innecesaria. Fallo al escribir auditoría de acción crítica aborta transacción.

PIN sujeto a rate limit persistente por usuario y origen; autenticación password refuerza sesión elevada con expiración 10 minutos para acciones técnicas. SupportSession tiene justificación, aprobador, alcance, expires_at, revocación. Una sesión PIN de Superadmin no autoriza restaurar/actualizar.

## Modelo operativo compartido

core.CompanySettings: singleton pk=1, name, tax_id, address, currency EUR, timezone Europe/Madrid, fiscal_mode TEST/PRODUCTION; productor/version fiscal según fiscal. Nunca contiene clave privada.

layout.Section(name, sort_order); Station(section, code único, name, active). Semilla explícita de instalación A1/A2/A3 y B1; sin credenciales semilla. Proteger estaciones con tickets activos.

catalog.Category(name); CatalogItem(kind SERVICE/PRODUCT, name, category nullable, price, tax_rate, active). customers.Customer(name, phone, email, tax_id, address, legal_basis); historial a través de Sale e Invoice.

pos.OpenTicket(station nullable PROTECT, customer nullable PROTECT, status OPEN/PAYMENT_PENDING/CLOSED/CANCELLED, created_by, created_at, version). Constraint condicional una cuenta por puesto en OPEN/PAYMENT_PENDING. TicketLine(ticket, item nullable PROTECT, description snapshot, quantity, unit_price snapshot, tax_rate snapshot, discount_percent, note). Un catálogo cambiado no modifica líneas existentes.

pos.Sale(ticket OneToOne PROTECT, total, created_by, created_at, idempotency_key unique, request_fingerprint). Payment(sale, method CASH/CARD, amount, received opcional, reference, cash_session nullable PROTECT). Mixto son dos Payment, no un método ambiguo. Inmutables tras cierre; nunca datos de tarjeta. Receipt/change no aumenta pago ni saldo.

cash.CashRegister(name); CashSession(register, opened_by, opening_balance, opened_at, closed_at nullable, closed_by nullable, counted nullable, expected nullable, difference nullable). Una abierta por register. CashMovement(session, kind IN/OUT, amount positivo, reason, actor, created_at), append-only. Esperado = apertura + efectivo vendido - efectivo devuelto + IN - OUT.

## Servicios operativos

Backend publica apps.pos.services:

- open_ticket(station, actor) -> OpenTicket: reutiliza activa, restricción DB resuelve carrera.
- add_line(ticket, item, actor, quantity=Decimal('1'), discount_percent=Decimal('0'), expected_version=None) -> TicketLine.
- update_line(line, actor, quantity=None, discount_percent=None, expected_version=None).
- remove_line(line, actor, expected_version=None).
- cancel_ticket(ticket, actor, expected_version=None): MANAGER.
- checkout(ticket, actor, payments, idempotency_key, cash_session=None, expected_version=None) -> Sale.

payments lista de dicts {'method':'CASH'|'CARD', 'amount':Decimal, 'received':Decimal opcional, 'reference':str}. CARD requiere confirmación/referencia explícita del datáfono externo. cash_session requerido si CASH>0. Valida total positivo y suma exacta. Clave reutilizada con distinto payload da ValidationError. Misma clave mismo payload devuelve misma Sale sin nuevos efectos. Otro idempotency_key para ticket cerrado devuelve error/referencia existente sin cobrar.

Dentro de atomic checkout toma escritura condicional de OpenTicket status/version, crea Sale/Payment y llama apps.billing.services.issue_invoice(sale, actor) -> Invoice. Factura y FiscalRecord/outbox son parte de misma transacción. Después llama apps.hardware.services.enqueue_invoice(invoice, actor, open_drawer=cash_amount>0) -> PrintJob; solo crea cola, no IO. Sale.invoice reverse OneToOne fiscal. Fallo previo al commit revierte todo. Error impresora o AEAT después no revierte venta. Eliminar ticket cerrado prohibido.

Backend publica cash.services.open_session(register, actor, opening_balance), add_movement(session, actor, kind, amount, reason), close_session(session, actor, counted); cierre MANAGER y sin modificar movimientos previos.

## Facturas y fiscalidad

billing.InvoiceSequence(series, year, next_number), unique series/year; Invoice(sale OneToOne nullable PROTECT, series, year, number, invoice_type F1/F2/R*, issued_at, issuer snapshot, customer snapshot, total, tax_total, net_total, rectifies nullable PROTECT, fiscal_mode). unique series/year/number. InvoiceLine(invoice, description, quantity, unit_price, discount_percent, tax_rate, net_total, tax_total, total). Número público series-year-number. Inmutabilidad por managers/modelos y triggers SQLite en migración si disponibles; auditoría no sustituye restricción. Rectificativa nuevo documento, serie distinta, referencia original y devolución económica conciliada.

Fiscal publica issue_invoice(sale, actor), rectify_invoice(invoice, actor, reason, ...) con permisos MANAGER como mínimo y reglas oficiales; render_pdf(invoice)->bytes; qr_url(invoice)->str; no QR placeholder en operación productiva.

verifactu.FiscalRecord(invoice FK PROTECT, record_type, previous nullable PROTECT, fingerprint, canonical_payload, created_at, XML inmutable); FiscalOutbox(record OneToOne, status PENDING/SENDING/ACCEPTED/REJECTED/RETRY, attempts, next_attempt_at, lease_until); FiscalTransmission(outbox, requested_at, response, status), append-only. Encadenamiento por instalación/obligado según especificación oficial; no por año o serie sin justificación oficial.

SOAP real separado de emisión: worker consume outbox con lease y CAS, IO fuera de atomic y actualiza resultado corto al final; respuesta oficial guardada saneada y sin credenciales. Timeout tras envío no significa no recibido: reintento mismo registro, interpretar duplicado sin emitir factura nueva. Liberar leases expiradas al reiniciar. Estados jamás ACCEPTED por simulación en DB operativa.

Gate productivo cerrado salvo verificación explícita con evidencia oficial y revisión experta. TEST marcado claramente; facturas de prueba no se presentan como fiscales productivas. Sin certificado, se prueban fixtures/schemas/transporte simulado, se informa BLOQUEADO prueba oficial. No generar declaración responsable firmada ficticia.

## Hardware

hardware.Printer(name, connection_type TCP/USB/SIMULATOR, address, port, enabled), PrintJob(invoice FK PROTECT, printer nullable, kind RECEIPT/COPY/DRAWER/TEST, status PENDING/SENDING/DONE/FAILED/UNKNOWN, attempts, payload, open_drawer, requested_by). HardwareEvent auditado.

hardware.services.enqueue_invoice(invoice, actor, open_drawer=False, copy=False) crea trabajo inmutable de intención. Ticket original único por invoice; copia explícita nueva y visible COPIA. Driver TCP/USB/bridge entrega bytes ESC/POS. Simulador únicamente settings.DEBUG/TEST. Al cortar comunicación tras entrega posible, UNKNOWN requiere decisión humana para evitar doble cajón; nunca vender otra vez.

Bridge local autenticado con allowlist de dispositivos, sin endpoint arbitrario de comandos/shell; privilegios mínimos. Drawer solo efectivo o prueba autorizada; imprimir copia no abre cajón. Worker management command procesa cola. Emisión tiene éxito aunque dispositivo esté desconectado.

## Rutas y templates

URLs principales / -> /tpv/, /acceso/, /salir/, /elevar/, /tpv/, /tpv/puestos/<int:pk>/ (POST abrir/reutilizar), /tpv/cuentas/<int:pk>/, /caja/, /catalogo/, /clientes/, /facturas/, /informes/, /auditoria/, /soporte/. Cada dueño define urls.py namespaced; frontend acuerda nombres con backend antes de templates. Base templates/base.html; errors 403/404/500; usar url reverse, no enlaces POST mediante GET.

Contrato UI: plano context sections con stations y active_ticket; cuenta ticket, lines, items, customers, total, idempotency_key y version; cobro envía clave estable (no regenerar en doble clic). POST exitoso redirect 303/302 o fragmento HTMX accesible. Conflicto versión retorna 409 con recarga; validación 400 con mensaje y datos conservados; denegación 403.

## Soporte y operación

Soporte usa rol SUPERADMIN + sesión elevada + SupportSession para PII/acciones críticas. Diagnósticos medidos, integridad PRAGMA integrity_check, migraciones, disco, versión y colas. Backup mediante sqlite3.Connection.backup, cifrado autenticado, clave fuera repo, manifest hash/version/schema y high-watermarks fiscales. Restauración offline con confirmación explícita, backup previo, integrity check, mantenimiento, conciliación y bloqueo de remisión hasta revisión de secuencias/acuse AEAT. No restaurar DB viva por petición HTTP.

scripts exponen install/start/check/backup/restore/update; no shell arbitraria desde UI. Actualización paquete verificado, backup previo, migraciones, healthcheck, historial; rollback código compatible nunca elimina facturas/registros fiscales. Export diagnóstico allowlist y saneado.

## Gates y pruebas

F0 contratos + settings + check/migrate sin drift + CI base; F1 seguridad negativa e instalación sin password; F2 persistencia A1/A2 reinicio; F3 sumas/IVA/cambio/idempotencia/concurrencia real; F4 inmutabilidad/numeración/rectificaciones; F5 XSD oficial y pruebas AEAT separadas; F6 simulador y checklist físico separado; F7 restore en DB nueva y update; F8 E01-E16, instalador limpio, reporte VERIFICADO/NO VERIFICADO/BLOQUEADO.

pytest usa SQLite en fichero para pruebas de hilos/procesos, no solo :memory:. E2E Playwright interactúa formularios reales y no usa mocks de negocio. Fixtures fiscales/simuladores identificados. Principal mantiene evidencia exacta de comandos y resultados por fase y solo hace commit del gate realmente alcanzado. Fallo fiscal/hardware externo no se oculta bajo gate aprobado: separar código automatizado verificado de validación externa bloqueada.

## Nombres URL y contextos mínimos fijados

| namespace:name | Ruta | Template / contexto |
|---|---|---|
| accounts:login | /acceso/ | accounts/login.html; users, form, error |
| accounts:logout | /salir/ POST | redirect login |
| accounts:elevate | /elevar/ GET/POST | accounts/elevate.html; form, next |
| pos:floor | /tpv/ | pos/floor.html; sections (prefetch stations), tickets_by_station |
| pos:open_station | /tpv/puestos/<int:pk>/ POST | redirect pos:ticket |
| pos:ticket | /tpv/cuentas/<int:pk>/ | pos/ticket.html; ticket, lines, items, customers, total, idempotency_key |
| pos:add_line | /tpv/cuentas/<int:pk>/lineas/ POST | item_id, quantity, discount_percent, version |
| pos:update_line | /tpv/lineas/<int:pk>/ POST | quantity, discount_percent, version |
| pos:remove_line | /tpv/lineas/<int:pk>/eliminar/ POST | version |
| pos:cancel_ticket | /tpv/cuentas/<int:pk>/anular/ POST | version |
| pos:checkout | /tpv/cuentas/<int:pk>/cobrar/ POST | idempotency_key, version, cash_amount, card_amount, received, card_reference, cash_session_id |
| cash:index | /caja/ | cash/index.html; registers, sessions, movements |
| cash:open | /caja/abrir/ POST | register_id, opening_balance |
| cash:movement | /caja/<int:pk>/movimiento/ POST | kind, amount, reason |
| cash:close | /caja/<int:pk>/cerrar/ POST | counted |
| catalog:index | /catalogo/ | catalog/index.html; items, categories, form |
| customers:index | /clientes/ | customers/index.html; customers, form, query |
| billing:index | /facturas/ | billing/index.html; invoices |
| billing:detail | /facturas/<int:pk>/ | billing/detail.html; invoice, lines, fiscal_record |
| billing:pdf | /facturas/<int:pk>/pdf/ | PDF attachment |
| billing:rectify | /facturas/<int:pk>/rectificar/ POST | reason, idempotency_key |
| hardware:reprint | /hardware/facturas/<int:pk>/copia/ POST | redirect invoice |
| reports:index | /informes/ | reports/index.html; totals, payments, tax_totals, rows, start, end |
| audit:index | /auditoria/ | audit/index.html; events |
| support:index | /soporte/ | support/index.html; diagnostics, printers, print_jobs, fiscal_outbox, backups, support_session |

Cada propietario puede añadir URLs CRUD y formularios por necesidades; cambios de estas rutas/nombres se comunican al principal y frontend antes de usarse. Principal config incluye apps.layout/catalog/customers por sus prefijos y apps.pos bajo /tpv/. Namespace no se repite en include interno.

Compatibilidad auditoría acordada con security: record(actor, action, target='', metadata=None, *, obj=None, outcome='SUCCESS'); si obj se proporciona deriva etiqueta/id segura sin serializar PII.
