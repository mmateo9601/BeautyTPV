from django.db import migrations

GUARDS = {
    "billing_invoice": "EXISTS (SELECT 1 FROM billing_invoice WHERE id=NEW.id OR (series=NEW.series AND year=NEW.year AND number=NEW.number) OR (NEW.sale_id IS NOT NULL AND sale_id=NEW.sale_id))",
    "billing_invoiceline": "EXISTS (SELECT 1 FROM billing_invoiceline WHERE id=NEW.id)",
    "billing_refund": "EXISTS (SELECT 1 FROM billing_refund WHERE id=NEW.id OR invoice_id=NEW.invoice_id)",
}


def protect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        for table, condition in GUARDS.items():
            schema_editor.execute(
                f"CREATE TRIGGER no_replace_{table} BEFORE INSERT ON {table} WHEN {condition} BEGIN SELECT RAISE(ABORT, 'Issued record cannot be replaced'); END"
            )


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        for table in GUARDS:
            schema_editor.execute(f"DROP TRIGGER IF EXISTS no_replace_{table}")


class Migration(migrations.Migration):
    dependencies = [("billing", "0003_seal_invoice_lines")]
    operations = [migrations.RunPython(protect, unprotect)]
