# Guía del desarrollador

BeautyTPV0.1.0 es Django local por empresa. El número de versión no declara release fiscal productiva. Antes de colaborar, lea [CONTRIBUTING](../../CONTRIBUTING.md), [arquitectura](../arquitectura/ARQUITECTURA.md), [modelos](../arquitectura/MODELOS_DATOS.md), [flujos](../arquitectura/FLUJOS_NEGOCIO.md) y [licencia AGPLv3](../legal/OPCIONES_LICENCIA.md).

## Incorporarse

1. Obtenga el código del repositorio de referencia y cumpla AGPLv3. El comando no garantiza que todos los commits locales hayan sido publicados:

   ```powershell
   git clone https://github.com/mmateo9601/BeautyTPV.git BeautyTPV
   Set-Location BeautyTPV
   ```

2. Prepare Python y DB independiente según [Entorno](ENTORNO_DESARROLLO.md); nunca pruebe sobre datos comerciales.
3. Ejecute check, revisión de migraciones, pytest y Ruff según [Pruebas](PRUEBAS.md).
4. Recorra DEMO/manuales para comprender la operación antes de cambiar reglas de cobro.
5. Use rama aislada y [Convenciones](CONVENCIONES.md). No publique tags/releases automáticamente.

## Dónde trabajar

| Objetivo | Archivos de entrada |
|---|---|
| Acceso/jerarquía/sesiones | [accounts](../../apps/accounts/) y su middleware |
| Empresa/terminal | [core](../../apps/core/), forms/services |
| Plano/puestos | [layout](../../apps/layout/) y [POS views](../../apps/pos/views.py) |
| Catálogo/clientes | [catalog](../../apps/catalog/) y [customers](../../apps/customers/) |
| Carrito/cobro/caja | [pos/services.py](../../apps/pos/services.py), [cash/services.py](../../apps/cash/services.py) |
| Documentos/registros | [billing](../../apps/billing/), [verifactu](../../apps/verifactu/) con contrato fiscal |
| Dispositivos/colas | [hardware](../../apps/hardware/) |
| Soporte/operaciones | [support](../../apps/support/) y [scripts](../../scripts/) |
| UI | [templates](../../templates/), [static](../../static/); Bootstrap5 y HTMX locales |
| Evidencia | [tests](../../tests/) y [E2E](../../tests/e2e/) |

Reports consulta registros autorizados; no duplica ventas. La lógica transaccional vive en servicios, no en templates/JavaScript. Una operación necesita servicio, permisos backend, formulario/vista, navegación, auditoría cuando corresponda y pruebas positivas/negativas.

## Ciclo de cambio

1. Describa problema reproducible, actor, efecto esperado y límites; asigne propietario y pacte contratos cruzados.
2. Lea modelo/servicio/tests y distinga configuración mutable de historia que exige compensación.
3. Añada una regresión significativa con DB temporal, datos sintéticos y transportes externos controlados.
4. Implemente el cambio mínimo respetando Decimal, permisos actuales, CAS e idempotencia. Una modificación de modelo exige migración compatible con historia y triggers.
5. Conecte la acción desde UI autorizada. Compruebe mensajes, loading, errores, móvil y enlaces.
6. Ejecute comprobaciones apropiadas; registre comando/resultado real/limitación. Un archivo o botón no acredita COMPLETO.
7. Actualice manuales, índice, matrices y capturas afectados. No publicar secretos ni datos personales.
8. Commit/PR centrado en problema, solución, pruebas y riesgo real. No borrar historia fiscal ni reducir assertions para obtener verde.

## Frontera de seguridad de los servicios

`checkout`, `save_register`, `save_company_settings` y `update_user` reciben actor y verifican estado/rol persistidos. Una vista usa `role_required`: mínimo Admin/Superadmin exige elevación. No autorizar por is_staff, botón oculto o una sesión obsoleta. Superadmin comercial necesita PII con otro aprobador activo.

Una tarea de sistema no falsifica usuarios web: workers tienen entrypoints/locks controlados. Servicios administrativos sin request verifican rol/alcance; la elevación se aplica en la entrada HTTP. Documente identidad y frontera de cualquier comando nuevo.

No hay SaaS, tenants, portal Cliente, agenda, reservas ni bonos V1. Tarjeta solo registra confirmación externa. PostgreSQL es futuro, no motor ya validado. El escenario fiscal no debe ampliarse ni pasar a producción por una prueba sintética. Véase [Extensiones](EXTENSIONES.md).
