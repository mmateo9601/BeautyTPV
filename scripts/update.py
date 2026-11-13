import argparse

from runtime import ROOT, load_instance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    load_instance(args.instance)
    import django

    django.setup()
    from django.conf import settings
    from django.db import connections

    from apps.support.models import UpdateRun
    from apps.support.operations import backup_key
    from apps.support.updates import apply_update

    connections.close_all()
    try:
        manifest = apply_update(
            args.package,
            args.sha256,
            ROOT,
            settings.DATABASES["default"]["NAME"],
            backup_key(),
            offline=args.offline,
        )
        UpdateRun.objects.create(
            version=manifest["version"], package_sha256=args.sha256, status="SUCCESS"
        )
    except Exception as error:
        UpdateRun.objects.create(
            version="unknown",
            package_sha256=args.sha256[:64],
            status="FAILED",
            note=type(error).__name__ + ": revisar evidencia offline",
        )
        raise
    print("Actualización aplicada; base fiscal preservada. Verifique flujos antes de reabrir.")


if __name__ == "__main__":
    main()
