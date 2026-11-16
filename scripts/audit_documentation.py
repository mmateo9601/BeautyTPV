"""Read-only documentation checks; results do not certify legal or external compliance."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(!?)\[([^\]]*)\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[\"'][^\n]*?[\"'])?\s*\)")
REFERENCE = re.compile(r"(?m)^\s{0,3}\[([^\]]+)\]:\s*(<[^>]+>|\S+)")
REFERENCE_USE = re.compile(r"(!?)\[([^\]]+)\]\[([^\]]*)\]")
SECRET = re.compile(
    r"(?:BEAUTYTPV_(?:SECRET_KEY|BACKUP_KEY)|password|contrase[nñ]a)\s*[=:]\s*[\"']([A-Za-z0-9+/=_-]{20,})[\"']",
    re.IGNORECASE,
)
CANONICAL = (
    "docs/README.md",
    "docs/FUNCIONALIDADES.md",
    "docs/manuales/GUIA_USUARIO.md",
    "docs/manuales/GUIA_ADMINISTRADOR.md",
    "docs/manuales/GUIA_SUPERADMIN.md",
    "docs/arquitectura/ARQUITECTURA.md",
    "docs/arquitectura/MODELOS_DATOS.md",
    "docs/arquitectura/FLUJOS_NEGOCIO.md",
    "docs/arquitectura/SEGURIDAD.md",
    "docs/arquitectura/DECISIONES_TECNICAS.md",
    "docs/desarrollo/GUIA_DESARROLLADOR.md",
    "docs/desarrollo/ENTORNO_DESARROLLO.md",
    "docs/desarrollo/PRUEBAS.md",
    "docs/desarrollo/CONVENCIONES.md",
    "docs/desarrollo/EXTENSIONES.md",
    "docs/integraciones/VERIFACTU.md",
    "docs/integraciones/HARDWARE.md",
    "docs/integraciones/SQLITE.md",
    "docs/instalacion/INSTALACION_WINDOWS.md",
    "docs/instalacion/ARRANQUE_DEMO.md",
    "docs/instalacion/DESPLIEGUE_LOCAL.md",
    "docs/instalacion/BACKUP_RESTORE.md",
    "docs/instalacion/ACTUALIZACIONES.md",
    "docs/instalacion/SOLUCION_PROBLEMAS.md",
    "docs/legal/OPCIONES_LICENCIA.md",
)


def issue(collection, kind, path, line, detail):
    collection.append(
        {"kind": kind, "file": str(path).replace("\\", "/"), "line": line, "detail": detail}
    )


def prose_lines(text):
    """Keep line numbers while excluding fenced code; retain prose and headings."""
    result, fence = [], None
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if match:
            mark = match.group(1)
            if fence is None:
                fence = (mark[0], len(mark), number)
            elif mark[0] == fence[0] and len(mark) >= fence[1]:
                fence = None
            result.append((number, ""))
        else:
            result.append((number, line if fence is None else ""))
    return result, fence


def heading_anchors(text):
    anchors, counts = set(), {}
    lines, _ = prose_lines(text)
    for _, line in lines:
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        heading = re.sub(r"<[^>]+>", "", match.group(1))
        heading = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", heading)
        heading = re.sub(r"[^\w\-\s]", "", heading, flags=re.UNICODE).strip().lower()
        slug = re.sub(r"\s", "-", unicodedata.normalize("NFC", heading))
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        anchors.add(slug + (f"-{count}" if count else ""))
    anchors.update(re.findall(r'<(?:a|h[1-6])\b[^>]*\bid=["\x27]([^"\x27]+)', text))
    return anchors


def local_target(root, source, target):
    target = unquote(target.strip("<>"))
    if re.match(r"^[A-Za-z]:[/\\]", target):
        return None, "absolute_local_path"
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None, "external"
    filename = parsed.path
    path = (
        source
        if not filename
        else (root / filename.lstrip("/") if filename.startswith("/") else source.parent / filename)
    )
    return path.resolve(), parsed.fragment


def audit_markdown(root, files):
    errors, warnings, links, images, routes = [], [], [], [], []
    contents = {path: path.read_text(encoding="utf-8") for path in files}
    anchors = {path.resolve(): heading_anchors(text) for path, text in contents.items()}
    for source, text in contents.items():
        relative = source.relative_to(root)
        lines, fence = prose_lines(text)
        if fence:
            issue(errors, "unclosed_fence", relative, fence[2], "Unclosed fenced code block")
        references = {key.casefold(): value for key, value in REFERENCE.findall(text)}
        table_width, table_start = None, 0
        for number, line in lines:
            if line.lstrip().startswith("|"):
                cleaned = re.sub(r"`[^`]*`", "", line)
                width = len(re.findall(r"(?<!\\)\|", cleaned))
                if table_width is None:
                    table_width, table_start = width, number
                elif width != table_width:
                    issue(
                        errors,
                        "table_columns",
                        relative,
                        number,
                        f"{width} separators; expected {table_width} from line {table_start}",
                    )
            else:
                table_width = None
            found = [(m.group(1), m.group(2), m.group(3)) for m in LINK.finditer(line)]
            for match in REFERENCE_USE.finditer(line):
                key = (match.group(3) or match.group(2)).casefold()
                if key in references:
                    found.append((match.group(1), match.group(2), references[key]))
                else:
                    issue(errors, "undefined_reference", relative, number, key)
            for image, label, target in found:
                if image and not label.strip():
                    issue(errors, "image_alt", relative, number, target)
                destination, fragment = local_target(root, source, target)
                item = {
                    "source": str(relative).replace("\\", "/"),
                    "line": number,
                    "target": target,
                    "image": bool(image),
                }
                links.append(item)
                if image:
                    images.append(item)
                if destination is None:
                    if fragment == "absolute_local_path":
                        issue(warnings, "nonportable_link", relative, number, target)
                    continue
                if not destination.exists():
                    issue(errors, "missing_target", relative, number, target)
                    continue
                item["resolved"] = (
                    str(destination.relative_to(root)).replace("\\", "/")
                    if destination.is_relative_to(root)
                    else str(destination)
                )
                if fragment and destination.suffix.lower() == ".md":
                    known = anchors.get(destination) or heading_anchors(
                        destination.read_text(encoding="utf-8")
                    )
                    if fragment not in known:
                        issue(errors, "missing_anchor", relative, number, target)
                elif (
                    fragment
                    and re.fullmatch(r"L\d+(?:-L?\d+)?", fragment)
                    and destination.is_file()
                ):
                    first = int(re.search(r"\d+", fragment).group())
                    if first > len(
                        destination.read_text(encoding="utf-8", errors="replace").splitlines()
                    ):
                        issue(errors, "missing_source_line", relative, number, target)
            for code_match in re.finditer(r"`([^`\n]+)`", line):
                code = code_match.group(1)
                if (
                    code.startswith("/")
                    and "://" not in code
                    and not re.search(r"\.(?:py|md|json|png|ps1|bat|html)(?:$|#)", code)
                ):
                    if " " not in code and not any(
                        word in line.lower()
                        for word in ("ejemplo", "futuro", "placeholder", "propuesto")
                    ):
                        before, after = line[: code_match.start()], line[code_match.end() :]
                        start = max(before.rfind(";"), before.rfind(". ")) + 1
                        endings = [
                            value for value in (after.find(";"), after.find(". ")) if value >= 0
                        ]
                        end = code_match.end() + min(endings) if endings else len(line)
                        routes.append(
                            {
                                "source": str(relative).replace("\\", "/"),
                                "line": number,
                                "route": code,
                                "context": line[start:end],
                            }
                        )
        for match in SECRET.finditer(text):
            if not any(
                word in match.group(1).casefold()
                for word in ("placeholder", "ejemplo", "example", "generad", "cambiar", "synthetic")
            ):
                issue(
                    errors,
                    "possible_secret",
                    relative,
                    text[: match.start()].count("\n") + 1,
                    "Long literal credential assignment (value omitted)",
                )
        if re.search(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s+[A-Za-z0-9+/=\r\n]{80,}", text
        ):
            issue(errors, "private_key", relative, 1, "Private-key block (content omitted)")
    return {
        "errors": errors,
        "warnings": warnings,
        "links": links,
        "images": images,
        "routes": routes,
    }


def audit_screenshots(root):
    from PIL import Image

    path = root / "docs/screenshots/manifest.json"
    result = {"status": "PENDIENTE", "checked": 0, "errors": []}
    if not path.exists():
        result["errors"].append("Missing docs/screenshots/manifest.json")
        return result
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = (
        manifest
        if isinstance(manifest, list)
        else manifest.get("screenshots", manifest.get("captures", manifest.get("images", [])))
    )
    for row in entries:
        name = row.get("file", row.get("filename", row.get("path", "")))
        candidate = root / name if str(name).startswith("docs/") else path.parent / name
        if not name or not candidate.is_file():
            result["errors"].append("Missing screenshot: " + str(name))
            continue
        data = candidate.read_bytes()
        if hashlib.sha256(data).hexdigest() != row.get("sha256"):
            result["errors"].append("Screenshot hash mismatch: " + str(name))
        with Image.open(candidate) as image:
            dimensions = image.size
            image.verify()
        viewport = row.get("viewport", {})
        expected = (
            row.get("width", viewport.get("width")),
            row.get("height", viewport.get("height")),
        )
        if expected != dimensions:
            result["errors"].append("Screenshot dimensions mismatch: " + str(name))
        if dimensions not in ((1440, 900), (820, 1180), (390, 844)):
            result["errors"].append("Unexpected viewport dimensions: " + str(name))
        if not row.get("role") or not row.get("route", row.get("url")):
            result["errors"].append("Missing route/role provenance: " + str(name))
        result["checked"] += 1
    if not entries:
        result["errors"].append("No screenshots recorded")
    result["status"] = "COMPLETO" if not result["errors"] else "PARCIAL"
    return result


def audit_licenses(root):
    path = root / "docs/legal/DEPENDENCY_LICENSES.json"
    result = {"status": "PENDIENTE", "checked": 0, "errors": [], "manual_review": []}
    if not path.is_file():
        result["errors"].append("Missing dependency license manifest")
        return result
    manifest = json.loads(path.read_text(encoding="utf-8"))
    project_file = root / "pyproject.toml"
    if project_file.is_file():
        project = tomllib.loads(project_file.read_text(encoding="utf-8"))["project"]
        product = manifest.get("product", {})
        for field in ("name", "version", "license"):
            if product.get(field) != project.get(field):
                result["errors"].append("Product metadata mismatch: " + field)
        license_file = root / "LICENSE"
        if (
            not license_file.is_file()
            or product.get("license_file") != "LICENSE"
            or hashlib.sha256(license_file.read_bytes()).hexdigest()
            != product.get("license_sha256")
        ):
            result["errors"].append("Product LICENSE missing or hash mismatch")
        for evidence in product.get("license_files", []):
            target = root / evidence["file"]
            if (
                not target.is_file()
                or hashlib.sha256(target.read_bytes()).hexdigest() != evidence["sha256"]
            ):
                result["errors"].append("Product legal-file hash mismatch: " + evidence["file"])
        result["product_license"] = product.get("license")
    entries = manifest.get("packages", manifest.get("dependencies", []))
    for row in entries:
        name = row.get("name", "unnamed")
        if not row.get("version"):
            result["errors"].append("Missing version: " + name)
        bundle = row.get("bundle", row.get("notice_bundle", {}))
        if isinstance(bundle, str):
            bundle = {"path": bundle, "sha256": row.get("bundle_sha256")}
        bundle_path = bundle.get("path", bundle.get("file"))
        bundle_hash = bundle.get("sha256", row.get("bundle_sha256"))
        if bundle_path:
            target = root / bundle_path
            if (
                not target.is_file()
                or hashlib.sha256(target.read_bytes()).hexdigest() != bundle_hash
            ):
                result["errors"].append("License bundle hash mismatch: " + name)
            elif bundle.get("sources"):
                data = target.read_bytes()
                for evidence in bundle["sources"]:
                    header = (
                        f"===== ORIGINAL: {evidence['origin']} =====\n"
                        f"SHA256: {evidence['sha256']}\n\n"
                    ).encode("utf-8")
                    start = data.find(header)
                    payload = data[start + len(header) : start + len(header) + evidence["bytes"]]
                    if start < 0 or hashlib.sha256(payload).hexdigest() != evidence["sha256"]:
                        result["errors"].append("Original license evidence mismatch: " + name)
        elif row.get("installed", True):
            result["manual_review"].append(name + ": no local license bundle")
        if row.get("review_required", row.get("manual_review_required", False)):
            result["manual_review"].append(name)
        result["checked"] += 1
    for vendor in manifest.get("vendors", []):
        for item in vendor.get("files", []):
            file = root / item["file"]
            if (
                not file.is_file()
                or hashlib.sha256(file.read_bytes()).hexdigest() != item["sha256"]
            ):
                result["errors"].append("Vendored component hash mismatch: " + item["file"])
    result["vendors_checked"] = len(manifest.get("vendors", []))
    if manifest.get("lock_sha256"):
        lock = root / "requirements.lock.txt"
        normalized = lock.read_bytes().replace(b"\r\n", b"\n") if lock.exists() else b""
        if hashlib.sha256(normalized).hexdigest() != manifest["lock_sha256"]:
            result["errors"].append("requirements.lock.txt hash mismatch")
    if not entries:
        result["errors"].append("No dependency license entries")
    result["status"] = "COMPLETO" if not result["errors"] else "PARCIAL"
    # Identification can be complete while redistribution permission remains pending.
    result["redistribution_approval"] = "BLOQUEADO EXTERNO"
    return result


def audit_routes(root, references):
    sys.path.insert(0, str(root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.urls import Resolver404, URLResolver, get_resolver, resolve

    checked, errors, patterns = [], [], []
    prefixes = set()

    def include_prefixes(patterns, parent=""):
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                prefix = parent + str(pattern.pattern)
                prefixes.add("/" + prefix)
                include_prefixes(pattern.url_patterns, prefix)

    include_prefixes(get_resolver().url_patterns)
    for item in references:
        route = item["route"]
        if any(symbol in route for symbol in ("*", "...", "|", ",", "[", "(", "\\")) or route in (
            "/",
            "/static/",
        ):
            patterns.append(item)
            continue
        route = route.split("?", 1)[0].split("#", 1)[0]
        route = re.sub(r"<(?:int:|str:|slug:|path:)?[^>]+>", "1", route)
        if re.search(
            r"no\s+(?:publica(?:da)?|existe|se\s+publica)\b", item.get("context", ""), re.I
        ):
            try:
                resolve(route)
            except Resolver404:
                checked.append(
                    {
                        **item,
                        "implementation": "Documented absence independently confirmed by resolver",
                    }
                )
            else:
                errors.append({**item, "detail": "Documentation says absent but route resolves"})
            continue
        if route in prefixes:
            checked.append(
                {
                    **item,
                    "implementation": "Existing Django include prefix; not claimed as an index view",
                }
            )
            continue
        if re.fullmatch(r"/jobs/\d+", route):
            bridge = root / "apps/hardware/management/commands/hardware_bridge.py"
            if bridge.is_file() and 'r"/jobs/([1-9][0-9]{0,17})"' in bridge.read_text(
                encoding="utf-8"
            ):
                checked.append(
                    {
                        **item,
                        "implementation": "hardware_bridge HTTP handler, loopback port8766; not Django",
                    }
                )
                continue
        if route == "/__demo_ready__":
            checked.append({**item, "implementation": "scripts/demo_server.py WSGI wrapper"})
            continue
        try:
            match = resolve(route)
        except Resolver404:
            errors.append(item)
        else:
            checked.append({**item, "view": match.view_name})
    return {"checked": checked, "patterns_not_claimed_as_routes": patterns, "errors": errors}


def command_help(root):
    script_names = (
        "install.py",
        "service.py",
        "backup.py",
        "restore.py",
        "update.py",
        "windows_demo.py",
        "package_release.py",
        "audit_inventory.py",
    )
    results = []
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("BEAUTYTPV_", "DJANGO_"))
    }
    env.update(
        {"BEAUTYTPV_DEBUG": "1", "DJANGO_SETTINGS_MODULE": "config.settings", "PYTHONUTF8": "1"}
    )
    commands = [[sys.executable, str(root / "scripts" / name), "--help"] for name in script_names]
    commands += [
        [sys.executable, str(root / "manage.py"), name, "--help"]
        for name in ("check", "migrate", "bootstrap", "hardware_worker", "reconcile_restore")
    ]
    for command in commands:
        result = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=30)
        results.append(
            {
                "command": [
                    Path(command[0]).name,
                    *[
                        str(Path(arg).relative_to(root)).replace("\\", "/")
                        if str(arg).startswith(str(root))
                        else arg
                        for arg in command[1:]
                    ],
                ],
                "exit_code": result.returncode,
            }
        )
    return results


def audit(root, *, live_routes=True, run_help=False):
    root = Path(root).resolve()
    files = sorted({*root.glob("*.md"), *(root / "docs").rglob("*.md")})
    markdown = audit_markdown(root, files)
    missing = [name for name in CANONICAL if not (root / name).is_file()]
    screenshots = audit_screenshots(root)
    licenses = audit_licenses(root)
    routes = (
        audit_routes(root, markdown["routes"])
        if live_routes
        else {"status": "NOT_EXECUTED", "errors": []}
    )
    help_results = command_help(root) if run_help else []
    errors = (
        len(markdown["errors"])
        + len(missing)
        + len(screenshots["errors"])
        + len(licenses["errors"])
        + len(routes["errors"])
        + sum(result["exit_code"] != 0 for result in help_results)
    )
    return {
        "scope": "Local Markdown structure, links, route resolution, image/license integrity; not a browser/render or legal certification",
        "status": "COMPLETO" if errors == 0 else "PARCIAL",
        "error_count": errors,
        "markdown_files": len(files),
        "missing_canonical_documents": missing,
        "markdown": markdown,
        "screenshots": screenshots,
        "licenses": licenses,
        "routes": routes,
        "commands_help": help_results,
        "main_license_files": [
            path.name
            for pattern in ("LICENSE", "LICENSE.md", "LICENSE.txt")
            for path in root.glob(pattern)
        ],
        "external_http_links": "Not fetched by this tool",
        "github_render": "BLOQUEADO EXTERNO (not published)",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--output", required=True)
    parser.add_argument("--skip-live-routes", action="store_true")
    parser.add_argument(
        "--run-help", action="store_true", help="Run only non-mutating parser --help commands"
    )
    args = parser.parse_args()
    result = audit(args.root, live_routes=not args.skip_live_routes, run_help=args.run_help)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "errors": result["error_count"],
                "documents": result["markdown_files"],
            }
        )
    )
    raise SystemExit(0 if result["error_count"] == 0 else 1)
