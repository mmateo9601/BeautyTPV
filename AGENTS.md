# Instrucciones persistentes — BeautyTPV

Lee `PLAYBOOK.md` antes de modificar código. Construye una aplicación funcional de TPV para estética, **una instalación por empresa**, Django + Bootstrap + HTMX + **SQLite inicialmente**. No SaaS ni multiempresa.

## Reglas permanentes
- El plano de puestos es el inicio; cuentas abiertas persistentes; ventas y facturación inmutables tras emitir.
- Roles: Empleado < Encargado < Administrador < Superadmin; Cliente es externo/futuro, sin portal en V1.
- El Superadmin debe tener panel funcional de soporte, hardware, diagnóstico, backup, restauración, versiones, dispositivos, colas fiscales y auditoría.
- No implementar facturación VERI*FACTU de forma aproximada: usar especificaciones oficiales vigentes, XSD/WSDL, pruebas de integración y reporte de evidencias.
- SQLite: transacciones cortas, idempotencia, resistencia a múltiples terminales, no `select_for_update` como mecanismo de serialización de filas.
- Hardware: implementar bridge ESC/POS/cajón y simulador; no afirmar pruebas físicas sin dispositivos.
- Seguridad: PIN hash, rate limiting, permisos backend, auditoría, no credenciales por defecto, secrets fuera del repo, no almacenar datos de tarjetas.
- Tests de servicio + navegador y migraciones por cada módulo; registro en `docs/IMPLEMENTATION_STATUS.md`.
- El cierre exige `docs/RELEASE_REPORT.md` con criterios verificables y bloqueos honestos.

## Delegación obligatoria
Usa subagentes `.codex/agents/{architect,backend,frontend,fiscal,hardware,security,qa,devops}.toml`. Arquitecto define interfaces antes de tareas paralelas. No asignar a dos agentes modificaciones simultáneas del mismo archivo. Principal integra, prueba y corrige.

## Comandos de control (cuando estén instalados)
`python manage.py check`, `python manage.py makemigrations --check --dry-run`, `pytest -q`, `ruff check .`, `ruff format --check .`, tests e2e y verificaciones de instalación/restore.
