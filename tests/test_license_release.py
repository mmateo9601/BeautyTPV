"""Offline regressions for product licensing and safe legal-file distribution."""

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from apps.support import updates
from scripts import license_inventory
from scripts.audit_documentation import audit_licenses
from scripts.package_release import build_package

LEGAL_FILES = {"LICENSE", "THIRD_PARTY_NOTICES.md", "SOURCE_CODE.md"}


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


@pytest.fixture
def licensed_project(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "pyproject.toml").write_text(
        '[project]\nname = "beautytpv"\nversion = "0.1.0"\n'
        'license = "AGPL-3.0-only"\n'
        'license-files = ["LICENSE", "THIRD_PARTY_NOTICES.md", "SOURCE_CODE.md"]\n',
        encoding="utf-8",
    )
    # Synthetic texts isolate hashing/packaging from any legal-text assertion.
    for name in LEGAL_FILES:
        (root / name).write_bytes(("fixture for " + name + "\n").encode())
    (root / "requirements.lock.txt").write_bytes(b"example==1.0\r\n")
    return root


def write_inventory(root):
    manifest = {
        "product": license_inventory.product_license_metadata(root),
        "lock_sha256": sha256(b"example==1.0\n"),
        "packages": [],
        "tools": [],
        "interpreter": {},
        "vendors": [],
    }
    target = root / "docs/legal/DEPENDENCY_LICENSES.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


@pytest.mark.parametrize("tamper", ["text", "metadata"])
def test_documentation_audit_detects_product_license_drift(licensed_project, tamper):
    manifest = write_inventory(licensed_project)
    manifest["packages"] = [{"name": "synthetic", "version": "1.0", "installed": False}]
    (licensed_project / "docs/legal/DEPENDENCY_LICENSES.json").write_text(json.dumps(manifest))
    assert audit_licenses(licensed_project)["status"] == "COMPLETO"
    if tamper == "text":
        (licensed_project / "LICENSE").write_bytes(b"altered license")
    else:
        project = licensed_project / "pyproject.toml"
        project.write_text(project.read_text().replace("AGPL-3.0-only", "MIT"))
    result = audit_licenses(licensed_project)
    assert result["status"] == "PARCIAL"
    assert any("Product" in error for error in result["errors"])


def make_package(tmp_path, files):
    destination = tmp_path / "candidate.zip"
    with zipfile.ZipFile(destination, "w") as archive:
        for name, payload in files.items():
            archive.writestr(name, payload)
        archive.writestr(
            "release.json",
            json.dumps({"version": "0.1.0", "files": {n: sha256(p) for n, p in files.items()}}),
        )
    return destination, sha256(destination.read_bytes())


def test_product_metadata_uses_project_identity_spdx_and_exact_file_bytes(licensed_project):
    product = license_inventory.product_license_metadata(licensed_project)
    assert (product["name"], product["version"], product["license"]) == (
        "beautytpv",
        "0.1.0",
        "AGPL-3.0-only",
    )
    assert product["license_file_present"] is True
    assert product["license_file"] == "LICENSE"
    assert product["license_sha256"] == sha256((licensed_project / "LICENSE").read_bytes())
    assert product["license_files"] == [
        {"file": name, "sha256": sha256((licensed_project / name).read_bytes())}
        for name in sorted(LEGAL_FILES)
    ]


def test_inventory_verify_accepts_matching_product(licensed_project, monkeypatch):
    expected = write_inventory(licensed_project)
    monkeypatch.setattr(license_inventory, "ROOT", licensed_project)
    assert license_inventory.verify() == expected


@pytest.mark.parametrize("changed", ["LICENSE", "THIRD_PARTY_NOTICES.md", "SOURCE_CODE.md"])
def test_inventory_verify_rejects_altered_legal_text(licensed_project, monkeypatch, changed):
    write_inventory(licensed_project)
    monkeypatch.setattr(license_inventory, "ROOT", licensed_project)
    with (licensed_project / changed).open("ab") as stream:
        stream.write(b"altered")
    with pytest.raises(ValueError, match="licencia del producto"):
        license_inventory.verify()


