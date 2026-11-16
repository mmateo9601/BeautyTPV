# Ampliar BeautyTPV sin romper contratos

V1 no incluye portal Cliente, agenda, reservas ni bonos. Son posibilidades futuras, no módulos disponibles. PostgreSQL tampoco está validado como motor actual. Este documento guía cambios autorizados; no amplía fiscalidad por un ejemplo.

## Antes de diseñar

1. Trace requisito a operación, actor, pantalla y dato persistente. Revise [modelos](../arquitectura/MODELOS_DATOS.md), [flujos](../arquitectura/FLUJOS_NEGOCIO.md) y [permisos](../ROLE_PERMISSION_MATRIX.md).
2. Distinga configuración editable, estado de trabajo e historia emitida. Defina transición/compensación cuando CRUD no sea legal o funcional.
3. Identifique módulo y consumidores. Pacte firma, errores, idempotencia y auditoría antes del paralelo.
4. Prepare positiva/negativa y caso de actor/objeto obsoleto si depende de rol, actividad o configuración mutable.

## Campo o modelo nuevo

- Elegir tipo/límites acordes al negocio; DecimalField para importes y validación de escala/finitud. Valorar PROTECT en relaciones históricas.
- Defaults/nullability compatibles con datos existentes y constraints para invariantes expresables en DB.
- No borrar/renombrar historia para simplificar formularios. Backfill solo con evidencia; desconocidos deben advertirse.
- Revisar rebuild de tablas SQLite y triggers: un campo o tabla nuevos no heredan por sí solos protección de documentos emitidos.

En una DB DEV aislada:

```powershell
.venv\Scripts\python.exe manage.py makemigrations <nombre_app>
.venv\Scripts\python.exe manage.py sqlmigrate <nombre_app> <numero_migracion>
.venv\Scripts\python.exe manage.py migrate --noinput
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Sustituir placeholders por la app/migración real. Probar upgrade sobre copia sintética con documentos emitidos; comparar historia, huellas y números antes/después.

## Operación administrativa

Patrones existentes: [catalog/services.py](../../apps/catalog/services.py) y [layout/views.py](../../apps/layout/views.py).

1. Servicio recibe actor, verifica require_role con mínimo explícito, valida datos y muta en transacción corta.
2. Audita metadatos filtrados y devuelve resultado real; errores comprensibles, sin secretos.
3. Vista exige rol/elevación y formulario, llama al servicio. No shell arbitrario ni rutas de DB proporcionadas por cliente.
4. Ruta nombrada, enlace autorizado, template con CSRF/feedback y confirmación de operaciones destructivas permitidas.
5. Pruebas del servicio sin request, HTTP válido/denegado, CSRF y persistencia. Toda ruta nueva requiere política en [test_audit_matrix.py](../../tests/test_audit_matrix.py).

No copiar este patrón para editar una factura: necesita una operación fiscal válida y revisión especializada.

## Interacción HTMX

Usar [pos/floor.html](../../templates/pos/floor.html) como referencia. Conservar ruta funcional, HTML válido y filtros al refrescar. Tratar409 de versión y fallos de red. Bloquear visualmente doble envío complementa la idempotencia/CAS; no la sustituye.

Probar escritorio/tablet/estrecho, roles y enlaces visibles. No simular persistencia con variables de navegador o estados fake.

## Prueba E2E nueva

1. Fixture de servidor/SQLite temporal como [centre_server](../../tests/e2e/test_browser.py); limpiar solo recursos creados por la prueba.
2. Preparar precondiciones; la acción probada debe usar controles de persona.
3. Autenticar PIN/contraseña según rol y conseguir elevación/scopes sin desactivar middleware.
4. Comprobar UI y DB, no solo HTTP.404 no demuestra autorización;400 no demuestra éxito.
5. Capturar datos sintéticos, sin secretos y con viewport definido; actualizar manuales con pantallas reales.

## Cambios fiscales, hardware y operación

Fiscalidad exige fuente oficial, XSD/WSDL, vectores, identidad/encadenamiento, acuses y revisión externa antes de producción. Un nuevo impuesto en catálogo no implementa por sí solo un régimen no soportado.

Hardware conserva intención y UNKNOWN: no equiparar TCP exitoso con papel ni reintentar automáticamente entrega incierta. Copia nunca abre cajón. Operaciones técnicas mantienen lock, backup previo y rollback de código sin reescribir historia fiscal.

PostgreSQL futuro requiere portar constraints, triggers, idempotencia, locks y pruebas de datos; portabilidad de intención no es certificación del motor. [SQLite](../integraciones/SQLITE.md) documenta el estado presente.

## Cerrar el cambio

Verificar servicio→HTTP→UI→DB, roles y efectos colaterales; ejecutar pruebas adecuadas y revisar migraciones, logs y documentación. Registrar límites externos. No crear tags/releases automáticamente: seguir [RELEASE_PROCESS](../../RELEASE_PROCESS.md).
