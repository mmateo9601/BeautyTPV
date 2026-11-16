# Versionado y distribución controlada

La versión declarada es `0.1.0` en [pyproject.toml](pyproject.toml). La interfaz obtiene versión de `release.json` cuando existe y, si no, de los metadatos instalados mediante `apps.support.versioning.application_version`. Esta fase no inventa una versión estable, no crea tags ni publica releases.

## Antes de preparar un candidato

1. Revisar el [estado de aceptación](docs/FINAL_ACCEPTANCE.md), [reporte de release](docs/RELEASE_REPORT.md), [auditoría documental](docs/DOCUMENTATION_AUDIT.md) y los cambios desde la revisión anterior.
2. Definir titular/licencia y autorización de distribución. Revisar [avisos de terceros](THIRD_PARTY_NOTICES.md), componentes nativos/fuentes y artefactos concretos. Mientras no se resuelva, no presentar el paquete como legalmente listo para distribución pública.
3. Ejecutar en el entorno preparado:

   ```powershell
   .venv\Scripts\python.exe manage.py check
   .venv\Scripts\python.exe manage.py makemigrations --check --dry-run
   .venv\Scripts\python.exe -m pytest -q
   .venv\Scripts\python.exe -m ruff check .
   .venv\Scripts\python.exe -m ruff format --check .
   .venv\Scripts\python.exe -m pip check
   ```

4. Probar migraciones sobre una copia aislada con historial emitido, integridad, cadena, backup/restore/hold y rollback de código. Nunca usar la base activa para ensayar restauraciones.
5. Revisar seguridad, permisos, scopes, credenciales, datos sintéticos de capturas y ausencia de secretos. La CI remota no se considera aprobada por existir un YAML.
6. Actualizar documentación/capturas, ejecutar sus verificadores y revisar visualmente. Mantener metadatos/`CHANGELOG.md` y registro de evidencias coherentes.

   ```powershell
   .venv\Scripts\python.exe scripts\license_inventory.py
   .venv\Scripts\python.exe scripts\license_inventory.py --verify
   .venv\Scripts\python.exe scripts\capture_documentation.py
   .venv\Scripts\python.exe scripts\audit_documentation.py --output docs/evidence/documentation-audit.json
   ```

El inventario de licencias utiliza paquetes ya instalados del lock. `--fetch-missing` es una operación opt-in limitada al aviso upstream fijado de pySerial; la verificación habitual no necesita red. Las capturas usan una DEMO temporal independiente, no la DEMO del usuario en8000.

## Paquete de actualización existente y sus límites

`scripts/package_release.py` construye un ZIP con `release.json`, versión y SHA256 de cada archivo permitido:

```powershell
.venv\Scripts\python.exe scripts\package_release.py --version 0.1.0 --output dist/BeautyTPV-0.1.0.zip
```

Ese comando genera un candidato local; no publica nada. La allowlist actual está en `apps/support/updates.py::ALLOWED_TOP_LEVEL`. Incluye aplicaciones, configuración, scripts, plantillas, estáticos, esquemas, tests y `docs/`; **no es una exportación completa del repositorio ni un instalador de doble clic**. Los BAT/PS de raíz y los nuevos documentos profesionales de raíz no forman parte de esa allowlist actual. No distribuirlo como si incluyera todos los accesos/documentos del repositorio.

Antes de una distribución completa, revisar y aprobar expresamente la lista de archivos, la presencia de avisos/licencia/documentos y el procedimiento de instalación. Esta fase documental conserva el comportamiento de la herramienta; no amplía silenciosamente su permiso de escritura. La licencia del producto pendiente sigue siendo un gate separado.

## Ensayo y aprobación del candidato

1. Preparar un directorio de ensayo con instancia sintética y secretos externos. Validar ZIP, hashes, versión y dependencias antes de aplicarlo.
2. Detener servicio y workers, tomar backup cifrado y aplicar con `scripts/update.ps1` o `scripts/update.py --offline`, conforme a [ACTUALIZACIONES](docs/instalacion/ACTUALIZACIONES.md).
3. Verificar migraciones, estáticos, integridad, flujos E01–E16 locales y colas. El rollback automático es de código; no retrocede datos fiscales ni resuelve un venv incompatible.
4. Adjuntar resultados, bloqueos externos y aceptación de responsables. AEAT oficial, declaración responsable suscrita y pruebas físicas no se sustituyen con simuladores.
5. Con aprobación explícita del propietario, decidir una versión, tag y publicación controlada. No se ejecutan esos pasos automáticamente en esta fase.
6. Para instalar en una empresa, backup previo, ventana de mantenimiento, controles TLS/ACL/firewall y validación humana del equipo destino. Registrar responsable, versión instalada y procedimiento de recuperación.

No publicar certificados, credenciales, bases, backups, rutas privadas ni logs crudos. Un hash o una suite verde acredita lo comprobado, no la autorización legal, la conformidad fiscal ni una prueba física inexistente.
