"""Installed release metadata; no user-supplied version from HTTP."""

import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def application_version(root=None):
    if root is None:
        root = Path(__file__).resolve().parents[2]
    try:
        value = json.loads((Path(root) / "release.json").read_text(encoding="utf-8"))["version"]
        if isinstance(value, str) and 0 < len(value) <= 40:
            return value
    except (OSError, ValueError, KeyError, TypeError):
        pass
    try:
        return version("beautytpv")
    except PackageNotFoundError:
        return "development"
