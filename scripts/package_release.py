"""Build a reviewable release package without runtime data or secrets."""

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apps.support.updates import (  # noqa: E402
    ALLOWED_ROOT_FILES,
    ALLOWED_TOP_LEVEL,
    validate_package,
)


def build_package(root, destination, version):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if not version or any(
        character not in "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-_"
        for character in version
    ):
        raise ValueError("Identificador de versión no válido.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = {}
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(ALLOWED_TOP_LEVEL | ALLOWED_ROOT_FILES):
            source = root / name
            if name in ALLOWED_ROOT_FILES and not source.is_file():
                continue
            paths = source.rglob("*") if source.is_dir() else [source]
            for path in sorted(paths):
                if not path.is_file() or path.is_symlink():
                    continue
                relative = path.relative_to(root)
                if "__pycache__" in relative.parts or path.suffix in (".pyc", ".pyo"):
                    continue
                data = path.read_bytes()
                files[relative.as_posix()] = hashlib.sha256(data).hexdigest()
                archive.writestr(relative.as_posix(), data)
        archive.writestr("release.json", json.dumps({"version": version, "files": files}, indent=2))
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    validate_package(destination, digest)
    destination.with_suffix(destination.suffix + ".sha256").write_text(
        digest + "\n", encoding="ascii"
    )
    return digest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", required=True)
    options = parser.parse_args()
    print(build_package(ROOT, options.output, options.version))
