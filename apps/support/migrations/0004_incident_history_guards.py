from django.db import migrations


def protect(apps, schema_editor):
    if schema_editor.connection.vendor != "sqlite":
        return
    statements = [
        "CREATE TRIGGER incident_action_no_update BEFORE UPDATE ON support_incidentaction BEGIN SELECT RAISE(ABORT, 'Immutable incident action'); END",
        "CREATE TRIGGER incident_action_no_delete BEFORE DELETE ON support_incidentaction BEGIN SELECT RAISE(ABORT, 'Immutable incident action'); END",
        "CREATE TRIGGER incident_action_no_replace BEFORE INSERT ON support_incidentaction WHEN EXISTS(SELECT 1 FROM support_incidentaction WHERE id=NEW.id) BEGIN SELECT RAISE(ABORT, 'Immutable incident action'); END",
        "CREATE TRIGGER incident_no_delete BEFORE DELETE ON support_incident BEGIN SELECT RAISE(ABORT, 'Retained incident'); END",
        "CREATE TRIGGER incident_no_replace BEFORE INSERT ON support_incident WHEN EXISTS(SELECT 1 FROM support_incident WHERE id=NEW.id) BEGIN SELECT RAISE(ABORT, 'Retained incident'); END",
        "CREATE TRIGGER incident_identity BEFORE UPDATE ON support_incident WHEN NEW.title IS NOT OLD.title OR NEW.description IS NOT OLD.description OR NEW.created_by_id IS NOT OLD.created_by_id OR NEW.created_at IS NOT OLD.created_at BEGIN SELECT RAISE(ABORT, 'Retained incident identity'); END",
    ]
    with schema_editor.connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor != "sqlite":
        return
    for name in (
        "incident_action_no_update",
        "incident_action_no_delete",
        "incident_action_no_replace",
        "incident_no_delete",
        "incident_no_replace",
        "incident_identity",
    ):
        schema_editor.execute(f"DROP TRIGGER IF EXISTS {name}")


class Migration(migrations.Migration):
    dependencies = [("support", "0003_incident_incidentaction")]
    operations = [migrations.RunPython(protect, unprotect)]
