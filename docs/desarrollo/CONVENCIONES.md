# Convenciones de código, datos y revisión

Recogen contratos vigentes, no una arquitectura nueva. Aplican a contribuciones autorizadas por [CONTRIBUTING](../../CONTRIBUTING.md), sujetas a [licencia pendiente](../legal/OPCIONES_LICENCIA.md).

## Estructura y responsabilidades

- Modelos en apps/modulo/models.py; reglas críticas en servicios; formularios/vistas para interacción. No lógica de cobro en templates o JavaScript.
- URLs nombradas con namespace y templates con `{% url %}`. Mantener acción accesible desde navegación, no rutas huérfanas.
- Dependencias POS/facturación/fiscal/hardware mediante servicios acordados antes de editar consumidores.
- Una instalación por empresa, sin selección de tenant ni parámetros que cambien esta frontera.
- Propiedad explícita de archivos durante paralelo; no revertir cambios de otro propietario ni mezclar sus migraciones.

## Importes, tiempo e identidad

Usar Decimal desde cadenas y helpers de redondeo existentes; no float para cobrar o repartir IVA. Validar finitud, signo, escala y capacidad del campo antes de escribir. TicketLine usa precio con IVA y redondeo por línea; no cambiar a redondeo global sin contrato fiscal.

Usar tiempos conscientes de zona, UTC en persistencia y zona IANA de empresa en presentación/fecha fiscal. No depender de la zona del proceso. Emisor, cliente y textos impresos se congelan en Invoice: no reconstruirlos desde ajustes o catálogo mutable al reimprimir.

## Transacciones e idempotencia

Mantener unidades cortas con atomic/atomic_retry, constraints y UPDATE condicional de versión/estado. `_lock_ticket` implementa CAS, no un bloqueo fila SQLite. No depender de select_for_update para serializar en SQLite. Sin HTTP, impresión ni interacción humana dentro de la transacción de cobro.

Una operación reintentable exige clave estable/huella. Ante locked/busy se repite toda la unidad tras rollback, nunca una sentencia aislada ni transacción ya anidada. El reintento no puede repetir IO irreversible; conservar mensaje comprensible al agotar límite.

## Permisos y datos sensibles

`require_role` recarga rol/estado/auth_version del actor; las operaciones sobre usuarios recargan también al objetivo. Admin solo inferiores; Superadmin gestiona Superadmin. No decidir por is_staff, campo oculto o sesión antigua.

En HTTP, role_required y CSRF para mutación por cookie; mínimo Admin/Superadmin exige elevación. Soporte añade scope/caducidad y PII aprobada por otro Admin. El bridge de máquina usa token/lease: su exención CSRF no lo hace público.

Auditar mediante la allowlist de metadatos. No añadir dumps de request, contraseñas, tokens, PEM, PAN, XML con PII ni clientes a logs. Diagnósticos muestran medidas, no estados oficiales o «OK» inventados.

## Historia y migraciones

No CRUD genérico de ventas, pagos, movimientos confirmados, facturas, registros/transmisiones fiscales, auditoría o intención de impresión. Usar cancelación previa, rectificación/compensación posterior y transiciones válidas de cola.

No reescribir migración publicada para adaptar una instalación existente. Añadir una nueva y probar sobre copia sintética con historia, constraints/triggers y hashes/números. Un rollback de código no autoriza rollback de DB ni pérdida fiscal.

## UI y accesibilidad

Bootstrap5/HTMX locales; JavaScript orienta cambio/bloqueo visual, no confirma pago bancario. Estados con texto además de color, labels, foco, errores por campo y vacío útil. POST con CSRF y feedback. No HTML/CSS libre en ajustes; mantener opciones cerradas, escape por defecto y logo raster validado.

## Formato, documentación y commits

Ruff usa Python3.12 y longitud100 en [pyproject.toml](../../pyproject.toml). Seguir .editorconfig; preservar bytes de [AEAT](../../schemas/aeat/) y [vendor](../../static/vendor/) declarados -text por .gitattributes.

Antes de revisión: Ruff, check Django/migraciones y pruebas apropiadas. Commit con problema/resultado y evidencia. No cambiar cifras de release por un subconjunto ni publicar etiqueta por conveniencia. Actualizar [índice](../README.md), manuales/capturas y [changelog](../../CHANGELOG.md) cuando corresponda. Cifras históricas deben conservar su contexto.
