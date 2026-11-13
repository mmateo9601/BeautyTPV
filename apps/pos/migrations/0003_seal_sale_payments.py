from django.db import migrations


def protect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute(
            "CREATE TRIGGER sealed_sale_payments BEFORE INSERT ON pos_payment "
            "WHEN EXISTS (SELECT 1 FROM pos_sale s JOIN pos_openticket t ON t.id=s.ticket_id "
            "WHERE s.id=NEW.sale_id AND t.status != 'OPEN') "
            "BEGIN SELECT RAISE(ABORT, 'Closed sale payments sealed'); END"
        )


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        schema_editor.execute("DROP TRIGGER IF EXISTS sealed_sale_payments")


class Migration(migrations.Migration):
    dependencies = [("pos", "0002_issued_guards")]
    operations = [migrations.RunPython(protect, unprotect)]
