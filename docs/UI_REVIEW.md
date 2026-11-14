# Revisión de interfaz de BeautyTPV V1

Fecha: 14-11-2026. Alcance: consolidación sobre `5dc936a`, conservando Bootstrap 5, HTMX, plano de inicio y reglas transaccionales. Esta revisión evalúa interfaces y persistencia con Chromium; no acredita hardware físico ni AEAT.

## Cambios y trazabilidad

| Requisito | Estado | Implementación y ruta | Prueba / evidencia | Observaciones y bloqueo |
|---|---|---|---|---|
| Ajustes separados Salón/Fiscal/TPV | VERIFICADO | templates/core/settings.html; /empresa/?section=commercial,fiscal,pos | test_admin_settings_logo_preferences_and_register_crud | Formularios reales y validación servidor; NIF/instalación protegidos tras emitir por backend |
| Nombre comercial y logotipo seguro visibles | VERIFICADO | templates/base.html + core/settings.html; core:logo/core:logo_save | Mismo test: subida PNG desde selector de archivos y consulta DB | Logo solo con sesión autorizada; no se crea endpoint público |
| Apariencia, densidad y contraste controlados | VERIFICADO | base.html + static/css/beautytpv.css | Mismo test comprueba clases persistidas y captura desktop/tablet | Opciones cerradas; sin CSS libre |
| Navegación administrativa y caja configurable | VERIFICADO | settings.html, cash/index.html, cash/registers.html y register_form.html | Mismo test crea/edita/desactiva caja por controles UI y comprueba DB | No borra historial; operaciones con turno abierto validadas en backend |
| Categorías, catálogo y puestos ordenables | VERIFICADO | catalog/categories.html, catalog/index.html, layout/index.html y formularios | test_admin_category_visibility_reaches_real_pos_and_cart | Campos de orden/visibilidad reales; prueba navegador con4casos aprobados |
| Plano con sección seleccionable y total pendiente | VERIFICADO | pos/floor.html; /tpv/?section= | Mismo test adicional + suites previas HTMX | Selección se conserva en peticiones HTMX; el plano continúa como inicio |
| Caja: filtros, historial y caja preferida | VERIFICADO LOCAL (HTTP/servicio) | cash/index.html; /caja/?q=&register=&status= | Suite backend + regresiones de caja originales | No cambia movimientos confirmados |
| Incidencias: lista, filtros, alta, validación, actuaciones y resolución | VERIFICADO | support/incidents.html, incident_detail.html; /soporte/incidencias/ | test_manager_incident_create_validate_and_resolve: error PII visible, DB sin inserción, corrección y resolución | Manager solo operativas; SA técnicas con autorización temporal |
| Equipo: revocación explícita y efectiva | VERIFICADO | support/user_edit.html; team:revoke_sessions | test_superadmin_revokes_user_session_from_team_controls: usuario creado desde UI, sesión secundaria real queda403 | Confirma y conserva credenciales; rol backend independiente |
| Superadmin: incidencia técnica y permisos | VERIFICADO | base.html, support/index.html; support:incidents | Mismo test crea incidencia SYSTEM con TECHNICAL temporal | No accede a información personal arbitrariamente |
| Buscar/filtrar equipo, terminales y colas | VERIFICADO LOCAL (HTTP/servicio) | support/users.html, terminals.html, index.html | Rutas y permisos cubiertos por suite de auditoría ampliada | Controles GET reales del backend, sin filtros decorativos |
| Verificar copia cifrada desde panel | VERIFICADO LOCAL (HTTP/servicio) | support/index.html; support:backup_verify | test_consolidation_ops.py | No activa mantenimiento ni restaura sobre DB viva |
| Campos ocultos y errores de formulario accesibles | VERIFICADO | includes/form.html | Compilación completa38templates; tests navegador con error real | Campos hidden no muestran label/espaciado; errors role=alert |

## Recorridos y resoluciones

Se usan controles de persona (formularios, botones, enlaces, selector de archivos, diálogos de confirmación). La preparación de rol para cada servidor aislado es precondición de test; las acciones de negocio se realizan vía interfaz y se contrastan con SQLite. No se inyectan datos de persistencia en sustitución de una acción probada.

- Escritorio1280×720: ajustes TPV y enlaces relacionados, logo, feedback de guardado y navegación. Captura [consolidation-settings-desktop.png](evidence/consolidation-settings-desktop.png), inspeccionada visualmente: dos columnas legibles, formularios sin solapamientos y menú con scroll en altura corta.
- Tablet820×1180: plano compacto y contraste reforzado; selector de secciones y tarjetas. [consolidation-floor-tablet.png](evidence/consolidation-floor-tablet.png), inspeccionada visualmente: los cuatro puestos y el footer son accesibles, sin desbordamiento horizontal.
- Estrecho390×844: incidencia resuelta, historial y formulario de actuación. [consolidation-incidents-mobile.png](evidence/consolidation-incidents-mobile.png), inspeccionada visualmente: paneles apilados, textos largos ajustados y controles táctiles; navegación horizontal desplazable.
- El test adicional genera [consolidation-ticket-mobile.png](evidence/consolidation-ticket-mobile.png), inspeccionado visualmente: catálogo, carrito, notas y cobro se apilan dentro del ancho, con campos accesibles y total legible.

Las aserciones verifican ausencia de desbordamiento horizontal. Las suites originales cubren PIN, dos cuentas persistentes, cobro, copia, factura/cliente y navegación de los cuatro roles. Esta revisión añade las operaciones nuevas y no reemplaza sus aserciones.

## Resultados y defectos corregidos

Primera ejecución detectó un error transitorio de sintaxis en `includes/form.html`, introducido al tratar campos ocultos; se reescribió el include y se compilaron38plantillas. Los selectores de pruebas se acotaron a los campos del formulario para no confundir filtros homónimos ni la alerta de red oculta con un error visible. No se retiraron validaciones ni assertions funcionales.

Ejecución de los tres primeros recorridos: **3 PASS, 40,64s**, un aviso de deprecación del plugin pytest (fixture para pytest10). Repetición final de las cuatro pruebas nuevas: **4 PASS, 51,57s**, sin fallos. El cuarto flujo verifica crear categoría oculta, crear artículo con orden, ausencia en TPV, activación de categoría y aparición real, nota persistente y total pendiente visible en plano. El resultado de la suite integrada se documenta en el informe final del coordinador.

## Límites externos

BLOQUEADO EXTERNO: papel80mm, QR impreso, cajón y otros dispositivos reales; envío/acuse AEAT con certificado; aceptación táctil con personal del salón y equipo/LAN de destino. Los datos y el logotipo de las capturas son sintéticos. La revisión visual no sustituye pruebas de teclado/lector de pantalla exhaustivas ni aceptación humana; no se declara certificación de accesibilidad.

Revisión del coordinador: capturas de ajustes1280, plano820 e incidencia390 inspeccionadas; sin solapamientos ni desbordamiento de formularios. La primera suite integrada detectó ambigüedad de texto Abierto entre filtro y estado de turno; se cambiaron opciones a Turnos abiertos/cerrados conservando las aserciones E01. Resultado final en FINAL_ACCEPTANCE.md.
