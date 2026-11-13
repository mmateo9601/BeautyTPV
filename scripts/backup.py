import argparse
from pathlib import Path

from runtime import load_instance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    load_instance(args.instance)
    import django

    django.setup()
    from django.conf import settings

    from apps.support.operations import backup_key, create_backup

    manifest, digest = create_backup(
        settings.DATABASES["default"]["NAME"], args.output, backup_key()
    )
    print("Copia cifrada verificada:", Path(args.output).name, "SHA256", digest)


if __name__ == "__main__":
    main()