def test_inventory_verify_rejects_spdx_drift_from_manifest(licensed_project, monkeypatch):
    write_inventory(licensed_project)
    monkeypatch.setattr(license_inventory, "ROOT", licensed_project)
    project = licensed_project / "pyproject.toml"
    project.write_text(project.read_text().replace("AGPL-3.0-only", "MIT"), encoding="utf-8")
    with pytest.raises(ValueError, match="licencia del producto"):
        license_inventory.verify()


def test_product_metadata_requires_license_file(licensed_project):
    (licensed_project / "LICENSE").unlink()
    with pytest.raises(ValueError, match="sin archivos"):
        license_inventory.product_license_metadata(licensed_project)


def test_release_includes_exact_legal_files_hashes_and_excludes_private_data(
    licensed_project, tmp_path
):
    private = {
        ".env": b"SECRET=private",
        "db.sqlite3": b"private database",
        "backups/customer.btpv": b"private backup",
        "media/customer.pdf": b"private invoice",
        "logs/support.log": b"private log",
    }
    for name, payload in private.items():
        target = licensed_project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    output = tmp_path / "release.zip"
    digest = build_package(licensed_project, output, "0.1.0")
    manifest = updates.validate_package(output, digest)
    assert digest == sha256(output.read_bytes())
    assert output.with_suffix(".zip.sha256").read_text().strip() == digest
    assert updates.ALLOWED_ROOT_FILES == LEGAL_FILES
    with zipfile.ZipFile(output) as archive:
        assert set(archive.namelist()) == LEGAL_FILES | {
            "pyproject.toml",
            "requirements.lock.txt",
            "release.json",
        }
        for name in LEGAL_FILES:
            assert archive.read(name) == (licensed_project / name).read_bytes()
            assert manifest["files"][name] == sha256(archive.read(name))
        assert not set(private).intersection(archive.namelist())


@pytest.mark.parametrize(
    "name",
    [
        "LICENSE/evil.py",
        "THIRD_PARTY_NOTICES.md/evil.py",
        "SOURCE_CODE.md/evil.py",
        "LICENSE.extra",
        "nested/LICENSE",
        "../LICENSE",
        "LICENSE\\evil.py",
    ],
)
def test_update_rejects_legal_filename_as_writable_subtree(tmp_path, name):
    package, digest = make_package(tmp_path, {name: b"untrusted"})
    with pytest.raises(ValueError):
        updates.validate_package(package, digest)


def test_package_does_not_traverse_directory_named_license(tmp_path):
    root = tmp_path / "source"
    (root / "LICENSE").mkdir(parents=True)
    (root / "LICENSE/evil.py").write_text("untrusted")
    (root / "README.md").write_text("installation")
    package = tmp_path / "release.zip"
    digest = build_package(root, package, "0.1.0")
    assert set(updates.validate_package(package, digest)["files"]) == {"README.md"}


def test_package_omits_symbolic_legal_file(licensed_project, tmp_path, monkeypatch):
    # Simulate the filesystem attribute without requiring Windows symlink privilege.
    original = Path.is_symlink
    link = licensed_project / "LICENSE"
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == link or original(path))
    package = tmp_path / "release.zip"
    digest = build_package(licensed_project, package, "0.1.0")
    assert "LICENSE" not in updates.validate_package(package, digest)["files"]


def test_update_rejects_symbolic_legal_destination_before_backup(tmp_path, monkeypatch):
    root = tmp_path / "installation"
    root.mkdir()
    target = root / "LICENSE"
    target.write_bytes(b"original")
    database = root / "db.sqlite3"
    database.write_bytes(b"untouched database")
    package, digest = make_package(tmp_path, {"LICENSE": b"updated"})
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == target or original(path))
    backups = []
    monkeypatch.setattr(updates, "create_backup", lambda *args: backups.append(args))
    with pytest.raises(ValueError, match="Destino protegido"):
        updates.apply_update(package, digest, root, database, b"unused", offline=True)
    assert backups == []
    assert target.read_bytes() == b"original"
    assert database.read_bytes() == b"untouched database"
