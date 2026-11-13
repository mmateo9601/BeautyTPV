"""Query public OSV advisories for locked Python and vendored JS versions only."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]


def scan():
    packages = []
    for line in (ROOT / "requirements.lock.txt").read_text(encoding="utf-8-sig").splitlines():
        if "==" in line and not line.startswith("#"):
            name, version = line.split("==", 1)
            packages.append({"name": name, "version": version, "ecosystem": "PyPI"})
    packages += [
        {"name": "bootstrap", "version": "5.3.8", "ecosystem": "npm"},
        {"name": "htmx.org", "version": "2.0.8", "ecosystem": "npm"},
    ]
    pending = [
        (
            index,
            {"package": {"name": p["name"], "ecosystem": p["ecosystem"]}, "version": p["version"]},
        )
        for index, p in enumerate(packages)
    ]
    for package in packages:
        package["advisories"] = []
    while pending:
        response = requests.post(
            "https://api.osv.dev/v1/querybatch",
            json={"queries": [query for _, query in pending]},
            timeout=(10, 45),
        )
        response.raise_for_status()
        results = response.json()["results"]
        if len(results) != len(pending):
            raise ValueError("Incomplete OSV batch response")
        following = []
        for (index, query), result in zip(pending, results):
            packages[index]["advisories"].extend(result.get("vulns", []))
            if result.get("next_page_token"):
                following.append((index, {**query, "page_token": result["next_page_token"]}))
        pending = following
    return {
        "source": "https://google.github.io/osv.dev/api/",
        "endpoint": "https://api.osv.dev/v1/querybatch",
        "queried_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "QUERIED",
        "packages": packages,
        "scope": "Known public advisories for these versions; not proof of absence of vulnerabilities or deployed OS security",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        report = scan()
    except Exception as error:
        report = {
            "status": "BLOCKED",
            "error_type": type(error).__name__,
            "scope": "External advisory service unavailable; not a clean scan",
        }
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "packages": len(report.get("packages", [])),
                "advisories": sum(len(p["advisories"]) for p in report.get("packages", [])),
            }
        )
    )
