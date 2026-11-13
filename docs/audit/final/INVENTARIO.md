# Inventario de implementación

Existencia no equivale a requisito COMPLETO. Sin datos del negocio.

75 rutas; 33 modelos; 274 funciones/métodos; 34 plantillas.

## Rutas, vistas y controles declarados

| Ruta | Nombre | Vista | Rol mínimo | Elevación | Métodos | Plantillas |
|---|---|---|---|---|---|---|
| / | <unnamed> | config.urls.<lambda> | PUBLIC | False | UNRESTRICTED |  |
| /acceso/ | accounts:login | apps.accounts.views.login_view | PUBLIC | False | GET, POST | accounts/login.html |
| /salir/ | accounts:logout | apps.accounts.views.logout_view | PUBLIC | False | POST |  |
| /elevar/ | accounts:elevate | apps.accounts.views.elevate_view | AUTHENTICATED | False | GET, POST | accounts/elevate.html |
| /auditoria/ | audit:index | apps.audit.views.index | ADMIN | True | UNRESTRICTED | audit/index.html |
| /tpv/ | pos:floor | apps.pos.views.floor | EMPLOYEE | False | UNRESTRICTED | pos/floor.html |
| /tpv/venta-rapida/ | pos:quick_sale | apps.pos.views.quick_sale | EMPLOYEE | False | POST |  |
| /tpv/cuentas/<int:pk>/preparar-cobro/ | pos:prepare_payment | apps.pos.views.prepare_payment | EMPLOYEE | False | POST |  |
| /tpv/cuentas/<int:pk>/reanudar/ | pos:resume_ticket | apps.pos.views.resume_ticket | EMPLOYEE | False | POST |  |
| /tpv/puestos/<int:pk>/ | pos:open_station | apps.pos.views.open_station | EMPLOYEE | False | POST |  |
| /tpv/cuentas/<int:pk>/ | pos:ticket | apps.pos.views.ticket | EMPLOYEE | False | UNRESTRICTED | pos/ticket.html |
| /tpv/cuentas/<int:pk>/lineas/ | pos:add_line | apps.pos.views.add_line | EMPLOYEE | False | POST |  |
| /tpv/lineas/<int:pk>/ | pos:update_line | apps.pos.views.update_line | EMPLOYEE | False | POST |  |
| /tpv/lineas/<int:pk>/eliminar/ | pos:remove_line | apps.pos.views.remove_line | MANAGER | False | POST |  |
| /tpv/cuentas/<int:pk>/anular/ | pos:cancel_ticket | apps.pos.views.cancel_ticket | MANAGER | False | POST |  |
| /tpv/cuentas/<int:pk>/cliente/ | pos:customer | apps.pos.views.customer | EMPLOYEE | False | POST |  |
| /tpv/cuentas/<int:pk>/cobrar/ | pos:checkout | apps.pos.views.checkout | EMPLOYEE | False | POST |  |
| /plano/configuracion/secciones/<int:pk>/editar/ | layout:section_edit | apps.layout.views.section_edit | ADMIN | True | UNRESTRICTED | layout/form.html |
| /plano/configuracion/secciones/<int:pk>/eliminar/ | layout:section_delete | apps.layout.views.section_delete | ADMIN | True | POST |  |
| /plano/configuracion/ | layout:index | apps.layout.views.index | ADMIN | True | UNRESTRICTED | layout/index.html |
| /plano/configuracion/secciones/ | layout:section_create | apps.layout.views.section_create | ADMIN | True | POST |  |
| /plano/configuracion/puestos/nuevo/ | layout:station_create | apps.layout.views.station_edit | ADMIN | True | UNRESTRICTED | layout/form.html |
| /plano/configuracion/puestos/<int:pk>/editar/ | layout:station_edit | apps.layout.views.station_edit | ADMIN | True | UNRESTRICTED | layout/form.html |
| /plano/configuracion/puestos/<int:pk>/eliminar/ | layout:station_delete | apps.layout.views.station_delete | ADMIN | True | POST |  |
| /catalogo/ | catalog:index | apps.catalog.views.index | ADMIN | True | UNRESTRICTED | catalog/index.html |
| /catalogo/nuevo/ | catalog:create | apps.catalog.views.edit | ADMIN | True | UNRESTRICTED | catalog/form.html |
| /catalogo/<int:pk>/editar/ | catalog:edit | apps.catalog.views.edit | ADMIN | True | UNRESTRICTED | catalog/form.html |
| /catalogo/categorias/ | catalog:category | apps.catalog.views.category | ADMIN | True | UNRESTRICTED | catalog/categories.html |
| /catalogo/categorias/<int:pk>/ | catalog:category_edit | apps.catalog.views.category | ADMIN | True | UNRESTRICTED | catalog/categories.html |
| /catalogo/categorias/<int:pk>/eliminar/ | catalog:category_delete | apps.catalog.views.delete_category | ADMIN | True | POST |  |
| /clientes/ | customers:index | apps.customers.views.index | EMPLOYEE | False | UNRESTRICTED | customers/index.html |
| /clientes/nuevo/ | customers:create | apps.customers.views.edit | EMPLOYEE | False | UNRESTRICTED | customers/form.html |
| /clientes/<int:pk>/ | customers:detail | apps.customers.views.detail | EMPLOYEE | False | UNRESTRICTED | customers/detail.html |
| /clientes/<int:pk>/editar/ | customers:edit | apps.customers.views.edit | EMPLOYEE | False | UNRESTRICTED | customers/form.html |
| /clientes/<int:pk>/eliminar/ | customers:delete | apps.customers.views.delete | ADMIN | True | POST |  |
| /caja/ | cash:index | apps.cash.views.index | EMPLOYEE | False | UNRESTRICTED | cash/index.html |
| /caja/abrir/ | cash:open | apps.cash.views.open | EMPLOYEE | False | POST |  |
| /caja/<int:pk>/movimiento/ | cash:movement | apps.cash.views.movement | MANAGER | False | POST |  |
| /caja/<int:pk>/cerrar/ | cash:close | apps.cash.views.close | MANAGER | False | POST |  |
| /facturas/ | billing:index | apps.billing.views.invoice_list | AUTHENTICATED | False | UNRESTRICTED | billing/list.html |
| /facturas/ | billing:list | apps.billing.views.invoice_list | AUTHENTICATED | False | UNRESTRICTED | billing/list.html |
| /facturas/<int:pk>/ | billing:detail | apps.billing.views.invoice_detail | AUTHENTICATED | False | UNRESTRICTED | billing/detail.html |
| /facturas/<int:pk>/pdf/ | billing:pdf | apps.billing.views.invoice_pdf | AUTHENTICATED | False | UNRESTRICTED |  |
| /facturas/<int:pk>/rectificar/ | billing:rectify | apps.billing.views.rectify | AUTHENTICATED | False | POST |  |
| /facturas/<int:pk>/reimprimir/ | billing:reprint | apps.billing.views.reprint | AUTHENTICATED | False | POST |  |
| /hardware/bridge/<int:terminal_pk>/claim/ | hardware:bridge_claim | apps.hardware.bridge.claim | BRIDGE_BEARER | False | POST |  |
| /hardware/bridge/<int:terminal_pk>/jobs/<int:job_pk>/ack/ | hardware:bridge_ack | apps.hardware.bridge.acknowledge | BRIDGE_BEARER | False | POST |  |
| /hardware/facturas/<int:pk>/copia/ | hardware:reprint | apps.hardware.views.reprint | EMPLOYEE | False | POST |  |
| /hardware/impresoras/<int:pk>/prueba/ | hardware:test | apps.hardware.views.test_printer | SUPERADMIN | True | POST |  |
| /hardware/trabajos/<int:pk>/reintentar/ | hardware:retry | apps.hardware.views.retry | SUPERADMIN | True | POST |  |
| /empresa/ | core:settings | apps.core.views.settings | ADMIN | True | UNRESTRICTED | core/settings.html |
| /informes/ | reports:index | apps.reports.views.index | MANAGER | False | UNRESTRICTED | reports/index.html |
| /soporte/restauracion/ | support:restore_advisor | apps.support.views.restore_advisor | SUPERADMIN | True | UNRESTRICTED | support/restore.html |
| /soporte/terminales/ | support:terminals | apps.support.views.terminals | SUPERADMIN | True | UNRESTRICTED | support/terminals.html |
| /soporte/terminales/<int:pk>/ | support:terminal_edit | apps.support.views.terminal_edit | SUPERADMIN | True | UNRESTRICTED | support/settings.html |
| /soporte/fiscal/ | support:fiscal_settings | apps.support.views.fiscal_settings | SUPERADMIN | True | UNRESTRICTED | support/settings.html |
| /soporte/logs/ | support:logs | apps.support.views.logs | SUPERADMIN | True | UNRESTRICTED |  |
| /soporte/ | support:index | apps.support.views.index | SUPERADMIN | True | UNRESTRICTED | support/index.html |
| /soporte/autorizacion/ | support:authorize | apps.support.views.authorize | SUPERADMIN | True | POST |  |
| /soporte/autorizacion/<int:pk>/revocar/ | support:revoke | apps.support.views.revoke | SUPERADMIN | True | POST |  |
| /soporte/diagnostico/ | support:diagnostic | apps.support.views.diagnostic | SUPERADMIN | True | POST |  |
| /soporte/diagnostico/exportar/ | support:diagnostics_export | apps.support.views.export_diagnostics | SUPERADMIN | True | UNRESTRICTED |  |
| /soporte/backup/ | support:backup | apps.support.views.backup | SUPERADMIN | True | POST |  |
| /soporte/backup/<int:pk>/descargar/ | support:backup_download | apps.support.views.backup_download | SUPERADMIN | True | UNRESTRICTED |  |
| /soporte/dispositivos/ | support:printer_save | apps.support.views.printer_save | SUPERADMIN | True | UNRESTRICTED | support/settings.html |
| /soporte/dispositivos/<int:pk>/ | support:printer_edit | apps.support.views.printer_save | SUPERADMIN | True | UNRESTRICTED | support/settings.html |
| /soporte/fiscal/<int:pk>/recuperar/ | support:recover_fiscal | apps.support.views.recover_fiscal | SUPERADMIN | True | POST |  |
| /soporte/fiscal/<int:pk>/subsanar/ | support:correct_fiscal | apps.support.views.correct_fiscal | SUPERADMIN | True | POST |  |
| /soporte/fiscal/<int:pk>/anular/ | support:annul_fiscal | apps.support.views.annul_fiscal | SUPERADMIN | True | POST |  |
| /soporte/ajustes/ | support:settings | apps.support.views.technical_settings | SUPERADMIN | True | UNRESTRICTED | support/settings.html |
| /soporte/actualizaciones/ | support:updates | apps.support.views.updates | SUPERADMIN | True | UNRESTRICTED | support/updates.html |
| /usuarios/<int:pk>/desbloquear/ | team:unlock | apps.support.views.unlock_user | ADMIN | True | POST |  |
| /usuarios/ | team:index | apps.support.views.users | ADMIN | True | UNRESTRICTED | support/users.html |
| /usuarios/<int:pk>/ | team:edit | apps.support.views.user_edit | ADMIN | True | UNRESTRICTED | support/user_edit.html |
| /health/ | health | config.views.health | PUBLIC | False | GET |  |

