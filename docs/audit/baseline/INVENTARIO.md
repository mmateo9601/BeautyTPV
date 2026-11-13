# Inventario de implementación

Existencia no equivale a requisito COMPLETO. Sin datos del negocio.

62 rutas; 30 modelos; 205 funciones/métodos; 32 plantillas.

## Rutas, vistas y controles declarados

| Ruta | Nombre | Vista | Rol mínimo | Elevación | Métodos | Plantillas |
|---|---|---|---|---|---|---|
| / | <unnamed> | config.urls.<lambda> | PUBLIC | False | UNRESTRICTED |  |
| /acceso/ | accounts:login | apps.accounts.views.login_view | PUBLIC | False | UNRESTRICTED | accounts/login.html |
| /salir/ | accounts:logout | apps.accounts.views.logout_view | PUBLIC | False | POST |  |
| /elevar/ | accounts:elevate | apps.accounts.views.elevate_view | AUTHENTICATED | False | UNRESTRICTED | accounts/elevate.html |
| /auditoria/ | audit:index | apps.audit.views.index | ADMIN | True | UNRESTRICTED | audit/index.html |
| /tpv/ | pos:floor | apps.pos.views.floor | EMPLOYEE | False | UNRESTRICTED | pos/floor.html |
| /tpv/puestos/<int:pk>/ | pos:open_station | apps.pos.views.open_station | EMPLOYEE | False | POST |  |
| /tpv/cuentas/<int:pk>/ | pos:ticket | apps.pos.views.ticket | EMPLOYEE | False | UNRESTRICTED | pos/ticket.html |
| /tpv/cuentas/<int:pk>/lineas/ | pos:add_line | apps.pos.views.add_line | EMPLOYEE | False | POST |  |
| /tpv/lineas/<int:pk>/ | pos:update_line | apps.pos.views.update_line | EMPLOYEE | False | POST |  |
| /tpv/lineas/<int:pk>/eliminar/ | pos:remove_line | apps.pos.views.remove_line | MANAGER | False | POST |  |
| /tpv/cuentas/<int:pk>/anular/ | pos:cancel_ticket | apps.pos.views.cancel_ticket | MANAGER | False | POST |  |
| /tpv/cuentas/<int:pk>/cliente/ | pos:customer | apps.pos.views.customer | EMPLOYEE | False | POST |  |
| /tpv/cuentas/<int:pk>/cobrar/ | pos:checkout | apps.pos.views.checkout | EMPLOYEE | False | POST |  |
| /plano/configuracion/ | layout:index | apps.layout.views.index | ADMIN | False | UNRESTRICTED | layout/index.html |
| /plano/configuracion/secciones/ | layout:section_create | apps.layout.views.section_create | ADMIN | False | POST |  |
| /plano/configuracion/puestos/nuevo/ | layout:station_create | apps.layout.views.station_edit | ADMIN | False | UNRESTRICTED | layout/form.html |
| /plano/configuracion/puestos/<int:pk>/editar/ | layout:station_edit | apps.layout.views.station_edit | ADMIN | False | UNRESTRICTED | layout/form.html |
| /plano/configuracion/puestos/<int:pk>/eliminar/ | layout:station_delete | apps.layout.views.station_delete | ADMIN | False | POST |  |
| /catalogo/ | catalog:index | apps.catalog.views.index | ADMIN | False | UNRESTRICTED | catalog/index.html |
| /catalogo/nuevo/ | catalog:create | apps.catalog.views.edit | ADMIN | False | UNRESTRICTED | catalog/form.html |
| /catalogo/<int:pk>/editar/ | catalog:edit | apps.catalog.views.edit | ADMIN | False | UNRESTRICTED | catalog/form.html |
| /catalogo/categorias/ | catalog:category | apps.catalog.views.category | ADMIN | False | UNRESTRICTED | catalog/categories.html |
| /catalogo/categorias/<int:pk>/ | catalog:category_edit | apps.catalog.views.category | ADMIN | False | UNRESTRICTED | catalog/categories.html |
| /catalogo/categorias/<int:pk>/eliminar/ | catalog:category_delete | apps.catalog.views.delete_category | ADMIN | False | POST |  |
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
| /hardware/facturas/<int:pk>/copia/ | hardware:reprint | apps.hardware.views.reprint | EMPLOYEE | False | POST |  |
| /hardware/impresoras/<int:pk>/prueba/ | hardware:test | apps.hardware.views.test_printer | SUPERADMIN | True | POST |  |
| /hardware/trabajos/<int:pk>/reintentar/ | hardware:retry | apps.hardware.views.retry | SUPERADMIN | True | POST |  |
| /empresa/ | core:settings | apps.core.views.settings | ADMIN | True | UNRESTRICTED | core/settings.html |
| /informes/ | reports:index | apps.reports.views.index | MANAGER | False | UNRESTRICTED | reports/index.html |
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
| /soporte/ajustes/ | support:settings | apps.support.views.technical_settings | SUPERADMIN | True | UNRESTRICTED | support/settings.html |
| /soporte/actualizaciones/ | support:updates | apps.support.views.updates | SUPERADMIN | True | UNRESTRICTED | support/updates.html |
| /usuarios/ | team:index | apps.support.views.users | ADMIN | True | UNRESTRICTED | support/users.html |
| /usuarios/<int:pk>/ | team:edit | apps.support.views.user_edit | ADMIN | True | UNRESTRICTED | support/user_edit.html |
| /health/ | <unnamed> | config.urls.<lambda> | PUBLIC | False | UNRESTRICTED |  |

