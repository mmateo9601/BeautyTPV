"""Inventory locked distributions and preserve their real licence notices.

No dependency is installed and no product licence is selected. Network access
is opt-in, restricted to the missing pySerial notice at its fixed release tag.
"""

import argparse
import hashlib
import json
import platform
import re
import sys
import tomllib
import urllib.request
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYSERIAL_LICENSE = "https://raw.githubusercontent.com/pyserial/pyserial/v3.5/LICENSE.txt"
REVIEW = {
    "certifi": "MPL-2.0: revisar obligaciones de los archivos cubiertos y acceso a su fuente.",
    "lxml": "LICENSES.txt enumera licencias/componentes adicionales, recursos y binarios; revisar el wheel exacto.",
    "pillow": "MIT-CMU declarada; los codecs/binarios del wheel pueden tener avisos adicionales.",
    "playwright": "Incluye driver Node y ThirdPartyNotices. Los navegadores descargados tienen sus propios avisos; no se redistribuyen aqui.",
    "reportlab": "Incluye fuentes Bitstream Vera y DarkGarden GPL-2.0-or-later; no tratar todo el wheel como BSD.",
    "text-unidecode": "Licencia dual Artistic/GPL: elegir y cumplir la alternativa pertinente antes de redistribuir.",
    "python-slugify": "Pin existente sin dependencia directa en pyproject; revisar necesidad y text-unidecode transitivo.",
    "cryptography": "Apache-2.0 OR BSD-3-Clause; revisar tambien OpenSSL/bibliotecas incluidas en el wheel.",
    "qrcode": "Los classifiers incluyen Other/Proprietary; el texto LICENSE concreto es la evidencia de sus condiciones BSD.",
    "tzdata": "Metadatos Apache-2.0 y avisos de datos IANA; conservar ambos textos.",
}
HINTS = {
    "colorama": "BSD-3-Clause (texto local)",
    "pyserial": "BSD-3-Clause (licencia upstream v3.5)",
    "pytest-django": "BSD-3-Clause (metadatos/texto local)",
    "pytest-playwright": "Apache-2.0 (texto local)",
    "pyusb": "BSD-3-Clause (texto local)",
    "qrcode": "BSD-3-Clause (texto local; revisar classifiers)",
    "reportlab": "BSD-3-Clause + licencias de fuentes (revisar)",
    "sqlparse": "BSD-3-Clause (texto local)",
    "text-unidecode": "Artistic OR GPL (revisar texto exacto)",
    "waitress": "ZPL-2.1",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def lock_digest():
    # Lock lines are semantic text; Git checks them out with CRLF on Windows.
    return digest((ROOT / "requirements.lock.txt").read_bytes().replace(b"\r\n", b"\n"))


def normalized(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def licence_paths(dist):
    return sorted(
        (
            item
            for item in dist.files or []
            if item.locate().is_file()
            and item.suffix.lower() not in (".py", ".pyc")
            and any(
                word in item.name.lower() for word in ("license", "copying", "notice", "copyright")
            )
        ),
        key=str,
    )


def write_bundle(target, items):
    content = bytearray()
    evidence = []
    for origin, data in items:
        content.extend(
            ("\n===== ORIGINAL: " + origin + " =====\nSHA256: " + digest(data) + "\n\n").encode(
                "utf-8"
            )
        )
        content.extend(data)
        content.extend(b"\n===== END ORIGINAL =====\n")
        evidence.append({"origin": origin, "sha256": digest(data), "bytes": len(data)})
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return {
        "file": target.relative_to(ROOT).as_posix(),
        "sha256": digest(content),
        "sources": evidence,
    }


def build(fetch_missing=False):
    legal = ROOT / "docs/legal"
    bundles = legal / "third-party"
    bundles.mkdir(parents=True, exist_ok=True)
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    direct_runtime = {
        normalized(re.split(r"[\[<>=!~ ]", value)[0]) for value in project["dependencies"]
    }
    direct_dev = {
        normalized(re.split(r"[\[<>=!~ ]", value)[0])
        for value in project["optional-dependencies"]["dev"]
    }
    packages = []
    for line in (ROOT / "requirements.lock.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        name, version = line.strip().split("==")
        dist = distribution(name)
        if dist.version != version:
            raise ValueError("El entorno no coincide con el lock: " + name)
        meta = dist.metadata
        key = normalized(name)
        originals = [
            (str(item).replace("\\", "/"), item.locate().read_bytes())
            for item in licence_paths(dist)
        ]
        if key == "pyserial" and not originals:
            supplement = legal / "upstream/pyserial-3.5-LICENSE.txt"
            if fetch_missing:
                with urllib.request.urlopen(PYSERIAL_LICENSE, timeout=30) as response:
                    data = response.read(100_000)
                if b"BSD-3-Clause" not in data or b"Redistribution" not in data:
                    raise ValueError("Licencia pySerial upstream no reconocida.")
                supplement.parent.mkdir(parents=True, exist_ok=True)
                supplement.write_bytes(data)
            if supplement.exists():
                originals.append((PYSERIAL_LICENSE, supplement.read_bytes()))
        raw = meta.get("License", "")
        expression = meta.get("License-Expression", "")
        scope = (
            "runtime-direct"
            if key in direct_runtime
            else "development-direct"
            if key in direct_dev
            else "locked-transitive-or-tool"
        )
        bundle = write_bundle(bundles / (key + ".txt"), originals) if originals else None
        packages.append(
            {
                "name": name,
                "version": version,
                "scope": scope,
                "license_expression": expression or None,
                "license_metadata": raw or None,
                "license_label": HINTS.get(key) or expression or raw or "NOASSERTION",
                "classifiers": meta.get_all("Classifier", []),
                "project_urls": meta.get_all("Project-URL", []),
                "home_page": meta.get("Home-page"),
                "metadata_sha256": digest(dist.read_text("METADATA").encode("utf-8")),
                "notice_bundle": bundle,
                "review_required": key in REVIEW or not originals,
                "review_reason": REVIEW.get(key)
                or (
                    "No se encontro texto de licencia: revision manual obligatoria."
                    if not originals
                    else "Inventario tecnico; revisar tambien el artefacto de distribucion final."
                ),
            }
        )
    vendors = []
    for name, version, license_id in (("bootstrap", "5.3.8", "MIT"), ("htmx", "2.0.8", "0BSD")):
        directory = ROOT / "static/vendor" / name
        vendors.append(
            {
                "name": name,
                "version": version,
                "license": license_id,
                "files": [
                    {"file": file.relative_to(ROOT).as_posix(), "sha256": digest(file.read_bytes())}
                    for file in sorted(directory.iterdir())
                    if file.is_file()
                ],
            }
        )
    tools = []
    for name in ("pip", "setuptools"):
        try:
            item = distribution(name)
        except PackageNotFoundError:
            tools.append(
                {
                    "name": name,
                    "version": None,
                    "scope": "build/tooling",
                    "review_required": True,
                    "note": "Requisito build no instalado persistentemente; version del entorno build aislado no inventada.",
                }
            )
        else:
            texts = [
                (str(p).replace("\\", "/"), p.locate().read_bytes()) for p in licence_paths(item)
            ]
            tools.append(
                {
                    "name": name,
                    "version": item.version,
                    "scope": "build/tooling",
                    "notice_bundle": write_bundle(bundles / (name + ".txt"), texts),
                    "review_required": True,
                    "note": "Herramienta local, no dependencia runtime del producto.",
                }
            )
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    interpreter = {
        "name": "Python",
        "version": platform.python_version(),
        "scope": "external-interpreter",
        "review_required": True,
        "note": "Si se redistribuye Python o un instalador completo, revisar tambien sus bibliotecas incorporadas y terminos originales.",
    }
    if python_license.is_file():
        interpreter["notice_bundle"] = write_bundle(
            bundles / "python.txt", [("Python/LICENSE.txt", python_license.read_bytes())]
        )
    manifest = {
        "schema": 1,
        "product": {
            "name": project["name"],
            "version": project["version"],
            "license": "NOASSERTION",
            "license_file_present": (ROOT / "LICENSE").exists(),
        },
        "scope": "Installed versions matching lock; preserved local notices; not a legal clearance or complete binary SBOM",
        "lock_sha256": lock_digest(),
        "lock_hash_normalization": "UTF-8 bytes with CRLF converted to LF",
        "packages": packages,
        "vendors": vendors,
        "tools": tools,
        "interpreter": interpreter,
        "additional_review": [
            "Navegadores Chromium/Playwright descargados fuera del repo y licencias de su build concreto.",
            "Recursos XSD/WSDL AEAT: fuente publica no implica licencia MIT del producto.",
            "Fuentes de ReportLab, codecs de Pillow y bibliotecas nativas de wheels.",
            "Iconos Unicode y tipografias del sistema referenciados: no se distribuyen archivos de fuentes propios en static.",
        ],
    }
    (legal / "DEPENDENCY_LICENSES.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def verify():
    manifest = json.loads(
        (ROOT / "docs/legal/DEPENDENCY_LICENSES.json").read_text(encoding="utf-8")
    )
    if manifest["lock_sha256"] != lock_digest():
        raise ValueError("El manifiesto no coincide con requirements.lock.txt.")
    for item in [*manifest["packages"], *manifest["tools"], manifest["interpreter"]]:
        bundle = item.get("notice_bundle")
        if bundle and digest((ROOT / bundle["file"]).read_bytes()) != bundle["sha256"]:
            raise ValueError("Avisos alterados: " + item["name"])
    for vendor in manifest["vendors"]:
        for file in vendor["files"]:
            if digest((ROOT / file["file"]).read_bytes()) != file["sha256"]:
                raise ValueError("Vendor alterado: " + file["file"])
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-missing", action="store_true")
    parser.add_argument("--verify", action="store_true")
    arguments = parser.parse_args()
    result = verify() if arguments.verify else build(arguments.fetch_missing)
    print(
        json.dumps(
            {
                "packages": len(result["packages"]),
                "vendors": len(result["vendors"]),
                "product_license": result["product"]["license"],
                "review_required": sum(p["review_required"] for p in result["packages"]),
            }
        )
    )