## Modelos

| Modelo | Tabla | Campos | Restricciones |
|---|---|---|---|
| accounts.User | accounts_user | id:BigAutoField, password:CharField, last_login:DateTimeField, is_superuser:BooleanField, username:CharField, first_name:CharField, last_name:CharField, email:CharField, is_staff:BooleanField, is_active:BooleanField, date_joined:DateTimeField, role:CharField, pin_hash:CharField, auth_version:PositiveIntegerField |  |
| accounts.LoginThrottle | accounts_loginthrottle | id:BigAutoField, key:CharField, failures:PositiveIntegerField, locked_until:DateTimeField, updated_at:DateTimeField |  |
| audit.AuditEvent | audit_auditevent | id:BigAutoField, actor:ForeignKey, action:CharField, target:CharField, outcome:CharField, metadata:JSONField, created_at:DateTimeField |  |
| core.CompanySettings | core_companysettings | id:BigAutoField, name:CharField, tax_id:CharField, address:TextField, currency:CharField, timezone:CharField, fiscal_mode:CharField, software_name:CharField, software_version:CharField, producer_name:CharField, producer_tax_id:CharField, installation_number:CharField, quick_sale_enabled:BooleanField, simplified_series:CharField, full_series:CharField, rectification_series:CharField | <CheckConstraint: condition=(AND: ('pk', 1)) name='single_company_installation'> |
| core.Terminal | core_terminal | id:BigAutoField, code:SlugField, name:CharField, active:BooleanField, last_seen_at:DateTimeField, bridge_token_hash:CharField |  |
| layout.Section | layout_section | id:BigAutoField, name:CharField, sort_order:PositiveIntegerField |  |
| layout.Station | layout_station | id:BigAutoField, section:ForeignKey, code:CharField, name:CharField, active:BooleanField |  |
| catalog.Category | catalog_category | id:BigAutoField, name:CharField |  |
| catalog.CatalogItem | catalog_catalogitem | id:BigAutoField, kind:CharField, name:CharField, category:ForeignKey, price:DecimalField, tax_rate:DecimalField, active:BooleanField | <CheckConstraint: condition=(AND: ('price__gte', 0)) name='catalog_nonnegative_price'>; <CheckConstraint: condition=(AND: ('tax_rate__gte', 0), ('tax_rate__lte', 100)) name='catalog_valid_tax'> |
| customers.Customer | customers_customer | id:BigAutoField, name:CharField, phone:CharField, email:CharField, tax_id:CharField, address:TextField, legal_basis:CharField, created_at:DateTimeField |  |
| pos.OpenTicket | pos_openticket | id:BigAutoField, station:ForeignKey, terminal:ForeignKey, customer:ForeignKey, status:CharField, created_by:ForeignKey, created_at:DateTimeField, cancelled_at:DateTimeField, cancelled_by:ForeignKey, version:PositiveIntegerField | <UniqueConstraint: fields=('station',) name='one_active_ticket_per_station' condition=(AND: ('status__in', ['OPEN', 'PAYMENT_PENDING']))> |
| pos.TicketLine | pos_ticketline | id:BigAutoField, ticket:ForeignKey, item:ForeignKey, description:CharField, quantity:DecimalField, unit_price:DecimalField, tax_rate:DecimalField, discount_percent:DecimalField, note:CharField | <CheckConstraint: condition=(AND: ('discount_percent__gte', 0), ('discount_percent__lte', 100), ('quantity__gt', 0), ('tax_rate__gte', 0), ('tax_rate__lte', 100), ('unit_price__gte', 0)) name='valid_ticket_line'> |
| pos.Sale | pos_sale | id:BigAutoField, ticket:OneToOneField, total:DecimalField, created_by:ForeignKey, created_at:DateTimeField, idempotency_key:CharField, request_fingerprint:CharField |  |
| pos.Payment | pos_payment | id:BigAutoField, sale:ForeignKey, method:CharField, amount:DecimalField, received:DecimalField, reference:CharField, cash_session:ForeignKey | <CheckConstraint: condition=(AND: ('amount__gt', 0)) name='positive_payment'> |
| cash.CashRegister | cash_cashregister | id:BigAutoField, name:CharField |  |
| cash.CashSession | cash_cashsession | id:BigAutoField, register:ForeignKey, opened_by:ForeignKey, opening_balance:DecimalField, opened_at:DateTimeField, closed_at:DateTimeField, closed_by:ForeignKey, counted:DecimalField, expected:DecimalField, difference:DecimalField | <UniqueConstraint: fields=('register',) name='one_open_cash_session' condition=(AND: ('closed_at__isnull', True))>; <CheckConstraint: condition=(AND: ('opening_balance__gte', 0)) name='positive_opening_balance'> |
| cash.CashMovement | cash_cashmovement | id:BigAutoField, session:ForeignKey, kind:CharField, amount:DecimalField, reason:CharField, actor:ForeignKey, created_at:DateTimeField | <CheckConstraint: condition=(AND: ('amount__gt', 0)) name='positive_cash_movement'> |
| billing.InvoiceSequence | billing_invoicesequence | id:BigAutoField, series:CharField, year:PositiveIntegerField, next_number:PositiveIntegerField | <UniqueConstraint: fields=('series', 'year') name='invoice_sequence_unique'> |
| billing.Invoice | billing_invoice | id:BigAutoField, sale:OneToOneField, series:CharField, year:PositiveIntegerField, number:PositiveIntegerField, invoice_type:CharField, issued_at:DateTimeField, issuer:JSONField, customer:JSONField, total:DecimalField, net_total:DecimalField, tax_total:DecimalField, rectifies:ForeignKey, reason:CharField, fiscal_mode:CharField, created_by:ForeignKey | <UniqueConstraint: fields=('series', 'year', 'number') name='invoice_number_unique'> |
| billing.InvoiceLine | billing_invoiceline | id:BigAutoField, invoice:ForeignKey, description:CharField, quantity:DecimalField, unit_price:DecimalField, discount_percent:DecimalField, tax_rate:DecimalField, net_total:DecimalField, tax_total:DecimalField, total:DecimalField |  |
| billing.Refund | billing_refund | id:BigAutoField, invoice:OneToOneField, method:CharField, amount:DecimalField, cash_session:ForeignKey, reference:CharField, actor:ForeignKey |  |
| verifactu.FiscalRecord | verifactu_fiscalrecord | id:BigAutoField, invoice:ForeignKey, record_type:CharField, previous:OneToOneField, fingerprint:CharField, canonical_payload:TextField, generated_at:CharField, created_at:DateTimeField, xml:TextField |  |
| verifactu.FiscalOutbox | verifactu_fiscaloutbox | id:BigAutoField, record:OneToOneField, status:CharField, attempts:PositiveIntegerField, next_attempt_at:DateTimeField, lease_until:DateTimeField, lease_token:CharField, last_error:CharField |  |
| verifactu.FiscalTransmission | verifactu_fiscaltransmission | id:BigAutoField, outbox:ForeignKey, requested_at:DateTimeField, response:TextField, status:CharField |  |
| verifactu.FiscalEndpointState | verifactu_fiscalendpointstate | id:BigAutoField, environment:CharField, next_allowed_at:DateTimeField, lease_until:DateTimeField, lease_token:CharField |  |
| hardware.Printer | hardware_printer | id:BigAutoField, name:CharField, connection_type:CharField, address:CharField, port:PositiveIntegerField, usb_vendor:PositiveIntegerField, usb_product:PositiveIntegerField, usb_endpoint:PositiveIntegerField, encoding:CharField, codepage:PositiveSmallIntegerField, enabled:BooleanField, terminal:ForeignKey |  |
| hardware.PrintJob | hardware_printjob | id:BigAutoField, invoice:ForeignKey, printer:ForeignKey, kind:CharField, status:CharField, attempts:PositiveIntegerField, payload:BinaryField, encoding:CharField, codepage:PositiveSmallIntegerField, open_drawer:BooleanField, requested_by:ForeignKey, created_at:DateTimeField, sent_at:DateTimeField, lease_until:DateTimeField, lease_token:CharField, last_error:CharField | <UniqueConstraint: fields=('invoice',) name='one_original_print_per_invoice' condition=(AND: ('kind', 'RECEIPT'))> |
| hardware.HardwareEvent | hardware_hardwareevent | id:BigAutoField, job:ForeignKey, printer:ForeignKey, action:CharField, message:CharField, created_at:DateTimeField |  |
| support.SupportSession | support_supportsession | id:BigAutoField, actor:ForeignKey, approved_by:ForeignKey, justification:CharField, scope:CharField, created_at:DateTimeField, expires_at:DateTimeField, revoked_at:DateTimeField |  |
| support.BackupRun | support_backuprun | id:BigAutoField, filename:CharField, sha256:CharField, created_at:DateTimeField, created_by:ForeignKey, status:CharField |  |
| support.UpdateRun | support_updaterun | id:BigAutoField, version:CharField, package_sha256:CharField, status:CharField, created_at:DateTimeField, note:CharField |  |
| support.TechnicalSettings | support_technicalsettings | id:BigAutoField, backup_retention_days:PositiveIntegerField, backup_interval_hours:PositiveIntegerField, certificate_path:CharField, private_key_path:CharField, fiscal_environment:CharField, updates_channel:CharField, maintenance:BooleanField |  |
| support.ServiceHeartbeat | support_serviceheartbeat | id:BigAutoField, name:CharField, pid:PositiveIntegerField, state:CharField, last_seen:DateTimeField, last_error_code:CharField |  |

