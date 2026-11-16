# Contribuir a BeautyTPV

BeautyTPV se ofrece bajo [GNU AGPLv3, únicamente versión 3](LICENSE), identificada como `AGPL-3.0-only`. Al enviar una contribución para incorporarla al proyecto, ofrézcala bajo esa misma licencia y confirme que dispone de los derechos necesarios. Conserve avisos de terceros y declare dependencias nuevas. Los autores conservan sus derechos: no se establece una cesión de titularidad ni un CLA implícito. Consulte [código fuente y alcance](SOURCE_CODE.md) y [avisos de terceros](THIRD_PARTY_NOTICES.md).

## Proponer mejoras

1. Cree un fork o una rama del [repositorio original](https://github.com/mmateo9601/BeautyTPV).
2. Prepare un cambio concreto, con pruebas apropiadas y documentación actualizada.
3. Abra una pull request explicando el problema, la solución y las verificaciones realizadas. Para vulnerabilidades siga el canal privado de [SECURITY](SECURITY.md).
4. Atienda la revisión; el mantenedor decide si incorpora el cambio.

Enviar mejoras al repositorio original es recomendado, no obligatorio por AGPLv3. Compartir el código correspondiente cuando la licencia lo exige no depende de presentar ni de que se acepte una PR. No incluya datos de clientes, claves, certificados ni bases de instalaciones.

## Preparar el trabajo

1. Lea [AGENTS.md](AGENTS.md), [PLAYBOOK.md](PLAYBOOK.md), [guía de desarrollador](docs/desarrollo/GUIA_DESARROLLADOR.md) y las convenciones aplicables.
2. Describa problema, alcance V1, módulo propietario y evidencia antes de editar; confirme interfaces antes de trabajo paralelo.
3. Utilice una rama o copia aislada. Una rama nueva puede seguir `codex/<descripcion>`; no reescriba historial ajeno ni elimine datos para facilitar migraciones.
4. Use una DEMO independiente con datos sintéticos, sin certificados ni remisión fiscal. No utilice la SQLite principal ni la DEMO personal de otro usuario como fixture de desarrollo.

## Garantías que debe conservar un cambio

- Instalación local por empresa, sin tenants/SaaS; SQLite en disco local y sin SMB/NFS.
- Plano inicial, cuentas persistentes, una cuenta activa por puesto, idempotencia y numeración consistente.
- Inmutabilidad de documentos/ventas/cobros/movimientos/auditoría; compensaciones o rectificaciones válidas en lugar de CRUD histórico.
- Rol/actividad actuales comprobados en backend, elevación HTTP y scopes independientes cuando corresponden. No basta esconder botones.
- Estados fiscales y de impresión honestos; no respuestas AEAT inventadas, no falso DONE físico ni reenvío automático de UNKNOWN.
- Secretos fuera del repositorio y datos de tarjetas fuera de notas/referencias. No generar credenciales fijas para facilitar pruebas.

Cambiar alcance fiscal, dependencias, esquema o permisos exige justificación, revisión especializada y pruebas. No añadir portal Cliente, agenda, reservas o bonos como parte silenciosa de V1.

## Validar y presentar

Desde el entorno virtual preparado, ejecute los controles correspondientes al cambio:

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
```

Las pruebas de navegador requieren Chromium instalado según [PRUEBAS](docs/desarrollo/PRUEBAS.md). Las pruebas de Windows/hardlinks o red local necesitan permisos de ejecución adecuados; registre un bloqueo real en vez de declararlas pasadas. No reduzca aserciones, añada omisiones o quite pruebas para ocultar un fallo.

Incluya en el cambio: problema y comportamiento final, archivos/migraciones, prueba positiva y negativa pertinente, comandos y resultados reales, capturas sintéticas si cambia UI y límites externos. Actualice los manuales, [CHANGELOG](CHANGELOG.md) y el estado de implementación si procede. Las capturas deben proceder de la aplicación real, con texto alternativo y sin secretos.

Haga commits por módulo/fase verificable. No publique tags, paquetes o releases sin seguir [RELEASE_PROCESS](RELEASE_PROCESS.md) y autorización del responsable. Para vulnerabilidades utilice [SECURITY](SECURITY.md), no un reporte público con detalles sensibles. Para participación y trato siga [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md).
