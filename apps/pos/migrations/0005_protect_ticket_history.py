from django.db import migrations


def protect(apps, schema_editor):
    if schema_editor.connection.vendor != "sqlite":
        return
    schema_editor.execute("DROP TRIGGER IF EXISTS sealed_sale_payments")
    schema_editor.execute(
        "CREATE TRIGGER sealed_sale_payments BEFORE INSERT ON pos_payment WHEN "
        "EXISTS (SELECT 1 FROM pos_sale s JOIN pos_openticket t ON t.id=s.ticket_id "
        "WHERE s.id=NEW.sale_id AND t.status NOT IN ('OPEN','PAYMENT_PENDING')) "
        "OR EXISTS (SELECT 1 FROM billing_invoice WHERE sale_id=NEW.sale_id) "
        "BEGIN SELECT RAISE(ABORT, 'Closed sale payments sealed'); END"
    )
    for operation in ("UPDATE", "DELETE"):
        schema_editor.execute(
            f"CREATE TRIGGER ticket_history_{operation.lower()} BEFORE {operation} ON pos_openticket "
            "WHEN OLD.status IN ('CLOSED','CANCELLED') "
            "BEGIN SELECT RAISE(ABORT, 'Ticket history immutable'); END"
        )
    guards = {
        "pos_sale": "id=NEW.id OR ticket_id=NEW.ticket_id OR idempotency_key=NEW.idempotency_key",
        "pos_payment": "id=NEW.id",
        "pos_openticket": "id=NEW.id AND status IN ('CLOSED','CANCELLED')",
        "pos_ticketline": "id=NEW.id AND ticket_id IN (SELECT id FROM pos_openticket WHERE status != 'OPEN')",
    }
    for table, condition in guards.items():
        schema_editor.execute(
            f"CREATE TRIGGER no_replace_{table} BEFORE INSERT ON {table} "
            f"WHEN EXISTS (SELECT 1 FROM {table} WHERE {condition}) "
            "BEGIN SELECT RAISE(ABORT, 'Immutable history replacement prohibited'); END"
        )


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        for name in (
            "ticket_history_update",
            "ticket_history_delete",
            "no_replace_pos_sale",
            "no_replace_pos_payment",
            "no_replace_pos_openticket",
            "no_replace_pos_ticketline",
        ):
            schema_editor.execute(f"DROP TRIGGER IF EXISTS {name}")
        schema_editor.execute("DROP TRIGGER IF EXISTS sealed_sale_payments")
        from importlib import import_module

        import_module("apps.pos.migrations.0003_seal_sale_payments").protect(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [("pos", "0004_openticket_terminal"), ("billing", "0001_initial")]
    operations = [migrations.RunPython(protect, unprotect)]