## Servicios y métodos

| Archivo | Función | Línea | Decoradores |
|---|---|---|---|
| apps/accounts/forms.py | __init__ | 9 |  |
| apps/accounts/middleware.py | __init__ | 16 |  |
| apps/accounts/middleware.py | __call__ | 19 |  |
| apps/accounts/middleware.py | __init__ | 45 |  |
| apps/accounts/middleware.py | sensitive | 49 | staticmethod |
| apps/accounts/middleware.py | __call__ | 57 |  |
| apps/accounts/models.py | create_superuser | 13 |  |
| apps/accounts/models.py | _get_session_auth_hash | 30 |  |
| apps/accounts/models.py | set_pin | 43 |  |
| apps/accounts/models.py | check_pin | 53 |  |
| apps/accounts/models.py | locked | 64 | property |
| apps/accounts/models.py | fail | 67 |  |
| apps/accounts/permissions.py | require_role | 10 |  |
| apps/accounts/permissions.py | require_elevated | 32 |  |
| apps/accounts/permissions.py | role_required | 42 |  |
| apps/accounts/permissions.py | decorate | 43 |  |
| apps/accounts/permissions.py | wrapped | 45 | wraps(view) |
| apps/accounts/services.py | _throttle_keys | 18 |  |
| apps/accounts/services.py | authenticate_local | 26 | transaction.atomic |
| apps/accounts/services.py | authorize_user_change | 63 |  |
| apps/accounts/services.py | create_user | 78 | transaction.atomic |
| apps/accounts/services.py | update_user | 97 | transaction.atomic |
| apps/accounts/services.py | elevation_expiry | 136 |  |
| apps/accounts/views.py | login_view | 15 | require_http_methods(['GET', 'POST']) |
| apps/accounts/views.py | logout_view | 48 | require_POST |
| apps/accounts/views.py | elevate_view | 56 | login_required, require_http_methods(['GET', 'POST']) |
| apps/audit/context.py | terminal_context | 8 | contextmanager |
| apps/audit/models.py | update | 7 |  |
| apps/audit/models.py | delete | 10 |  |
| apps/audit/models.py | bulk_update | 13 |  |
| apps/audit/models.py | save | 31 |  |
| apps/audit/models.py | delete | 36 |  |
| apps/audit/services.py | record | 25 |  |
| apps/audit/views.py | index | 11 | role_required('ADMIN', elevated=True) |
| apps/billing/models.py | update | 7 |  |
| apps/billing/models.py | delete | 10 |  |
| apps/billing/models.py | save | 20 |  |
| apps/billing/models.py | delete | 25 |  |
| apps/billing/models.py | full_number | 70 | property |
| apps/billing/models.py | public_number | 74 | property |
| apps/billing/models.py | __str__ | 77 |  |
| apps/billing/services.py | production_guard | 18 |  |
| apps/billing/services.py | _number | 38 |  |
| apps/billing/services.py | issue_invoice | 46 | transaction.atomic |
| apps/billing/services.py | rectify_invoice | 128 | transaction.atomic |
| apps/billing/services.py | render_pdf | 199 |  |
| apps/billing/views.py | invoice_list | 17 | login_required |
| apps/billing/views.py | _invoice | 25 |  |
| apps/billing/views.py | invoice_detail | 36 | login_required |
| apps/billing/views.py | invoice_pdf | 54 | login_required |
| apps/billing/views.py | rectify | 63 | login_required, require_POST |
| apps/billing/views.py | reprint | 88 | login_required, require_POST |
| apps/cash/models.py | __str__ | 13 |  |
| apps/cash/models.py | expected_balance | 49 | property |
| apps/cash/models.py | __str__ | 64 |  |
| apps/cash/services.py | _amount | 15 |  |
| apps/cash/services.py | open_session | 23 | atomic_retry |
| apps/cash/services.py | add_movement | 36 | atomic_retry |
| apps/cash/services.py | close_session | 62 | atomic_retry |
| apps/cash/views.py | index | 15 | role_required('EMPLOYEE') |
| apps/cash/views.py | open | 34 | require_POST, role_required('EMPLOYEE') |
| apps/cash/views.py | movement | 48 | require_POST, role_required('MANAGER') |
| apps/cash/views.py | close | 64 | require_POST, role_required('MANAGER') |
| apps/catalog/models.py | __str__ | 12 |  |
| apps/catalog/models.py | __str__ | 42 |  |
| apps/catalog/views.py | index | 15 | role_required('ADMIN') |
| apps/catalog/views.py | edit | 27 | role_required('ADMIN') |
| apps/catalog/views.py | category | 38 | role_required('ADMIN') |
| apps/catalog/views.py | delete_category | 59 | require_POST, role_required('ADMIN') |
| apps/core/guards.py | require_operational | 7 |  |
| apps/core/http.py | form_pk | 4 |  |
| apps/core/management/commands/bootstrap.py | handle | 13 | transaction.atomic |
| apps/core/models.py | clean | 49 |  |
| apps/core/models.py | save | 61 |  |
| apps/core/models.py | load | 66 | classmethod |
| apps/core/models.py | __str__ | 69 |  |
| apps/core/models.py | set_bridge_token | 80 |  |
| apps/core/models.py | check_bridge_token | 85 |  |
| apps/core/models.py | __str__ | 94 |  |
| apps/core/transactions.py | atomic_retry | 10 |  |
| apps/core/transactions.py | wrapped | 12 | wraps(function) |
| apps/core/views.py | settings | 11 | role_required('ADMIN', elevated=True) |
| apps/customers/models.py | __str__ | 18 |  |
| apps/customers/views.py | index | 19 | role_required('EMPLOYEE') |
| apps/customers/views.py | edit | 56 | role_required('EMPLOYEE') |
| apps/customers/views.py | detail | 68 | role_required('EMPLOYEE') |
| apps/customers/views.py | delete | 85 | require_POST, role_required('ADMIN', elevated=True) |
| apps/hardware/agent.py | validate_server | 21 |  |
| apps/hardware/agent.py | write_journal | 39 |  |
| apps/hardware/agent.py | run_once | 51 |  |
| apps/hardware/agent.py | main | 102 |  |
| apps/hardware/bridge.py | authenticated_terminal | 24 |  |
| apps/hardware/bridge.py | claim | 36 | csrf_exempt, require_POST |
| apps/hardware/bridge.py | acknowledge | 111 | csrf_exempt, require_POST |
| apps/hardware/drivers.py | send | 15 |  |
| apps/hardware/escpos.py | safe_text | 10 |  |
| apps/hardware/escpos.py | qr_command | 15 |  |
| apps/hardware/escpos.py | render_receipt | 31 |  |
| apps/hardware/escpos.py | render_test | 80 |  |
| apps/hardware/management/commands/hardware_bridge.py | add_arguments | 15 |  |
| apps/hardware/management/commands/hardware_bridge.py | handle | 18 |  |
| apps/hardware/management/commands/hardware_bridge.py | run_locked | 26 |  |
| apps/hardware/management/commands/hardware_bridge.py | do_POST | 34 |  |
| apps/hardware/management/commands/hardware_bridge.py | log_message | 66 |  |
| apps/hardware/management/commands/hardware_worker.py | add_arguments | 13 |  |
| apps/hardware/management/commands/hardware_worker.py | handle | 17 |  |
| apps/hardware/management/commands/hardware_worker.py | run_locked | 25 |  |
| apps/hardware/models.py | clean | 28 |  |
| apps/hardware/models.py | __str__ | 68 |  |
| apps/hardware/models.py | save | 114 |  |
| apps/hardware/services.py | enqueue_invoice | 17 | transaction.atomic |
| apps/hardware/services.py | enqueue_test | 80 | transaction.atomic |
| apps/hardware/services.py | retry_job | 102 | transaction.atomic |
| apps/hardware/services.py | recover_expired | 128 |  |
| apps/hardware/services.py | process_job | 138 |  |
| apps/hardware/views.py | reprint | 14 | require_POST, role_required('EMPLOYEE') |
| apps/hardware/views.py | test_printer | 26 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/hardware/views.py | retry | 47 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/layout/models.py | __str__ | 12 |  |
| apps/layout/models.py | __str__ | 25 |  |
| apps/layout/models.py | delete | 28 |  |
| apps/layout/views.py | index | 16 | role_required('ADMIN') |
| apps/layout/views.py | section_create | 31 | require_POST, role_required('ADMIN') |
| apps/layout/views.py | section_edit | 41 | role_required('ADMIN') |
| apps/layout/views.py | section_delete | 54 | require_POST, role_required('ADMIN') |
| apps/layout/views.py | station_edit | 66 | role_required('ADMIN') |
| apps/layout/views.py | station_delete | 84 | require_POST, role_required('ADMIN') |
| apps/pos/models.py | money | 11 |  |
| apps/pos/models.py | update | 16 |  |
| apps/pos/models.py | delete | 19 |  |
| apps/pos/models.py | save | 29 |  |
| apps/pos/models.py | delete | 34 |  |
| apps/pos/models.py | total | 79 | property |
| apps/pos/models.py | delete | 82 |  |
| apps/pos/models.py | total | 112 | property |
| apps/pos/models.py | net_total | 116 | property |
| apps/pos/models.py | tax_total | 120 | property |
| apps/pos/models.py | save | 123 |  |
| apps/pos/models.py | delete | 128 |  |
| apps/pos/models.py | customer | 143 | property |
| apps/pos/models.py | change | 165 | property |
| apps/pos/services.py | decimal_value | 21 |  |
| apps/pos/services.py | _lock_ticket | 31 |  |
| apps/pos/services.py | open_ticket | 50 | atomic_retry |
| apps/pos/services.py | _validate_terminal | 69 |  |
| apps/pos/services.py | quick_ticket | 77 | atomic_retry |
| apps/pos/services.py | prepare_payment | 98 | atomic_retry |
| apps/pos/services.py | resume_ticket | 110 | atomic_retry |
| apps/pos/services.py | add_line | 120 | atomic_retry |
| apps/pos/services.py | update_line | 160 | atomic_retry |
| apps/pos/services.py | remove_line | 187 | atomic_retry |
| apps/pos/services.py | set_customer | 196 | atomic_retry |
| apps/pos/services.py | cancel_ticket | 206 | atomic_retry |
| apps/pos/services.py | checkout | 218 | atomic_retry |
| apps/pos/views.py | _error | 20 |  |
| apps/pos/views.py | _version | 29 |  |
| apps/pos/views.py | floor | 38 | role_required('EMPLOYEE') |
| apps/pos/views.py | _terminal | 62 |  |
| apps/pos/views.py | quick_sale | 68 | require_POST, role_required('EMPLOYEE') |
| apps/pos/views.py | prepare_payment | 78 | require_POST, role_required('EMPLOYEE') |
| apps/pos/views.py | resume_ticket | 90 | require_POST, role_required('EMPLOYEE') |
| apps/pos/views.py | open_station | 102 | require_POST, role_required('EMPLOYEE') |
| apps/pos/views.py | ticket | 113 | role_required('EMPLOYEE') |
| apps/pos/views.py | add_line | 146 | require_POST, role_required('EMPLOYEE') |
| apps/pos/views.py | update_line | 165 | require_POST, role_required('EMPLOYEE') |
| apps/pos/views.py | remove_line | 183 | require_POST, role_required('MANAGER') |
| apps/pos/views.py | cancel_ticket | 194 | require_POST, role_required('MANAGER') |
| apps/pos/views.py | customer | 206 | require_POST, role_required('EMPLOYEE') |
| apps/pos/views.py | checkout | 222 | require_POST, role_required('EMPLOYEE') |
| apps/reports/views.py | _sum | 24 |  |
| apps/reports/views.py | _filters | 28 |  |
| apps/reports/views.py | _period | 40 |  |
| apps/reports/views.py | _select_operations | 52 |  |
| apps/reports/views.py | _safe_csv | 70 |  |
| apps/reports/views.py | index | 76 | role_required('MANAGER') |
| apps/support/fiscal.py | fiscal_configuration | 10 |  |
| apps/support/fiscal.py | validate_certificate_references | 21 |  |
| apps/support/forms.py | clean | 13 |  |
| apps/support/forms.py | clean | 100 |  |
| apps/support/forms.py | save | 125 |  |
| apps/support/forms.py | __init__ | 143 |  |
| apps/support/forms.py | clean_confirmation | 149 |  |
| apps/support/management/commands/operations_worker.py | add_arguments | 14 |  |
| apps/support/management/commands/operations_worker.py | handle | 18 |  |
| apps/support/management/commands/reconcile_restore.py | add_arguments | 19 |  |
| apps/support/management/commands/reconcile_restore.py | handle | 24 |  |
| apps/support/middleware.py | __init__ | 8 |  |
| apps/support/middleware.py | __call__ | 11 |  |
| apps/support/models.py | active | 21 | property |
| apps/support/models.py | __str__ | 32 |  |
| apps/support/models.py | load | 62 | classmethod |
| apps/support/operations.py | backup_key | 18 |  |
| apps/support/operations.py | backup_directory | 27 |  |
| apps/support/operations.py | hold_path | 35 |  |
| apps/support/operations.py | service_lock | 40 | contextmanager |
| apps/support/operations.py | exclusive_operation | 120 | contextmanager |
| apps/support/operations.py | create_backup | 125 |  |
| apps/support/operations.py | inspect_backup | 180 |  |
| apps/support/operations.py | restore_backup | 192 |  |
| apps/support/scheduler.py | heartbeat | 16 |  |
| apps/support/scheduler.py | run_backup_policy | 28 |  |
| apps/support/scheduler.py | run_cycle | 61 |  |
| apps/support/services.py | authorize_support | 22 |  |
| apps/support/services.py | active_authorization | 45 |  |
| apps/support/services.py | require_authorization | 62 |  |
| apps/support/services.py | diagnostics | 70 |  |
| apps/support/services.py | aeat_connectivity | 127 |  |
| apps/support/updates.py | validate_package | 33 |  |
| apps/support/updates.py | _check_locked_dependencies | 76 |  |
| apps/support/updates.py | _atomic_write | 98 |  |
| apps/support/updates.py | apply_update | 112 |  |
| apps/support/versioning.py | application_version | 8 |  |
| apps/support/views.py | index | 33 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | authorize | 58 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | revoke | 76 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | diagnostic | 86 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | export_diagnostics | 96 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | backup | 107 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | backup_download | 131 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | printer_save | 142 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | recover_fiscal | 155 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | correct_fiscal | 172 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | annul_fiscal | 187 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | technical_settings | 214 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | updates | 225 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | users | 264 | role_required('ADMIN', elevated=True) |
| apps/support/views.py | user_edit | 295 | role_required('ADMIN', elevated=True) |
| apps/support/views.py | logs | 328 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | unlock_user | 349 | require_POST, role_required('ADMIN', elevated=True) |
| apps/support/views.py | terminals | 368 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | terminal_edit | 389 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | fiscal_settings | 409 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | restore_advisor | 438 | role_required('SUPERADMIN', elevated=True) |
| apps/verifactu/management/commands/send_fiscal.py | add_arguments | 9 |  |
| apps/verifactu/management/commands/send_fiscal.py | handle | 12 |  |
| apps/verifactu/management/commands/send_fiscal.py | run_locked | 20 |  |
| apps/verifactu/protocol.py | canonical_hash | 41 |  |
| apps/verifactu/protocol.py | fiscal_date | 48 |  |
| apps/verifactu/protocol.py | qr_url | 55 |  |
| apps/verifactu/protocol.py | child | 75 |  |
| apps/verifactu/protocol.py | build_xml | 82 |  |
| apps/verifactu/protocol.py | validate_xml | 190 |  |
| apps/verifactu/protocol.py | soap_envelope | 201 |  |
| apps/verifactu/protocol.py | validate_response | 210 |  |
| apps/verifactu/protocol.py | parse_response | 241 |  |
| apps/verifactu/protocol.py | response_wait_seconds | 265 |  |
| apps/verifactu/protocol.py | verify_record_snapshot | 274 |  |
| apps/verifactu/protocol.py | resolve | 182 |  |
| apps/verifactu/protocol.py | text | 294 |  |
| apps/verifactu/services.py | create_record | 32 | transaction.atomic |
| apps/verifactu/services.py | verify_chain | 81 |  |
| apps/verifactu/services.py | correct_rejected | 101 | transaction.atomic |
| apps/verifactu/services.py | annul_record | 141 | transaction.atomic |
| apps/verifactu/services.py | send_one | 157 |  |
| scripts/audit_dependencies.py | scan | 13 |  |
| scripts/audit_inventory.py | inventory | 13 |  |
| scripts/audit_inventory.py | visit | 24 |  |
| scripts/audit_upgrade_recovery.py | run | 21 |  |
| scripts/audit_upgrade_recovery.py | inspect_database | 37 |  |
| scripts/audit_upgrade_recovery.py | execute | 49 |  |
| scripts/backup.py | main | 7 |  |
| scripts/benchmark_sqlite.py | writer | 17 |  |
| scripts/benchmark_sqlite.py | benchmark | 54 |  |
| scripts/check.py | main | 8 |  |
| scripts/install.py | main | 12 |  |
| scripts/package_release.py | build_package | 16 |  |
| scripts/restore.py | main | 6 |  |
| scripts/runtime.py | load_instance | 27 |  |
| scripts/service.py | supervise_workers | 13 |  |
| scripts/service.py | close_server | 34 |  |
| scripts/service.py | main | 46 |  |
| scripts/service.py | failed | 88 |  |
| scripts/service.py | report | 92 |  |
| scripts/update.py | main | 6 |  |

