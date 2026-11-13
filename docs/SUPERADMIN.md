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
