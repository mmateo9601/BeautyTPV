# Revisión de seguridad — DEMO Windows

Fecha: 14-11-2026. Revisión inicial del diseño; no constituye aún evidencia de ejecución de los scripts. Propiedad del especialista: este documento, sin cambios a módulos funcionales.

Se leyeron AGENTS.md, PLAYBOOK.md, configuración security y los settings/scripts de instancia actuales. El requisito nuevo es una demostración aislada limitada a localhost; no cambia la política productiva.

## Fronteras y controles exigidos

| Riesgo | Control de diseño | Comprobación necesaria |
|---|---|---|
| Heredar la BD principal del entorno | Settings DEMO dedicado; resolver DB fija dentro de LOCALAPPDATA/BeautyTPV-DEMO; marker identificable antes de migrar, seed o reset; limpiar variables heredadas | Inyectar BEAUTYTPV_DB/DJANGO_SETTINGS_MODULE/certificados falsos y comprobar DB DEMO/TEST efectiva |
| Alterar archivos fuera de DEMO al reiniciar | Ruta raíz conocida, archivos esperados, validación de contención y rechazo de enlaces/reparse points; nunca borrar un directorio calculado no comprobado | Reset sobre directorio temporal marcado; datos centinela ajenos intactos |
| Credenciales fijas o filtradas | Contraseñas y PIN únicos aleatorios o definidos de forma interactiva; hash Django; secretos y archivo de entrega fuera de Git; ACL de directorio y archivos para SID actual y SYSTEM antes de escribir | Buscar secretos en repo/logs; verificar ACL y capacidad de login de cuatro roles; no publicar valores en reportes |
| DEBUG/servidor desarrollo confundido con producción | Waitress y DEBUG=False; módulo DEMO separado permite HTTP solo loopback; no cambiar config.settings productivo | settings DEBUGFalse, bind127.0.0.1 y ausencia de runserver; HTTP200 y estáticos reales |
| Puertos duplicados o navegador abierto hacia otra app | Comprobar puerto antes de lanzar; readiness específico con identidad aleatoria DEMO, no solo /health200; un segundo arranque solo reutiliza instancia verificada | Ocupar8000 con otro servidor, rechazar sin detenerlo; doble arranque conserva mismo proceso |
| Parada de Python ajeno o PID reciclado | Señal de evento Windows nombrado por nonce privado; identidad PID/creationtime comprobada; no taskkill /IM python ni matar por puerto | Estado obsoleto/PID ajeno no lo detiene; cierre normal libera solo servidor DEMO y sus workers |
| Envío AEAT accidental | TEST forzado, certificados externos vacíos, sin worker de remisión; defensa de transporte fail-closed exclusiva de DEMO aunque se cambie configuración desde UI | Cola local crece sin FiscalTransmission/remisión; intento de enviar falla sin abrir socket |
| Dispositivo físico activado sin querer | Solo impresora SIMULATOR en seed y worker DEMO con validación del tipo; no ejecutar hardware físico por configuración mutable | Cobro produce spool y entrega simulada; configuración TCP/USB/serie no dispara transporte físico DEMO |
| Rebajar permisos para demo | Mantener roles, PIN, elevación, scopes PII/TECH/BACKUP/UPDATE y rate limiting; acceso Superadmin usa contraseña elevada y autorización cuando corresponde | Employee denegado en soporte/configuración; SA sin PII sigue denegado; aprobación independiente con Admin para datos comerciales |
| Logs/estado con secretos | JSON de estado solo identidad de proceso, sin contraseñas/PIN/clave/certificados; errores GUI resumidos y logs locales restringidos | Revisar archivo de estado y logs tras éxito y error |

## Decisiones concretas

- Las excepciones HTTP de localhost se aplican únicamente a settings DEMO. En producción continúan HTTPS/cookies Secure, guard fiscal cerrado y servidor WSGI real.
- El archivo local de credenciales de prueba es material sensible, incluso con datos sintéticos; si se genera para facilitar uso sin terminal, debe quedar bajo ACL restrictiva y explicarse su ubicación. No hay contraseñas incorporadas al repositorio.
- Root y Superadmin son identidades distintas: un administrador del sistema operativo puede modificar código/archivos locales y no queda aislado por los roles Django. No se promete defensa contra el propietario de la misma sesión Windows.
- Un nonce impredecible privado y evento de la sesión local evita usar nombre global fijo como mecanismo de parada. JSON es dato; no ejecutar configuración como código.
- La reinicialización debe cerrar primero la DEMO y conservar o reemplazar exclusivamente su SQLite y sus artefactos identificados; no usar comodines globales para borrar bases de datos.

## Estado de esta revisión

Diseño revisado y recomendaciones enviadas al coordinador. Falta revisar implementación final y comprobar los controles mediante pruebas reales. No se ha validado aún un acceso directo ni se afirma ausencia de tráfico real en una ejecución no realizada. Los bloqueos AEAT/hardware físicos del producto continúan intactos.

## Cierre integrado del coordinador

La decisión final y pruebas reales están en ../GUIA_WINDOWS_DEMO.md y ../evidence/windows-demo-smoke.json. Perfil config.demo_settings con DEBUG=False, guards específicos de simulación, transportes físicos rechazados y remisión bloqueada. Factura TEST/spool simulado verificados, cero FiscalTransmission. Se preservan límites externos; esta sección supersede recomendaciones preliminares que no se adoptaron.
