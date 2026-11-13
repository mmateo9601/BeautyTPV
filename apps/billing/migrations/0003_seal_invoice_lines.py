from django.db import migrations


def protect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute(
            "CREATE TRIGGER sealed_invoice_lines BEFORE INSERT ON billing_invoiceline "
            "WHEN EXISTS (SELECT 1 FROM verifactu_fiscalrecord WHERE invoice_id=NEW.invoice_id) "
            "BEGIN SELECT RAISE(ABORT, 'Issued invoice lines sealed'); END"
        )


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute("DROP TRIGGER IF EXISTS sealed_invoice_lines")


class Migration(migrations.Migration):
    dependencies = [("billing", "0002_immutable_triggers"), ("verifactu", "0001_initial")]
    operations = [migrations.RunPython(protect, unprotect)]
