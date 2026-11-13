# Auditoría integral de interfaz

Base revisada: 4ce821e. Propiedad: templates/, static/, tests/e2e/test_audit_ui.py. Fecha: 2026-11-13.

## Hallazgos corregidos

- Informes insertaba paneles HTML dentro del bloque title y duplicaba secciones. Se limita el título a Informes y se conservan los paneles una vez en content.
- Las cuentas PAYMENT_PENDING y cerradas mostraban edición de líneas y cliente. Se oculta la edición fuera de OPEN, se muestra estado explícito y se conectan preparar cobro/reanudar. El cobro sigue disponible en OPEN/PAYMENT_PENDING.
- Faltaban notas de línea y filtro de categoría. Los formularios envían note y category a servicios reales.
- La venta rápida configurable no tenía acceso. Se añade POST de creación y enlaces a las ventas rápidas persistentes del usuario.
- Los iconos decorativos del menú se incluían en su nombre accesible. Se marcan aria-hidden para identificación por texto estable.
- La configuración de secciones carecía de accesos de edición y eliminación. Se conectan los nuevos endpoints, con confirmación en POST.
- Los filtros nuevos de informes no estaban representados. Se añaden caja, método, empleado y artículo, selección persistente, explicación de operaciones completas y tablas de documentos/anulaciones.
- Soporte no enlazaba terminales ni certificado fiscal. Se añaden pantallas, formularios y navegación; comprobación de paquete y SHA-256 muestra el resultado sin instalar nada.
- Gestión de usuario no explicaba revocación de sesiones. Se informa que cambiar PIN, contraseña, rol o estado exige nuevo acceso. Superadmin dispone del formulario de desbloqueo bajo control backend.
- Devolución en efectivo requería escribir ID del turno manualmente. Se utiliza un selector de turnos abiertos.

## Verificación

Todas las plantillas compilan con Django. Ruff pasa para test_audit_ui.py. La suite de navegador usa Chromium, servidor Django y SQLite aislados; no simula negocio. Cubre conservar nota, preparar cobro, bloquear edición, estado del plano, reanudar y menús de los cuatro roles con anchura 390 px. La ausencia de autorización PII de Superadmin debe producir 403 al abrir informes, aunque el rol herede el acceso funcional.

La suite QA independiente cubre flujos fiscales, mixto, CRUD y autorización de soporte. Esta revisión no declara pruebas físicas ni aceptación AEAT. No sustituye los bloqueos del informe de release.
