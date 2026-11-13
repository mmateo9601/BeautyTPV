# Estado de implementación

## Fase 0 — en curso
Inventario: repositorio inicial con especificación, ocho agentes y sin código. Cambio previo del usuario en PROMPT_INICIAL_CODEX.md preservado. Python 3.14.7; entorno .venv. Contratos y ADR en elaboración.

Gate F0 local: manage.py check sin incidencias; makemigrations --check --dry-run sin cambios; migración SQLite con User personalizado aplicada; pytest tests/test_bootstrap.py: 1 passed; ruff config/manage/bootstrap pasa. CI configurada (ejecución remota no verificada). Contratos y 3 ADR revisados por coordinador. Dependencias instaladas Django 5.2.19. No fiscal/hardware verificados aún.

