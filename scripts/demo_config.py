"""Fixed, private DEMO paths. No production instance configuration is consumed."""

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIND = "BeautyTPV-DEMO"


def demo_directory(value=None):
    value = value or os.environ.get("BEAUTYTPV_DEMO_DIR")
    if not value:
        local = os.environ.get("LOCALAPPDATA")
        if not local:
            raise ValueError("No se encuentra LOCALAPPDATA. Use una carpeta DEMO explicita.")
        value = Path(local) / KIND
    original = Path(value).absolute()
    directory = original.resolve()
    if (
        directory != original
        or directory == ROOT
        or directory.is_relative_to(ROOT)
        or ROOT.is_relative_to(directory)
    ):
        raise ValueError(
            "La carpeta DEMO debe estar fuera del repositorio y sin enlaces/junctions."
        )
    if directory == directory.parent:
        raise ValueError("No se admite una raiz de disco como carpeta DEMO.")
    return directory


def read_configuration(directory):
    directory = demo_directory(directory)
    path = directory / "config.json"
    if (
        path.is_symlink()
        or (hasattr(path, "is_junction") and path.is_junction())
        or (path.exists() and path.stat().st_nlink != 1)
    ):
        raise ValueError("Configuracion DEMO enlazada: operacion rechazada.")
    values = json.loads(path.read_text(encoding="utf-8"))
    if (
        set(values) != {"kind", "version", "secret_key", "backup_key"}
        or values.get("kind") != KIND
        or values.get("version") != 1
    ):
        raise ValueError("La carpeta no contiene una configuracion BeautyTPV DEMO reconocida.")
    if not isinstance(values["secret_key"], str) or len(values["secret_key"]) < 40:
        raise ValueError("Secreto DEMO invalido. No se inicia la aplicacion.")
    from cryptography.fernet import Fernet

    Fernet(values["backup_key"].encode("ascii"))
    # Never follow a substituted database to a different installation.
    for filename in (
        "demo.sqlite3",
        "server.json",
        "credenciales-demo.txt",
        "launch.lock",
        "preparacion.log",
        "demo-server.log",
        "staticfiles",
        "backups",
    ):
        target = directory / filename
        if (
            target.resolve().parent != directory
            or target.is_symlink()
            or (hasattr(target, "is_junction") and target.is_junction())
            or (target.is_file() and target.stat().st_nlink != 1)
        ):
            raise ValueError("Archivo DEMO enlazado fuera de su carpeta: " + filename)
    return values


def secure_directory(directory):
    directory = demo_directory(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        import csv

        result = subprocess.run(
            ["whoami", "/user", "/fo", "csv", "/nh"], capture_output=True, text=True, check=True
        )
        sid = next(csv.reader(result.stdout.strip().splitlines()))[1]
        subprocess.run(
            [
                "icacls",
                str(directory),
                "/inheritance:r",
                "/grant:r",
                f"*{sid}:(OI)(CI)F",
                "*S-1-5-18:(OI)(CI)F",
            ],
            capture_output=True,
            check=True,
        )
    else:
        directory.chmod(0o700)


def demo_environment(directory):
    directory = demo_directory(directory)
    read_configuration(directory)
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("BEAUTYTPV_", "DJANGO_")) and key != "PYTHONPATH"
    }
    env.update(
        {
            "BEAUTYTPV_DEMO_DIR": str(directory),
            "DJANGO_SETTINGS_MODULE": "config.demo_settings",
            "PYTHONUTF8": "1",
        }
    )
    return env


def write_credentials(directory, credentials):
    directory = demo_directory(directory)
    read_configuration(directory)
    if not credentials:
        return
    lines = [
        "BeautyTPV DEMO - credenciales privadas generadas para esta instancia",
        "Solo localhost / datos sinteticos / TEST. No reutilizar en instalaciones reales.",
        "",
        "Para Admin/Superadmin: marque 'Contrasena administrativa' al entrar.",
        "El PIN no concede elevacion. PII de Superadmin requiere aprobacion de demo_admin.",
        "",
    ]
    for username, values in credentials.items():
        lines += [
            f"Usuario: {username}",
            f"Rol: {values['role']}",
            f"Contrasena: {values['password']}",
            f"PIN: {values['pin']}",
            "",
        ]
    destination = directory / "credenciales-demo.txt"
    destination.write_text("\n".join(lines), encoding="utf-8")
    if os.name != "nt":
        destination.chmod(0o600)