## Modelos

| Modelo | Tabla | Campos | Restricciones |
|---|---|---|---|
| accounts.User | accounts_user | id:BigAutoField, password:CharField, last_login:DateTimeField, is_superuser:BooleanField, username:CharField, first_name:CharField, last_name:CharField, email:CharField, is_staff:BooleanField, is_active:BooleanField, date_joined:DateTimeField, role:CharField, pin_hash:CharField |  |
| accounts.LoginThrottle | accounts_loginthrottle | id:BigAutoField, key:CharField, failures:PositiveIntegerField, locked_until:DateTimeField, updated_at:DateTimeField |  |
| audit.AuditEvent | audit_auditevent | id:BigAutoField, actor:ForeignKey, action:CharField, target:CharField, outcome:CharField, metadata:JSONField, created_at:DateTimeField |  |
| core.CompanySettings | core_companysettings | id:BigAutoField, name:CharField, tax_id:CharField, address:TextField, currency:CharField, timezone:CharField, fiscal_mode:CharField, software_name:CharField, software_version:CharField, producer_name:CharField, producer_tax_id:CharField, installation_number:CharField |  |
| layout.Section | layout_section | id:BigAutoField, name:CharField, sort_order:PositiveIntegerField |  |
| layout.Station | layout_station | id:BigAutoField, section:ForeignKey, code:CharField, name:CharField, active:BooleanField |  |
| catalog.Category | catalog_category | id:BigAutoField, name:CharField |  |
| catalog.CatalogItem | catalog_catalogitem | id:BigAutoField, kind:CharField, name:CharField, category:ForeignKey, price:DecimalField, tax_rate:DecimalField, active:BooleanField | <CheckConstraint: condition=(AND: ('price__gte', 0)) name='catalog_nonnegative_price'>; <CheckConstraint: condition=(AND: ('tax_rate__gte', 0), ('tax_rate__lte', 100)) name='catalog_valid_tax'> |
| customers.Customer | customers_customer | id:BigAutoField, name:CharField, phone:CharField, email:CharField, tax_id:CharField, address:TextField, legal_basis:CharField, created_at:DateTimeField |  |
| pos.OpenTicket | pos_openticket | id:BigAutoField, station:ForeignKey, customer:ForeignKey, status:CharField, created_by:ForeignKey, created_at:DateTimeField, version:PositiveIntegerField | <UniqueConstraint: fields=('station',) name='one_active_ticket_per_station' condition=(AND: ('status__in', ['OPEN', 'PAYMENT_PENDING']))> |
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
| verifactu.FiscalOutbox | verifactu_fiscaloutbox | id:BigAutoField, record:OneToOneField, status:CharField, attempts:PositiveIntegerField, next_attempt_at:DateTimeField, lease_until:DateTimeField, last_error:CharField |  |
| verifactu.FiscalTransmission | verifactu_fiscaltransmission | id:BigAutoField, outbox:ForeignKey, requested_at:DateTimeField, response:TextField, status:CharField |  |
| hardware.Printer | hardware_printer | id:BigAutoField, name:CharField, connection_type:CharField, address:CharField, port:PositiveIntegerField, usb_vendor:PositiveIntegerField, usb_product:PositiveIntegerField, usb_endpoint:PositiveIntegerField, encoding:CharField, codepage:PositiveSmallIntegerField, enabled:BooleanField |  |
| hardware.PrintJob | hardware_printjob | id:BigAutoField, invoice:ForeignKey, printer:ForeignKey, kind:CharField, status:CharField, attempts:PositiveIntegerField, payload:BinaryField, open_drawer:BooleanField, requested_by:ForeignKey, created_at:DateTimeField, sent_at:DateTimeField, lease_until:DateTimeField, last_error:CharField | <UniqueConstraint: fields=('invoice',) name='one_original_print_per_invoice' condition=(AND: ('kind', 'RECEIPT'))> |
| hardware.HardwareEvent | hardware_hardwareevent | id:BigAutoField, job:ForeignKey, printer:ForeignKey, action:CharField, message:CharField, created_at:DateTimeField |  |
| support.SupportSession | support_supportsession | id:BigAutoField, actor:ForeignKey, approved_by:ForeignKey, justification:CharField, scope:CharField, created_at:DateTimeField, expires_at:DateTimeField, revoked_at:DateTimeField |  |
| support.BackupRun | support_backuprun | id:BigAutoField, filename:CharField, sha256:CharField, created_at:DateTimeField, created_by:ForeignKey, status:CharField |  |
| support.UpdateRun | support_updaterun | id:BigAutoField, version:CharField, package_sha256:CharField, status:CharField, created_at:DateTimeField, note:CharField |  |
| support.TechnicalSettings | support_technicalsettings | id:BigAutoField, backup_retention_days:PositiveIntegerField, backup_interval_hours:PositiveIntegerField, updates_channel:CharField, maintenance:BooleanField |  |

