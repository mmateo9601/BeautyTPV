# Consolidación backend: ajustes, catálogo, plano y caja

Implementación sobre la auditoría existente, sin reconstruir ni borrar historial. Propiedad core/catalog/layout/cash/pos; plantillas frontend e integración fiscal pertenecen a otros agentes.

## Ajustes de empresa

`core:settings` ofrece categorías `?section=commercial|fiscal|pos`; GET sin parámetro abre Salón. POST sin parámetro conserva el formulario legacy. Cada formulario guarda solo su subconjunto mediante `apps.core.services.save_company_settings(actor,data,logo=None,remove_logo=False)`, con ADMIN persistido y elevación en HTTP. Añade nombre/domicilio comercial, teléfono/correo/pie futuro y preferencias allowlist: tema salvia/océano, densidad, contraste y sección inicial. Inicio obligatorio sigue siendo plano. `currency` se valida como EUR en modelo/servicio. NIF e instalación no se pueden cambiar tras primera factura; nombres/domicilio/series solo afectan futuras emisiones.

`core:logo_save` es POST elevado y `core:logo` GET interno. Imagen PNG/JPEG/WebP <=2MiB, <=16M píxeles, convertida a PNG RGBA <=600x600 y <=256KiB, sin SVG/HTML/URL externa ni metadatos originales. Almacenada en SQLite e incluida en backup, entregada como PNG/nosniff/private no-store. Retirada explícita. El logo no se aplica retrospectivamente a documentos.

## Catálogo y plano

Category agrega orden y visibilidad TPV; CatalogItem agrega orden. Ocultar una categoría excluye artículos de búsqueda/lista y del servicio de adición por ID, sin borrar líneas previas. Servicios `save_catalog_item`, `save_category`, `delete_category` exigen ADMIN también sin petición HTTP. Formularios preservan compatibilidad de entradas antiguas que no contenían nuevos campos. Listado filtra q/tipo/activo/categoría.

Station agrega orden. `save_station` impide desactivar o reasignar sección cuando tiene cuenta activa; `save_section`, `delete_station`, `delete_section` protegen rango e historial. Listado filtra q/sección/actividad. Sección preferida de terminal tiene precedencia sobre empresa y puede anularse seleccionando todas. Preferencias nunca abren automáticamente una cuenta.

## Caja y terminal

CashRegister agrega active y terminal nullable protegida. `cash:registers`, `cash:register_create` y `cash:register_edit` permiten consultar/buscar/filtrar/crear/editar/desactivar. `save_register` exige ADMIN; recarga terminal de DB para no confiar en objeto obsoleto y rechaza desactivación o reasignación con turno abierto. No se elimina historial ni se editan movimientos sellados. Apertura conserva EMPLOYEE autorizado previamente, decisión explícita del coordinador; movimientos/cierre siguen MANAGER.

Terminal agrega sección y caja predeterminadas. Su validación recarga la caja actual y exige activa y compartida o propia. El TPV propone solo sesiones activas compartidas/de esa terminal; selección preferida no cambia permisos. Checkout valida estado actual y asignación; no cambia pagos anteriores ni numeración. Filtros con identificadores extremos usan form_pk y responden400.

## Evidencias y límites

`tests/test_consolidation_backend.py`: pruebas de servicios y HTTP positivas/negativas, ajustes parciales, identidad fiscal, EUR/temas/zona/correo, normalización y acceso al logo, categorías ocultas, orden, puesto abierto, caja inactiva/abierta, CRUD caja, preferencias reales y filtros extremos. Suite integrada dirigida con `test_audit_backend.py` y `test_audit_forms.py`: resultado comunicado al coordinador. Ruff y drift de migraciones limpios.

Migraciones: core0004, catalog0002, layout0002 y cash0004, aditivas con valores por defecto compatibles y FK nullable. Sin ALTER sobre documentos emitidos. El principal ejecuta gate completo de instalación/upgrade/E2E. AEAT oficial, dispositivo físico y validación humana/equipo destino siguen BLOQUEADO EXTERNO.
