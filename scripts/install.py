import argparse
import json
import os
import secrets
import subprocess
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="Instalación local independiente BeautyTPV")
    parser.add_argument("--instance-dir", required=True)
    parser.add_argument(
        "--skip-dependencies",
        action="store_true",
        help="Solo verificación de instalación con entorno ya preparado",
    )
    parser.add_argument(
        "--no-user", action="store_true", help="Posponer creación interactiva del Superadmin"
    )
    args = parser.parse_args()
    directory = Path(args.instance_dir).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    configuration = directory / "instance.json"
    if configuration.exists():
        raise SystemExit("Instancia ya configurada. No se sobreescriben secretos ni BD.")
    environment = ROOT / ".venv"
    if not environment.exists():
        venv.EnvBuilder(with_pip=True).create(environment)
    executable = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not args.skip_dependencies:
        subprocess.run(
            [str(executable), "-m", "pip", "install", "-r", str(ROOT / "requirements.lock.txt")],
            check=True,
        )
        subprocess.run(
            [str(executable), "-m", "pip", "install", "--no-deps", "-e", str(ROOT) + "[dev]"],
            check=True,
        )
    import base64

    values = {
        "BEAUTYTPV_SECRET_KEY": secrets.token_urlsafe(64),
        "BEAUTYTPV_DEBUG": "0",
        "BEAUTYTPV_ALLOWED_HOSTS": "localhost,127.0.0.1",
        "BEAUTYTPV_DB": str(directory / "db.sqlite3"),
        "BEAUTYTPV_BACKUP_KEY": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
        "BEAUTYTPV_BACKUP_DIR": str(directory / "backups"),
        "BEAUTYTPV_FISCAL_ENVIRONMENT": "TEST",
        "BEAUTYTPV_BRIDGE_TOKEN": secrets.token_urlsafe(48),
    }
    with configuration.open("x", encoding="utf-8") as stream:
        json.dump(values, stream, indent=2)
    if os.name == "nt":
        import getpass

        subprocess.run(
            ["icacls", str(configuration), "/inheritance:r", "/grant:r", getpass.getuser() + ":F"],
            check=True,
            capture_output=True,
        )
    else:
        configuration.chmod(0o600)
    os.environ.update(values)
    for arguments in [
        ["migrate", "--noinput"],
        ["bootstrap"],
        ["check"],
        ["collectstatic", "--noinput"],
    ]:
        subprocess.run([str(executable), str(ROOT / "manage.py"), *arguments], cwd=ROOT, check=True)
    if not args.no_user:
        subprocess.run(
            [str(executable), str(ROOT / "manage.py"), "createsuperuser"], cwd=ROOT, check=True
        )
    print("Instalación creada sin credenciales predeterminadas.")
    print("Configuración externa:", configuration)
    print("Configure HTTPS local y copias externas; facturación TEST hasta validación fiscal.")


if __name__ == "__main__":
    main()
