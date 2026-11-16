> Guía canónica actual: [manuales/GUIA_SUPERADMIN.md](manuales/GUIA_SUPERADMIN.md). Este documento conserva procedimientos y evidencias históricos; consulte la guía actual antes de operar.

# Operación Superadmin

Acceda con contraseña administrativa o confirme identidad en `/elevar/`. La elevación dura diez minutos; el PIN nunca autoriza operaciones técnicas críticas. `/soporte/` es un panel propio, independiente de Django Admin.

- Salud: versión, SQLite, integrity_check, latencia medida de consulta, disco libre, migraciones pendientes, colas fiscal/impresión y caducidad PEM del certificado externo. No se inventan métricas de red: el botón diagnóstico de red comprueba TCP443, sin envío fiscal ni autenticación de certificado.
- Sesión de soporte: motivo, alcance TECHNICAL/PII/BACKUP/UPDATE, aprobador con contraseña y caducidad de veinte minutos. PII requiere otro administrador; no existe backdoor de soporte. Cree el administrador responsable antes de acceder como técnico a datos personales. El alcance técnico no revela claves ni respuestas fiscales completas.
- Equipo `/usuarios/`: Admin crea/modifica solo inferiores; Superadmin puede gestionar Superadmin. PIN se almacena con hash, reset auditado; no hay credenciales predeterminadas. Para acciones de PII se aplica autorización adicional.
- Dispositivos: altas/edición ESC/POS TCP, USB o serie; simulador exclusivamente desarrollo. Prueba de ticket y cajón auditadas. UNKNOWN exige revisión humana; reintento no repite entrega incierta. Los cambios no alteran facturas ni vuelven a cobrar.
- Fiscal: pendientes, reintentos y estado real conservado. Recuperar solo programa pendientes/reintentables; los rechazados requieren subsanación fiscal, aceptados no se reenvían arbitrariamente.
- Backup: alcance BACKUP, cifrado autenticado, auditoría, política de intervalo/retención operada por worker y descarga cifrada. Restauración offline y conciliación obligatoria según BACKUP_RESTORE.
- Actualizaciones: versión e historial, paquete local de hash verificado, backup previo y rollback solo código. Véase UPDATE.
- Auditoría: vista protegida `/auditoria/`; export de diagnóstico contiene solo métricas permitidas, sin secrets, PII ni rutas de certificados. Logs de subprocess/servicio no deben publicarse sin saneado.

El servidor/bridge/workers oficiales comparten lock de ciclo de vida. Restore/update exige lock exclusivo. En mantenimiento cierre terminales y procesos externos, preserve acuses y no retire retención sin conciliación documentada.

No se acredita hardware físico ni conformidad AEAT mediante este panel: consulte RELEASE_REPORT y VERIFACTU_COMPLIANCE.


## Funciones ampliadas por la auditoría

Terminales: `/soporte/terminales/` administra actividad/token y la asignación de impresoras. Fiscal: `/soporte/fiscal/` configura referencias externas del certificado y clave; valida caducidad y correspondencia sin guardar sus bytes. La anulación registral exige motivo y confirmación; no devuelve el importe de una venta. Para devolución se usa la rectificativa.

Restauración: `/soporte/restauracion/` verifica una copia registrada, muestra diferencias fiscales y prepara mantenimiento con confirmación `PREPARAR RESTAURACION`. No reemplaza una BD viva por HTTP. Seguir el procedimiento CLI offline, conservar acuses y conciliar antes de retirar el hold. Desbloquear PIN se realiza desde Equipo con autorización jerárquica; el bloqueo por origen exige soporte técnico.

Cambiar rol, actividad, PIN o contraseña revoca sesiones existentes. Reactivar un usuario no recupera sus concesiones anteriores. El panel distingue supervisión real de ejecución sin supervisor; workers caídos no se presentan como sanos.


## Controles añadidos en la consolidación

Equipo incluye filtros y edición de nombre. Revocar sesiones exige REVOCAR SESIONES: invalida sesiones y concesiones conservando credenciales; autorrevocar exige nuevo acceso. Admin solo inferiores; Superadmin también Superadmins.

Terminales configuran caja activa propia/compartida y sección preferida. Impresoras permiten corte y cajón: se aplican a bytes nuevos sin reescribir intención previa. Durante SENDING no se cambia destino/terminal. Incidencias técnicas requieren elevación y TECHNICAL; no pegar XML/logs/claves/tarjetas/datos personales. Los patrones de rechazo no son detección universal: el operador debe evitar cualquier dato identificable.

Verificar backup comprueba hash/autenticación/integridad y audita sin mantenimiento ni reemplazo de BD; es distinto de Preparar restauración. Diagnóstico muestra Python/Django/dependencias reales. Filtros de usuarios/terminales/colas actúan sobre DB.
