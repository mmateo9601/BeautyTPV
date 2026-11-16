"""Optional local GFM/Mermaid visual check, without publishing or new product deps.

Requires an existing Node/Marked and a local, externally obtained Mermaid UMD
bundle. It serves only generated HTML, documentation images and that runtime on
loopback; Chromium aborts requests to all non-loopback destinations.
"""

import argparse
import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
STYLES = """body{margin:30px auto;padding:0 26px;max-width:1040px;color:#1f2328;background:#fff;font:16px/1.6 Arial,sans-serif}h1,h2{border-bottom:1px solid #ddd;padding-bottom:.3em}a{color:#0969da}img{max-width:100%;height:auto}pre{padding:16px;background:#f6f8fa;overflow:auto;font-size:13px}code{font-family:Consolas,monospace}table{border-collapse:collapse;display:block;max-width:100%;overflow:auto;font-size:14px}th,td{padding:7px 10px;border:1px solid #d0d7de}tr:nth-child(2n){background:#f6f8fa}.mermaid{background:white;overflow:auto}blockquote{border-left:4px solid #ddd;padding-left:18px;color:#59636e}"""
BOOT = """<script src='/runtime/mermaid.js'></script><script>
window.docResult={done:false,mermaid:0,error:null};
(async()=>{try{
const blocks=[...document.querySelectorAll('code.language-mermaid')];
for(const block of blocks){const pre=block.parentElement;pre.className='mermaid';pre.textContent=block.textContent;}
mermaid.initialize({startOnLoad:false,securityLevel:'strict',fontFamily:'Arial'});
if(blocks.length)await mermaid.run({querySelector:'.mermaid'});
window.docResult.mermaid=blocks.length;
}catch(e){window.docResult.error=String(e);}
window.docResult.done=true;})();</script>"""


def render(marked_module, mermaid, node="node"):
    from playwright.sync_api import sync_playwright

    files = sorted({*ROOT.glob("*.md"), *(ROOT / "docs").rglob("*.md")})
    documents = [
        {"path": p.relative_to(ROOT).as_posix(), "markdown": p.read_text(encoding="utf-8")}
        for p in files
    ]
    completed = subprocess.run(
        [node, str(ROOT / "scripts/render_markdown.mjs"), marked_module],
        input=json.dumps(documents),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    html = {
        d[
            "path"
        ]: "<!doctype html><html lang='es'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><style>"
        + STYLES
        + "</style><body>"
        + d["html"]
        + BOOT
        for d in json.loads(completed.stdout)
    }
    runtime = Path(mermaid).read_bytes()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            path = unquote(urlsplit(self.path).path)
            payload, mime = None, "text/html; charset=utf-8"
            if path == "/runtime/mermaid.js":
                payload, mime = runtime, "application/javascript"
            elif path.startswith("/__render__/"):
                relative = path.removeprefix("/__render__/")
                if relative in html:
                    payload = html[relative].encode("utf-8")
                else:
                    candidate = (ROOT / relative).resolve()
                    if (
                        candidate.is_relative_to(ROOT / "docs")
                        and candidate.suffix.lower() == ".png"
                        and candidate.is_file()
                    ):
                        payload, mime = candidate.read_bytes(), "image/png"
            if payload is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    results = []
    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(server.server_port)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                page.route(
                    "**/*",
                    lambda route: (
                        route.continue_()
                        if route.request.url.startswith(base + "/")
                        else route.abort()
                    ),
                )
                for path in html:
                    page.goto(base + "/__render__/" + path, wait_until="networkidle")
                    page.wait_for_function(
                        "window.docResult && window.docResult.done", timeout=30000
                    )
                    status = page.evaluate("window.docResult")
                    missing = page.locator("img").evaluate_all(
                        "images=>images.filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.getAttribute('src'))"
                    )
                    status.update(
                        {
                            "document": path,
                            "broken_images": missing,
                            "images": page.locator("img").count(),
                        }
                    )
                    results.append(status)
                    if path == "README.md":
                        page.screenshot(
                            path=str(ROOT / "docs/evidence/documentation-readme-render.png")
                        )
                    if path == "docs/manuales/GUIA_USUARIO.md":
                        page.screenshot(
                            path=str(ROOT / "docs/evidence/documentation-manual-render.png")
                        )
                browser.close()
        finally:
            server.shutdown()
            thread.join(timeout=5)
    evidence = {
        "scope": "Local GFM via external Marked and Mermaid UMD 11.12.2; not the remote GitHub renderer",
        "product_dependencies_added": False,
        "network": "Loopback only during render",
        "documents": results,
        "errors": sum(bool(r["error"] or r["broken_images"]) for r in results),
    }
    (ROOT / "docs/evidence/documentation-render.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--marked-module",
        required=True,
        help="Existing Marked ESM module path or resolvable module name",
    )
    parser.add_argument(
        "--mermaid-js",
        required=True,
        help="Local Mermaid UMD bundle, not downloaded by this command",
    )
    parser.add_argument("--node", default="node")
    args = parser.parse_args()
    result = render(args.marked_module, args.mermaid_js, args.node)
    print(json.dumps({"documents": len(result["documents"]), "errors": result["errors"]}))
    raise SystemExit(1 if result["errors"] else 0)
