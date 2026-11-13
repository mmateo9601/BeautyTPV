"""Inventory implementation metadata only; existence never implies verification."""

import argparse
import ast
import inspect
import json
import os
import re
import sys
from pathlib import Path


def inventory(root, output):
    sys.path.insert(0, str(root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.apps import apps
    from django.urls import URLResolver, get_resolver

    result = {"routes": [], "models": [], "functions": [], "templates": [], "commands": []}

    def visit(patterns, prefix="", namespaces=()):
        for pattern in patterns:
            route = prefix + str(pattern.pattern)
            if isinstance(pattern, URLResolver):
                visit(
                    pattern.url_patterns,
                    route,
                    namespaces + ((pattern.namespace,) if pattern.namespace else ()),
                )
                continue
            view = inspect.unwrap(pattern.callback)
            source = inspect.getsource(view)
            minimum = re.search(r'role_required\(["\x27](\w+)', source)
            limited = re.search(r"@require_http_methods\(\[(.*?)\]\)", source, re.S)
            methods = (
                ["POST"]
                if "@require_POST" in source
                else ["GET"]
                if "@require_GET" in source
                else re.findall(r"[\"']([A-Z]+)[\"']", limited.group(1))
                if limited
                else ["UNRESTRICTED"]
            )
            role = (
                minimum.group(1)
                if minimum
                else (
                    "BRIDGE_BEARER"
                    if "authenticated_terminal(" in source
                    else "AUTHENTICATED"
                    if "@login_required" in source
                    else "PUBLIC"
                )
            )
            result["routes"].append(
                {
                    "route": "/" + route,
                    "name": ":".join((*namespaces, pattern.name or "<unnamed>")),
                    "view": f"{view.__module__}.{view.__name__}",
                    "source": str(Path(inspect.getsourcefile(view)).relative_to(root)).replace(
                        "\\", "/"
                    ),
                    "line": inspect.getsourcelines(view)[1],
                    "minimum_role": role,
                    "elevated": bool(re.search(r"elevated\s*=\s*True", source))
                    or bool(minimum and minimum.group(1) in ("ADMIN", "SUPERADMIN")),
                    "methods": methods,
                    "csrf_exempt": "@csrf_exempt" in source,
                    "templates": sorted(set(re.findall(r'["\x27]([\w/.-]+\.html)["\x27]', source))),
                    "authorization_calls": sorted(set(re.findall(r"\b(require_\w+)\(", source))),
                }
            )

    visit(get_resolver().url_patterns)
    for model in apps.get_models():
        if not model.__module__.startswith("apps."):
            continue
        result["models"].append(
            {
                "model": model._meta.label,
                "table": model._meta.db_table,
                "fields": [
                    {
                        "name": f.name,
                        "type": f.get_internal_type(),
                        "null": f.null,
                        "unique": f.unique,
                        "related_model": f.related_model._meta.label if f.related_model else None,
                    }
                    for f in model._meta.local_fields
                ],
                "constraints": [str(c) for c in model._meta.constraints],
            }
        )
    for directory in ("apps", "scripts"):
        for path in sorted((root / directory).rglob("*.py")):
            if "migrations" in path.parts or "__pycache__" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result["functions"].append(
                        {
                            "file": path.relative_to(root).as_posix(),
                            "name": node.name,
                            "line": node.lineno,
                            "decorators": [ast.unparse(d) for d in node.decorator_list],
                        }
                    )
            if "commands" in path.parts or directory == "scripts":
                result["commands"].append(path.relative_to(root).as_posix())
    for path in sorted((root / "templates").rglob("*.html")):
        content = path.read_text(encoding="utf-8")
        result["templates"].append(
            {
                "file": path.relative_to(root).as_posix(),
                "named_links": sorted(set(re.findall(r"\{%\s*url\s+[\"']([^\"']+)[\"']", content))),
                "literal_links": sorted(set(re.findall(r'(?:href|action)="(/[^"{}]*)"', content))),
                "forms": len(re.findall(r"<form\b", content)),
                "htmx": re.findall(r'hx-(?:get|post|put|delete|patch)="([^"]+)"', content),
            }
        )
    output.mkdir(parents=True, exist_ok=True)
    (output / "inventory.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Inventario de implementación",
        "",
        "Existencia no equivale a requisito COMPLETO. Sin datos del negocio.",
        "",
        f"{len(result['routes'])} rutas; {len(result['models'])} modelos; {len(result['functions'])} funciones/métodos; {len(result['templates'])} plantillas.",
        "",
        "## Rutas, vistas y controles declarados",
        "",
        "| Ruta | Nombre | Vista | Rol mínimo | Elevación | Métodos | Plantillas |",
        "|---|---|---|---|---|---|---|",
    ]
    for route in result["routes"]:
        lines.append(
            "| "
            + " | ".join(
                str(value)
                for value in (
                    route["route"],
                    route["name"],
                    route["view"],
                    route["minimum_role"],
                    route["elevated"],
                    ", ".join(route["methods"]),
                    ", ".join(route["templates"]),
                )
            )
            + " |"
        )
    lines += [
        "",
        "## Modelos",
        "",
        "| Modelo | Tabla | Campos | Restricciones |",
        "|---|---|---|---|",
    ]
    for model in result["models"]:
        lines.append(
            f"| {model['model']} | {model['table']} | "
            + ", ".join(f["name"] + ":" + f["type"] for f in model["fields"])
            + " | "
            + "; ".join(model["constraints"])
            + " |"
        )
    lines += [
        "",
        "## Servicios y métodos",
        "",
        "| Archivo | Función | Línea | Decoradores |",
        "|---|---|---|---|",
    ]
    for function in result["functions"]:
        lines.append(
            f"| {function['file']} | {function['name']} | {function['line']} | "
            + ", ".join(function["decorators"])
            + " |"
        )
    lines += [
        "",
        "## Plantillas y conexiones",
        "",
        "| Plantilla | Forms | URLs nombradas | Enlaces literales | HTMX |",
        "|---|---|---|---|---|",
    ]
    for template in result["templates"]:
        lines.append(
            "| "
            + " | ".join(
                str(v)
                for v in (
                    template["file"],
                    template["forms"],
                    ", ".join(template["named_links"]),
                    ", ".join(template["literal_links"]),
                    ", ".join(template["htmx"]),
                )
            )
            + " |"
        )
    (output / "INVENTARIO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: len(value) for key, value in result.items()}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--output", required=True)
    arguments = parser.parse_args()
    inventory(Path(arguments.root).resolve(), Path(arguments.output).resolve())
