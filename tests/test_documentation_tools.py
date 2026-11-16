"""Adversarial checks for the documentation auditor, not mirrored product tests."""

import hashlib
import json

from PIL import Image

from scripts.audit_documentation import (
    audit_licenses,
    audit_markdown,
    audit_screenshots,
    heading_anchors,
)


def test_link_audit_detects_missing_target_anchor_alt_and_unclosed_fence(tmp_path):
    page = tmp_path / "README.md"
    page.write_text(
        "# Bienvenida\n[bad](missing.md)\n[anchor](#ausente)\n![](photo.png)\n```python\n",
        encoding="utf-8",
    )
    Image.new("RGB", (1, 1)).save(tmp_path / "photo.png")
    result = audit_markdown(tmp_path, [page])
    kinds = {error["kind"] for error in result["errors"]}
    assert {"missing_target", "missing_anchor", "image_alt", "unclosed_fence"} <= kinds


def test_anchors_duplicate_headings_and_references_ignore_code_literals(tmp_path):
    page = tmp_path / "README.md"
    page.write_text(
        "# Datos fiscales\n# Datos fiscales\n[second][s]\n\n[s]: #datos-fiscales-1\n\n```python\n[not a real link](missing.md)\n```\n",
        encoding="utf-8",
    )
    assert heading_anchors(page.read_text()) == {"datos-fiscales", "datos-fiscales-1"}
    assert not audit_markdown(tmp_path, [page])["errors"]


def test_table_audit_tolerates_pipe_inside_code_but_rejects_missing_cell(tmp_path):
    page = tmp_path / "README.md"
    page.write_text(
        "| A | B |\n|---|---|\n| `OPEN|CLOSED` | value |\n| missing |\n", encoding="utf-8"
    )
    result = audit_markdown(tmp_path, [page])
    assert [error["line"] for error in result["errors"] if error["kind"] == "table_columns"] == [4]


def test_screenshot_manifest_requires_matching_pixels_hash_and_provenance(tmp_path):
    folder = tmp_path / "docs/screenshots"
    folder.mkdir(parents=True)
    picture = folder / "plano.png"
    Image.new("RGB", (1440, 900), "white").save(picture)
    row = {
        "file": "plano.png",
        "sha256": hashlib.sha256(picture.read_bytes()).hexdigest(),
        "width": 1440,
        "height": 900,
        "role": "EMPLOYEE",
        "route": "/tpv/",
    }
    (folder / "manifest.json").write_text(json.dumps({"screenshots": [row]}))
    assert audit_screenshots(tmp_path)["status"] == "COMPLETO"
    row.update(sha256="0" * 64, width=820)
    del row["role"]
    (folder / "manifest.json").write_text(json.dumps({"screenshots": [row]}))
    result = audit_screenshots(tmp_path)
    assert len(result["errors"]) == 3


def test_license_bundle_integrity_does_not_imply_redistribution_approval(tmp_path):
    folder = tmp_path / "docs/legal"
    folder.mkdir(parents=True)
    bundle = folder / "third-party.txt"
    bundle.write_bytes(b"Synthetic license notice")
    entry = {
        "name": "synthetic-package",
        "version": "1.0",
        "bundle": {
            "path": str(bundle.relative_to(tmp_path)),
            "sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        },
        "review_required": True,
    }
    (folder / "DEPENDENCY_LICENSES.json").write_text(json.dumps({"packages": [entry]}))
    result = audit_licenses(tmp_path)
    assert result["status"] == "COMPLETO"
    assert result["redistribution_approval"] == "BLOQUEADO EXTERNO"
    bundle.write_bytes(b"Tampered")
    assert audit_licenses(tmp_path)["status"] == "PARCIAL"


def test_secret_assignment_is_reported_without_copying_the_secret(tmp_path):
    page = tmp_path / "README.md"
    value = "qK9Z6yTd7R2vW8mX4pB1nF3jL5cS0aH"
    page.write_text(f'BEAUTYTPV_SECRET_KEY="{value}"\n', encoding="utf-8")
    result = audit_markdown(tmp_path, [page])
    assert any(error["kind"] == "possible_secret" for error in result["errors"])
    assert value not in json.dumps(result)
