# Seguridad y operación local

BeautyTPV es una instalación independiente por empresa. El fichero SQLite vive en el disco local del servidor, nunca en SMB/NFS. El navegador accede al servidor; no recibe secretos de dispositivos ni certificados.

## Amenazas y controles requeridos

| Amenaza | Control | Evidencia requerida |
|---|---|---|
| Adivinación de PIN | Hash Django, intentos persistentes, bloqueo temporal por usuario y origen | Tests de PIN y bloqueo |
| Empleado invoca URL administrativa | Comprobación de rango en vista y servicio | Tests negativos de permisos |
| Administrador se promociona | Solo Superadmin asigna Superadmin; administración limitada a inferiores | Test de escalada |
| Terminal abandonado | Caducidad de sesión, logout POST, reautenticación por contraseña para privilegios | Test de elevación/caducidad |
| Soporte consulta datos personales sin motivo | Autorización explícita, alcance, justificación, expiración y auditoría | Test de sesión soporte |
| CSRF o red no confiable | Middleware CSRF; HTTPS y cookies Secure en despliegue | Check deploy y prueba POST |
| Alteración de evidencia | Auditoría append-only en ORM; protección del servidor y copias | Tests de update/delete |
| Filtración de secretos en logs | Metadatos por lista permitida; no almacenar PIN, contraseñas, claves ni tarjetas | Test de filtrado |
| Robo o corrupción de copia | Backup consistente cifrado; clave externa y restauración aislada | Prueba recuperación |
| Factura modificada | Snapshots inmutables y rectificación | Pruebas fiscal/integración |

## Límites de confianza

El administrador del sistema operativo puede modificar el fichero de base de datos y el código. Las restricciones ORM no sustituyen permisos del sistema, control de acceso al servidor, copias protegidas y supervisión de integridad. No se declara resistencia criptográfica a un administrador del servidor.

El PIN identifica empleados durante operación presencial. Un usuario administrativo necesita contraseña para obtener sesión elevada. Las acciones técnicas críticas requieren elevación reciente además de rango; la elevación no cambia el rol. Volver a acceder con PIN elimina la elevación anterior incluso cuando Django conserva la sesión del mismo usuario.

El acceso técnico Superadmin a clientes, facturas, informes, cuentas abiertas y reimpresión exige una sesión elevada y una autorización temporal PII aprobada por otro administrador activo. El middleware `apps.accounts.middleware.SupportPIIMiddleware` comprueba alcance, vencimiento, revocación e independencia del aprobador y audita cada concesión o denegación. Debe instalarse después del middleware de autenticación. Los roles operativos inferiores mantienen sus permisos normales.

La auditoría aplica restricciones ORM y triggers SQLite contra modificación o borrado, incluido UPSERT por `bulk_create`. Los hashes de evidencias de conciliación solo se conservan como SHA-256 hexadecimal de 64 caracteres; los metadatos no permitidos se descartan.

No hay usuario externo Cliente, portal, contraseña predeterminada, acceso de soporte oculto ni almacenamiento de datos de tarjetas. La confirmación de tarjeta representa el resultado del datáfono externo.

## Despliegue

Configure una clave Django única fuera del repositorio, hosts explícitos, `DEBUG=False`, TLS en redes no confiables y firewall limitado a terminales autorizados. Proteja claves de cifrado, certificados y base de datos mediante permisos del sistema. No publique el servicio de desarrollo de Django en Internet.

## Estado de revisión

La suite `tests/test_security.py` cubre matriz de rangos, escalada, hash y bloqueo PIN, elevación, inmutabilidad de auditoría, evidencia de conciliación y autorización PII. La revisión transversal identificó correcciones adicionales de reimpresión, sesiones de caja obsoletas, protección de mantenimiento y procesos de restauración; el coordinador integra y verifica esos módulos. Los controles de la tabla son criterios de revisión: su mera inclusión no significa que la revisión externa haya pasado. El informe de release debe distinguir las evidencias ejecutadas y los controles pendientes.


## Revisión integral posterior a 4ce821e

Sesiones ligadas a versión de autenticación y credenciales/rol persistidos; acciones administrativas requieren elevación también en GET. Scopes PII se aplican a todos los métodos. Terminales de máquina usan token hash y lease; una cookie no autoriza el bridge. Triggers bloquean también INSERT OR REPLACE en historial protegido. Los tests negativos y sus límites están en `audit/SECURITY_FINDINGS.md` y en la matriz raíz `AUDITORIA_COMPLETA.md`.
