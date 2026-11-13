import argparse

from runtime import load_instance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args()
    load_instance(args.instance)
    import django

    django.setup()
    from django.conf import settings
    from django.db import connections

    from apps.support.operations import backup_key, restore_backup

    database = settings.DATABASES["default"]["NAME"]
    connections.close_all()
    restore_backup(
        args.archive, database, backup_key(), confirmation=args.confirm, offline=args.offline
    )
    print(
        "Restauración íntegra. Remisión y operativa RETENIDAS: conciliar AEAT y ejecutar reconcile_restore."
    )


if __name__ == "__main__":
    main()