## Plantillas y conexiones

| Plantilla | Forms | URLs nombradas | Enlaces literales | HTMX |
|---|---|---|---|---|
| templates/403.html | 0 |  | /elevar/, /tpv/ |  |
| templates/404.html | 0 |  | /tpv/ |  |
| templates/500.html | 0 |  | /tpv/ |  |
| templates/accounts/elevate.html | 1 |  |  |  |
| templates/accounts/login.html | 1 |  |  |  |
| templates/audit/index.html | 1 |  |  |  |
| templates/base.html | 1 | accounts:logout | /auditoria/, /caja/, /catalogo/, /clientes/, /empresa/, /facturas/, /informes/, /plano/configuracion/, /soporte/, /tpv/, /usuarios/ |  |
| templates/billing/detail.html | 2 | billing:pdf, billing:rectify, billing:reprint | /facturas/ |  |
| templates/billing/index.html | 0 | billing:detail |  |  |
| templates/billing/list.html | 0 |  |  |  |
| templates/cash/index.html | 3 | cash:close, cash:movement, cash:open |  |  |
| templates/catalog/categories.html | 2 | catalog:category, catalog:category_delete, catalog:category_edit, catalog:index |  |  |
| templates/catalog/form.html | 1 | catalog:index |  |  |
| templates/catalog/index.html | 0 | catalog:category, catalog:create, catalog:edit |  |  |
| templates/core/form.html | 0 |  |  |  |
| templates/core/settings.html | 1 |  |  |  |
| templates/customers/detail.html | 1 | billing:detail, customers:delete, customers:edit, customers:index |  |  |
| templates/customers/form.html | 1 | customers:index |  |  |
| templates/customers/index.html | 1 | customers:create, customers:detail, customers:edit |  |  |
| templates/error.html | 0 |  | /tpv/ |  |
| templates/errors/operation.html | 0 |  | /tpv/ |  |
| templates/includes/form.html | 0 |  |  |  |
| templates/layout/form.html | 1 | layout:index |  |  |
| templates/layout/index.html | 4 | layout:section_create, layout:section_delete, layout:section_edit, layout:station_create, layout:station_delete, layout:station_edit | /tpv/ |  |
| templates/pos/floor.html | 2 | pos:floor, pos:open_station, pos:quick_sale, pos:ticket | /caja/, /plano/configuracion/ | {% url 'pos:floor' %}, {% url 'pos:floor' %} |
| templates/pos/ticket.html | 9 | pos:add_line, pos:cancel_ticket, pos:checkout, pos:customer, pos:floor, pos:prepare_payment, pos:remove_line, pos:resume_ticket, pos:update_line |  |  |
| templates/reports/index.html | 1 | billing:detail |  |  |
| templates/support/index.html | 12 | accounts:elevate, hardware:retry, hardware:test, support:annul_fiscal, support:authorize, support:backup, support:backup_download, support:correct_fiscal, support:diagnostic, support:diagnostics_export, support:fiscal_settings, support:printer_edit, support:printer_save, support:recover_fiscal, support:restore_advisor, support:revoke, support:terminals | /soporte/actualizaciones/, /soporte/ajustes/, /soporte/logs/ |  |
| templates/support/restore.html | 1 | support:index |  |  |
| templates/support/settings.html | 1 |  | /soporte/ |  |
| templates/support/terminals.html | 1 | support:index, support:terminal_edit |  |  |
| templates/support/updates.html | 1 |  | /soporte/ |  |
| templates/support/user_edit.html | 2 | team:unlock | /usuarios/ |  |
| templates/support/users.html | 1 | team:edit |  |  |
