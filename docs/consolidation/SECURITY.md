# Consolidación de seguridad

## Cambio implementado

`apps.accounts.services.revoke_user_sessions(actor, target) -> User` permite invalidar todas las sesiones de un usuario sin modificar PIN o contraseña. ADMIN solo puede administrar inferiores; SUPERADMIN puede actuar sobre cualquier rango, incluida su propia sesión. Se recargan actor/target y se rechazan actores desactivados, degradados o con auth_version obsoleto.

La operación transaccional incrementa auth_version con F, revoca las autorizaciones de soporte donde el usuario sea actor o aprobador y registra user.sessions_revoked con el contador de concesiones. No registra credenciales. El caller HTTP debe exigir sesión elevada y POST/CSRF; devops conecta la pantalla fuera de la propiedad de este agente.

## Pruebas

`tests/test_consolidation_security.py` comprueba múltiples sesiones, nuevo acceso con las mismas credenciales, auditoría, servicios llamados sin request, rangos insuficientes/iguales, target promovido, actor degradado/desactivado/revocado, concesiones como actor/aprobador y autorrevocación Superadmin. Resultado de ejecución en la entrega del agente; el cierre integrado debe incorporar también el endpoint.

## Contratos para otros módulos

- Ajustes/logo: ADMIN elevado en HTTP y require_role(actor, ADMIN) en servicios; separar cambios comerciales de identidad fiscal y conservar snapshots emitidos.
- Logo: aceptar raster validado, re-encode, límite de bytes/píxeles; no SVG/HTML ni extensión confiada. Servir MIME fijo con nosniff; no ejecutar contenido subido.
- Incidencias: no almacenar cuerpos SOAP, secretos ni PII sin necesidad; autorización por rol y scopes para datos técnicos/personales. La gestión operativa no habilita consola de comandos.
- La elevación es contexto HTTP; servicios exigen rol/estado/version persistidos. No confundir APIs de servicio confiables con autorización por ocultación de botones. Los CRUD previos que aún guardan ModelForms directamente en views deben usar las nuevas APIs actor-aware para consumidores no HTTP; el coordinador asigna esos módulos.

## Límites

Ninguna prueba local demuestra TLS/firewall del equipo destino, custodia física, aceptación AEAT o impresora real. El acceso OS privilegiado puede reemplazar código/BD; roles aplicativos no lo aíslan.
