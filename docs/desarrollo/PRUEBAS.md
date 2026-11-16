# Pruebas y evidencias

La suite verifica negocio y seguridad además de rutas/archivos. El resultado vigente Fase11 se registra en [DOCUMENTATION_AUDIT](../DOCUMENTATION_AUDIT.md) y [RELEASE_REPORT](../RELEASE_REPORT.md). No atribuir ejecución nueva a cifras históricas.

## Gate ordinario

Desde raíz y entorno preparado:

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
.venv\Scripts\python.exe -m pytest -q
```

Makemigrations check comprueba deriva sin crear archivos, no sustituye migrate sobre DB de prueba con datos previos. Pytest-django gestiona DB de tests: nunca usar DB comercial como fixture ni reuse-db sin comprender su ubicación.

Para JUnit:

```powershell
.venv\Scripts\python.exe -m pytest -q --junitxml=docs/evidence/phase11-tests.xml -o junit_family=xunit1
```

Revisar XML/capturas antes de publicar; pueden contener fixtures/errores. No poner credenciales reales en assertions/dumps. Un PASS parametrizado no equivale a una función completa.

## Capas de verificación

| Capa | Archivos reales | Demostración |
|---|---|---|
| Negocio | [backend](../../tests/test_backend.py), [aceptación](../../tests/test_acceptance.py) | Totales/IVA/pagos/caja/transiciones/compensación |
| Formularios | [HTTP positivos](../../tests/test_audit_forms.py), [consolidación](../../tests/test_consolidation_backend.py) | Validación, guardado y recuperación de DB |
| Seguridad | [base](../../tests/test_security.py), [auditoría](../../tests/test_audit_security.py), [sesiones](../../tests/test_consolidation_security.py) | Jerarquía actual, elevación, invalidación, PII |
| Todas las rutas | [matriz](../../tests/test_audit_matrix.py) | Cuatro roles, objetos reales, CSRF; POST inválido no acredita éxito |
| Fiscal | [vectores/XSD](../../tests/test_fiscal.py), [regresiones](../../tests/test_audit_fiscal.py) | Hash, snapshot, leases/espera, parser y respuestas sintéticas |
| Hardware | [base](../../tests/test_hardware.py), [bridge](../../tests/test_audit_hardware.py) | Bytes/routing/retry/TCPloopback/UNKNOWN; sin papel físico |
| Procesos/recuperación | [concurrencia](../../tests/test_concurrency.py), [backup](../../tests/test_backup.py), [operaciones](../../tests/test_audit_ops.py) | Dobles cobros, caída antes commit, restore y rollback seguro |
| DEMO Windows | [lanzador](../../tests/test_windows_demo.py), [servidor](../../tests/test_demo_server.py), [perfil](../../tests/test_demo_profile.py) | Aislamiento/hardlinks/procesos, protocolo y límites de transporte |
| Navegador | [E2E](../../tests/e2e/) | Controles de persona contra servidor/SQLite temporales |

Una negativa debe acompañarse de una válida con efecto en DB. Probar servicios también sin request. No considerar404 prueba de autorización ni400 prueba de éxito.

## Subconjuntos y E2E

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_consolidation_acceptance.py tests/test_audit_matrix.py
.venv\Scripts\python.exe -m pytest -q tests/test_fiscal.py tests/test_audit_fiscal.py
.venv\Scripts\python.exe -m pytest -q tests/test_demo_server.py tests/test_demo_profile.py
.venv\Scripts\python.exe -m playwright install chromium
.venv\Scripts\python.exe -m pytest -q tests/e2e --browser chromium
```

[centre_server](../../tests/e2e/test_browser.py) prepara SQLite temporal, servidor loopback en puerto libre y datos sintéticos. Limpia solo procesos que crea. Usa runserver de pruebas, no producción. DEMO habitual puede seguir en8000: los E2E eligen otros puertos.

Sandboxes pueden impedir TCP local, Chromium o hardlinks. Distinguir fallo de aplicación de restricción del entorno, solicitar ejecución autorizada cuando corresponda y registrar exactamente lo ejecutado. No quitar assertions ni crear skips generales para ocultar errores.

## Auditoría documental y capturas

```powershell
.venv\Scripts\python.exe scripts\audit_documentation.py --output docs/evidence/documentation-audit.json --run-help
.venv\Scripts\python.exe scripts\license_inventory.py --verify
.venv\Scripts\python.exe scripts\capture_documentation.py
```

El auditor comprueba enlaces, anclas, rutas, imágenes, hashes y ayuda de comandos; no ejecuta operaciones destructivas ni certifica permisos por resolver una URL. La captura prepara una instancia temporal independiente, con datos sintéticos y fiscal TEST sin remisión. No reutiliza la DEMO habitual ni sus credenciales.

La comprobación visual opcional usa `scripts/render_documentation.py --marked-module <ruta-a-marked.esm.js> --mermaid-js <ruta-a-mermaid.min.js>`. Requiere Node, Marked y Mermaid ya disponibles externamente; no añade dependencias del producto ni los descarga automáticamente. Sirve HTML solo en loopback y bloquea peticiones externas del navegador. La evidencia local está en [documentation-render.json](../evidence/documentation-render.json), con procedencia del runtime en [documentation-render-runtime.json](../evidence/documentation-render-runtime.json). No acredita el renderizador remoto de GitHub.

## Validación de plataforma

[ci.yml](../../.github/workflows/ci.yml) declara Ubuntu/Python3.12. No hay ejecución remota atribuida a esta fase. Parte del lanzador usa WinAPI/eventos y varias fixtures solo funcionan en Windows: no inferir suite Windows verde en Ubuntu por existir un workflow. Revisar matriz/marcadores antes de aprobar CI como gate; estos documentos no modifican ni desactivan pruebas. No afirmar Windows10 físico cuando solo se probó Windows11.

## Operaciones y carga sintéticas

Scripts existentes para entornos temporales, no para un negocio activo:

```powershell
.venv\Scripts\python.exe scripts\audit_upgrade_recovery.py --output docs/evidence/upgrade-recovery-local.json
.venv\Scripts\python.exe scripts\benchmark_sqlite.py --terminals 1 3 6 --operations 10 --output docs/evidence/sqlite-carga-local.json
```

El primero comprueba migración histórica, instalación y CLI backup/restore; el segundo mide carga local. No certifican capacidad sostenida/LAN/conciliación AEAT. Leer argumentos y revisar salida antes de publicar. Tras gate verde, ampliar/repetir solo por cambios, fallos o riesgos concretos.

**Verificado localmente** exige comando ejecutado/evidencia; **preparado** no atribuye ejecución pendiente; **bloqueado externo** distingue certificado/acuse/firma/hardware/destino/personas/CI remota. Capturas DEMO no sustituyen permisos ni conformidad. Véase [proceso de release](../../RELEASE_PROCESS.md).