## Servicios y métodos

| Archivo | Función | Línea | Decoradores |
|---|---|---|---|
| apps/accounts/middleware.py | __init__ | 13 |  |
| apps/accounts/middleware.py | sensitive | 17 | staticmethod |
| apps/accounts/middleware.py | __call__ | 25 |  |
| apps/accounts/models.py | create_superuser | 11 |  |
| apps/accounts/models.py | set_pin | 27 |  |
| apps/accounts/models.py | check_pin | 37 |  |
| apps/accounts/models.py | locked | 48 | property |
| apps/accounts/models.py | fail | 51 |  |
| apps/accounts/permissions.py | require_role | 9 |  |
| apps/accounts/permissions.py | require_elevated | 17 |  |
| apps/accounts/permissions.py | role_required | 23 |  |
| apps/accounts/permissions.py | decorate | 24 |  |
| apps/accounts/permissions.py | wrapped | 26 | wraps(view) |
| apps/accounts/services.py | _throttle_keys | 16 |  |
| apps/accounts/services.py | authenticate_local | 24 | transaction.atomic |
| apps/accounts/services.py | authorize_user_change | 54 |  |
| apps/accounts/services.py | create_user | 67 | transaction.atomic |
| apps/accounts/services.py | update_user | 86 | transaction.atomic |
| apps/accounts/services.py | elevation_expiry | 112 |  |
| apps/accounts/views.py | login_view | 14 | require_http_methods(['GET', 'POST']) |
| apps/accounts/views.py | logout_view | 42 | require_POST |
| apps/accounts/views.py | elevate_view | 50 | login_required, require_http_methods(['GET', 'POST']) |
| apps/audit/models.py | update | 7 |  |
| apps/audit/models.py | delete | 10 |  |
| apps/audit/models.py | bulk_update | 13 |  |
| apps/audit/models.py | save | 31 |  |
| apps/audit/models.py | delete | 36 |  |
| apps/audit/services.py | record | 24 |  |
| apps/audit/views.py | index | 10 | role_required('ADMIN', elevated=True) |
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
| apps/billing/services.py | rectify_invoice | 120 | transaction.atomic |
| apps/billing/services.py | render_pdf | 188 |  |
| apps/billing/views.py | invoice_list | 17 | login_required |
| apps/billing/views.py | _invoice | 25 |  |
| apps/billing/views.py | invoice_detail | 36 | login_required |
| apps/billing/views.py | invoice_pdf | 54 | login_required |
| apps/billing/views.py | rectify | 63 | login_required, require_POST |
| apps/billing/views.py | reprint | 87 | login_required, require_POST |
| apps/cash/models.py | __str__ | 13 |  |
| apps/cash/models.py | expected_balance | 49 | property |
| apps/cash/models.py | __str__ | 64 |  |
| apps/cash/services.py | _amount | 12 |  |
| apps/cash/services.py | open_session | 20 | transaction.atomic |
| apps/cash/services.py | add_movement | 32 | transaction.atomic |
| apps/cash/services.py | close_session | 48 | transaction.atomic |
| apps/cash/views.py | index | 13 | role_required('EMPLOYEE') |
| apps/cash/views.py | open | 27 | require_POST, role_required('EMPLOYEE') |
| apps/cash/views.py | movement | 41 | require_POST, role_required('MANAGER') |
| apps/cash/views.py | close | 57 | require_POST, role_required('MANAGER') |
| apps/catalog/models.py | __str__ | 12 |  |
| apps/catalog/models.py | __str__ | 42 |  |
| apps/catalog/views.py | index | 15 | role_required('ADMIN') |
| apps/catalog/views.py | edit | 27 | role_required('ADMIN') |
| apps/catalog/views.py | category | 38 | role_required('ADMIN') |
| apps/catalog/views.py | delete_category | 59 | require_POST, role_required('ADMIN') |
| apps/core/guards.py | require_operational | 7 |  |
| apps/core/management/commands/bootstrap.py | handle | 13 | transaction.atomic |
| apps/core/models.py | save | 19 |  |
| apps/core/models.py | load | 24 | classmethod |
| apps/core/models.py | __str__ | 27 |  |
| apps/core/views.py | settings | 11 | role_required('ADMIN', elevated=True) |
| apps/customers/models.py | __str__ | 18 |  |
| apps/customers/views.py | index | 19 | role_required('EMPLOYEE') |
| apps/customers/views.py | edit | 56 | role_required('EMPLOYEE') |
| apps/customers/views.py | detail | 68 | role_required('EMPLOYEE') |
| apps/customers/views.py | delete | 85 | require_POST, role_required('ADMIN', elevated=True) |
| apps/hardware/drivers.py | send | 15 |  |
| apps/hardware/escpos.py | safe_text | 10 |  |
| apps/hardware/escpos.py | qr_command | 15 |  |
| apps/hardware/escpos.py | render_receipt | 31 |  |
| apps/hardware/escpos.py | render_test | 72 |  |
| apps/hardware/management/commands/hardware_bridge.py | add_arguments | 15 |  |
| apps/hardware/management/commands/hardware_bridge.py | handle | 18 |  |
| apps/hardware/management/commands/hardware_bridge.py | run_locked | 26 |  |
| apps/hardware/management/commands/hardware_bridge.py | do_POST | 34 |  |
| apps/hardware/management/commands/hardware_bridge.py | log_message | 56 |  |
| apps/hardware/management/commands/hardware_worker.py | add_arguments | 12 |  |
| apps/hardware/management/commands/hardware_worker.py | handle | 16 |  |
| apps/hardware/management/commands/hardware_worker.py | run_locked | 24 |  |
| apps/hardware/models.py | __str__ | 25 |  |
| apps/hardware/models.py | save | 68 |  |
| apps/hardware/services.py | enqueue_invoice | 17 | transaction.atomic |
| apps/hardware/services.py | enqueue_test | 58 | transaction.atomic |
| apps/hardware/services.py | retry_job | 77 | transaction.atomic |
| apps/hardware/services.py | recover_expired | 95 |  |
| apps/hardware/services.py | process_job | 102 |  |
| apps/hardware/views.py | reprint | 14 | require_POST, role_required('EMPLOYEE') |
| apps/hardware/views.py | test_printer | 26 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/hardware/views.py | retry | 36 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/layout/models.py | __str__ | 12 |  |
| apps/layout/models.py | __str__ | 25 |  |
| apps/layout/models.py | delete | 28 |  |
| apps/layout/views.py | index | 15 | role_required('ADMIN') |
| apps/layout/views.py | section_create | 30 | require_POST, role_required('ADMIN') |
| apps/layout/views.py | station_edit | 40 | role_required('ADMIN') |
| apps/layout/views.py | station_delete | 58 | require_POST, role_required('ADMIN') |
| apps/pos/models.py | money | 11 |  |
| apps/pos/models.py | update | 16 |  |
| apps/pos/models.py | delete | 19 |  |
| apps/pos/models.py | save | 29 |  |
| apps/pos/models.py | delete | 34 |  |
| apps/pos/models.py | total | 70 | property |
| apps/pos/models.py | delete | 73 |  |
| apps/pos/models.py | total | 103 | property |
| apps/pos/models.py | net_total | 107 | property |
| apps/pos/models.py | tax_total | 111 | property |
| apps/pos/models.py | save | 114 |  |
| apps/pos/models.py | delete | 119 |  |
| apps/pos/models.py | customer | 134 | property |
| apps/pos/models.py | change | 156 | property |
| apps/pos/services.py | decimal_value | 19 |  |
| apps/pos/services.py | _lock_ticket | 29 |  |
| apps/pos/services.py | open_ticket | 43 | transaction.atomic |
| apps/pos/services.py | add_line | 58 | transaction.atomic |
| apps/pos/services.py | update_line | 87 | transaction.atomic |
| apps/pos/services.py | remove_line | 109 | transaction.atomic |
| apps/pos/services.py | set_customer | 117 | transaction.atomic |
| apps/pos/services.py | cancel_ticket | 126 | transaction.atomic |
| apps/pos/services.py | checkout | 135 | transaction.atomic |
| apps/pos/views.py | _error | 18 |  |
| apps/pos/views.py | _version | 27 |  |
| apps/pos/views.py | floor | 36 | role_required('EMPLOYEE') |
| apps/pos/views.py | open_station | 49 | require_POST, role_required('EMPLOYEE') |
| apps/pos/views.py | ticket | 58 | role_required('EMPLOYEE') |
| apps/pos/views.py | add_line | 85 | require_POST, role_required('EMPLOYEE') |
| apps/pos/views.py | update_line | 103 | require_POST, role_required('EMPLOYEE') |
| apps/pos/views.py | remove_line | 120 | require_POST, role_required('MANAGER') |
| apps/pos/views.py | cancel_ticket | 131 | require_POST, role_required('MANAGER') |
| apps/pos/views.py | customer | 143 | require_POST, role_required('EMPLOYEE') |
| apps/pos/views.py | checkout | 159 | require_POST, role_required('EMPLOYEE') |
| apps/reports/views.py | index | 17 | role_required('MANAGER') |
| apps/support/management/commands/operations_worker.py | add_arguments | 18 |  |
| apps/support/management/commands/operations_worker.py | handle | 22 |  |
| apps/support/management/commands/operations_worker.py | run_locked | 30 |  |
| apps/support/management/commands/reconcile_restore.py | add_arguments | 19 |  |
| apps/support/management/commands/reconcile_restore.py | handle | 24 |  |
| apps/support/middleware.py | __init__ | 8 |  |
| apps/support/middleware.py | __call__ | 11 |  |
| apps/support/models.py | active | 20 | property |
| apps/support/models.py | load | 47 | classmethod |
| apps/support/operations.py | backup_key | 16 |  |
| apps/support/operations.py | backup_directory | 25 |  |
| apps/support/operations.py | hold_path | 33 |  |
| apps/support/operations.py | service_lock | 38 | contextmanager |
| apps/support/operations.py | exclusive_operation | 118 | contextmanager |
| apps/support/operations.py | create_backup | 123 |  |
| apps/support/operations.py | inspect_backup | 178 |  |
| apps/support/operations.py | restore_backup | 190 |  |
| apps/support/services.py | authorize_support | 22 |  |
| apps/support/services.py | active_authorization | 45 |  |
| apps/support/services.py | require_authorization | 55 |  |
| apps/support/services.py | diagnostics | 63 |  |
| apps/support/services.py | aeat_connectivity | 103 |  |
| apps/support/updates.py | validate_package | 29 |  |
| apps/support/updates.py | apply_update | 71 |  |
| apps/support/views.py | index | 32 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | authorize | 57 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | revoke | 75 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | diagnostic | 85 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | export_diagnostics | 95 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | backup | 106 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | backup_download | 129 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | printer_save | 140 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | recover_fiscal | 153 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | correct_fiscal | 170 | require_POST, role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | technical_settings | 184 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | updates | 195 | role_required('SUPERADMIN', elevated=True) |
| apps/support/views.py | users | 207 | role_required('ADMIN', elevated=True) |
| apps/support/views.py | user_edit | 238 | role_required('ADMIN', elevated=True) |
| apps/support/views.py | logs | 271 | role_required('SUPERADMIN', elevated=True) |
| apps/verifactu/management/commands/send_fiscal.py | add_arguments | 9 |  |
| apps/verifactu/management/commands/send_fiscal.py | handle | 12 |  |
| apps/verifactu/management/commands/send_fiscal.py | run_locked | 20 |  |
| apps/verifactu/protocol.py | canonical_hash | 40 |  |
| apps/verifactu/protocol.py | fiscal_date | 47 |  |
| apps/verifactu/protocol.py | qr_url | 54 |  |
| apps/verifactu/protocol.py | child | 74 |  |
| apps/verifactu/protocol.py | build_xml | 81 |  |
| apps/verifactu/protocol.py | validate_xml | 170 |  |
| apps/verifactu/protocol.py | soap_envelope | 181 |  |
| apps/verifactu/protocol.py | validate_response | 190 |  |
| apps/verifactu/protocol.py | parse_response | 216 |  |
| apps/verifactu/protocol.py | resolve | 162 |  |
| apps/verifactu/services.py | create_record | 29 | transaction.atomic |
| apps/verifactu/services.py | verify_chain | 64 |  |
| apps/verifactu/services.py | correct_rejected | 84 | transaction.atomic |
| apps/verifactu/services.py | annul_record | 103 | transaction.atomic |
| apps/verifactu/services.py | send_one | 119 |  |
| scripts/backup.py | main | 7 |  |
| scripts/check.py | main | 8 |  |
| scripts/install.py | main | 12 |  |
| scripts/package_release.py | build_package | 16 |  |
| scripts/restore.py | main | 6 |  |
| scripts/runtime.py | load_instance | 27 |  |
| scripts/service.py | main | 9 |  |
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
| templates/layout/index.html | 3 | layout:section_create, layout:station_create, layout:station_delete, layout:station_edit | /tpv/ |  |
| templates/pos/floor.html | 1 | pos:floor, pos:open_station | /caja/, /plano/configuracion/ | {% url 'pos:floor' %} |
| templates/pos/ticket.html | 6 | pos:add_line, pos:cancel_ticket, pos:checkout, pos:customer, pos:floor, pos:remove_line, pos:update_line |  |  |
| templates/reports/index.html | 1 | billing:detail |  |  |
| templates/support/index.html | 11 | accounts:elevate, hardware:retry, hardware:test, support:authorize, support:backup, support:backup_download, support:correct_fiscal, support:diagnostic, support:diagnostics_export, support:printer_edit, support:printer_save, support:recover_fiscal, support:revoke | /soporte/actualizaciones/, /soporte/ajustes/, /soporte/logs/ |  |
| templates/support/settings.html | 1 |  | /soporte/ |  |
| templates/support/updates.html | 0 |  | /soporte/ |  |
| templates/support/user_edit.html | 1 |  | /usuarios/ |  |
| templates/support/users.html | 1 | team:edit |  |  |
