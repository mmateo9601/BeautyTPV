"""Offline, staged code updates; dependency changes fail preflight without touching the venv."""

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from .operations import create_backup, exclusive_operation, hold_path

ALLOWED_TOP_LEVEL = {
    "schemas",
    "tests",
    ".env.example",
    "apps",
    "config",
    "templates",
    "static",
    "scripts",
    "docs",
    "manage.py",
    "pyproject.toml",
    "requirements.lock.txt",
    "README.md",
}
# Legal notices are exact root filenames, never additional writable subtrees.
ALLOWED_ROOT_FILES = {"LICENSE", "THIRD_PARTY_NOTICES.md", "SOURCE_CODE.md"}


def validate_package(archive, expected_sha256):
    archive = Path(archive)
    if (
        not re.fullmatch(r"[a-fA-F0-9]{64}", expected_sha256)
        or hashlib.sha256(archive.read_bytes()).hexdigest() != expected_sha256.lower()
    ):
        raise ValueError("SHA-256 del paquete incorrecto.")
    archive_bytes = archive.read_bytes()
    if hashlib.sha256(archive_bytes).hexdigest() != expected_sha256.lower():
        raise ValueError("El paquete cambió durante la validación.")
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as package:
        entries = [entry.filename for entry in package.infolist() if not entry.is_dir()]
        if len(entries) != len(set(name.casefold() for name in entries)):
            raise ValueError("El paquete contiene rutas duplicadas o colisiones de mayúsculas.")
        manifest = json.loads(package.read("release.json"))
        if (
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.+_-]{0,39}", str(manifest.get("version", "")))
            or not isinstance(manifest.get("files"), dict)
            or not manifest["files"]
        ):
            raise ValueError("release.json inválido.")
        if set(entries) - {"release.json"} != set(manifest["files"]):
            raise ValueError("Manifest y archivos distintos.")
        for name, digest in manifest["files"].items():
            path = PurePosixPath(name)
            if (
                path.is_absolute()
                or ".." in path.parts
                or not path.parts
                or (path.parts[0] not in ALLOWED_TOP_LEVEL and name not in ALLOWED_ROOT_FILES)
                or "\\" in name
                or ":" in name
                or str(path) != name
            ):
                raise ValueError("Ruta de paquete no permitida.")
            if (
                not isinstance(digest, str)
                or hashlib.sha256(package.read(name)).hexdigest() != digest
            ):
                raise ValueError("Hash interno de paquete incorrecto.")
        return manifest


def _check_locked_dependencies(lock_path, runner, executable):
    if not lock_path.is_file():
        return
    pins = []
    for line in lock_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9][A-Za-z0-9_.-]*)==([A-Za-z0-9][A-Za-z0-9.+_-]*)", line)
        if not match:
            raise ValueError("Dependencias deben estar fijadas exactamente, sin URLs/opciones.")
        pins.append(list(match.groups()))
    code = "import importlib.metadata as m,json,sys; pins=json.loads(sys.argv[1]); bad=[name+'=='+wanted for name,wanted in pins if m.version(name)!=wanted]; assert not bad, 'Entorno incompatible con lock: '+', '.join(bad)"
    try:
        runner([executable, "-c", code, json.dumps(pins)])
        runner([executable, "-m", "pip", "check"])
    except Exception as error:
        raise ValueError(
            "Entorno incompatible: provisione y verifique dependencias antes de actualizar. La actualización no modifica pip/venv."
        ) from error


def _atomic_write(destination, payload):
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".update-", dir=destination.parent)
    staged = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staged, destination)
    finally:
        staged.unlink(missing_ok=True)


def apply_update(archive, expected_sha256, root, database, key, *, offline, runner=None):
    if not offline:
        raise ValueError("Actualización requiere servicio y workers detenidos (--offline).")
    manifest = validate_package(archive, expected_sha256)
    root, database = Path(root).resolve(), Path(database).resolve()
    runner = runner or (lambda arguments: subprocess.run(arguments, cwd=root, check=True))
    with (
        exclusive_operation(database),
        tempfile.TemporaryDirectory(prefix=".update-stage-", dir=root) as temporary,
    ):
        staged = Path(temporary)
        targets = {}
        # Stage and validate every path before writing a single installation file.
        archive_bytes = Path(archive).read_bytes()
        if hashlib.sha256(archive_bytes).hexdigest() != expected_sha256.lower():
            raise ValueError("El paquete cambió antes de preparar la actualización.")
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as package:
            for name in manifest["files"]:
                destination = root / name
                resolved = destination.resolve()
                if (
                    not resolved.is_relative_to(root)
                    or resolved == database
                    or destination.is_symlink()
                    or (destination.exists() and not destination.is_file())
                ):
                    raise ValueError("Destino protegido, enlace o ruta fuera de instalación.")
                targets[name] = destination
                target = staged / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(package.read(name))
            (staged / "release.json").write_bytes(package.read("release.json"))
        lock = staged / "requirements.lock.txt"
        _check_locked_dependencies(
            lock if lock.exists() else root / "requirements.lock.txt", runner, sys.executable
        )
        backup = root / "backups" / ("pre-update-" + manifest["version"] + ".btpv")
        create_backup(database, backup, key)
        targets["release.json"] = root / "release.json"
        previous = {
            name: target.read_bytes() if target.is_file() else None
            for name, target in targets.items()
        }
        modified = []
        try:
            for name, target in targets.items():
                # Mark before IO: failure after replacement must also be rolled back.
                modified.append(name)
                _atomic_write(target, (staged / name).read_bytes())
            runner([sys.executable, str(root / "manage.py"), "migrate", "--noinput"])
            runner([sys.executable, str(root / "manage.py"), "check"])
            runner([sys.executable, str(root / "manage.py"), "collectstatic", "--noinput"])
        except Exception:
            rollback_errors = []
            for name in reversed(modified):
                try:
                    if previous[name] is None:
                        targets[name].unlink(missing_ok=True)
                    else:
                        _atomic_write(targets[name], previous[name])
                except OSError:
                    rollback_errors.append(name)
            hold_path(database).write_text(
                json.dumps(
                    {
                        "reason": "Actualización fallida; BD preservada. Revisar compatibilidad antes de reanudar.",
                        "rollback_incomplete": rollback_errors,
                    }
                ),
                encoding="utf-8",
            )
            raise
    return manifest
