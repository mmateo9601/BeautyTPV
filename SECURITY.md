# Seguridad de BeautyTPV

BeautyTPV es software local por empresa. La versión declarada en los metadatos es `0.1.0`; no hay una política pública de versiones soportadas ni un compromiso de plazos de parcheo definido. La producción fiscal permanece bloqueada por validaciones externas. TEST no acredita conformidad AEAT.

## Comunicar una vulnerabilidad

No se ha definido un correo de seguridad, una empresa titular ni un canal público de divulgación privada. **Acuerde primero un canal privado con el propietario del producto o el instalador responsable de su instalación.** Si no dispone de ese contacto, solicite el canal de seguridad sin publicar detalles explotables ni datos del negocio. No inventar ni utilizar un destinatario supuesto.

No publique una vulnerabilidad activa con credenciales, copias SQLite, datos de clientes o pruebas explotables en un issue abierto. No envíe archivos sensibles hasta confirmar quién los recibirá y por qué canal.

Un reporte inicial saneado debe contener:

1. Versión/commit y entorno afectado, sin rutas privadas innecesarias.
2. Módulo y precondiciones: rol, sesión elevada o scope requerido.
3. Pasos reproducibles sobre una DEMO independiente y resultado observado/esperado.
4. Impacto posible y capturas o registros mínimos con datos sintéticos.
5. Si existe, cambio o prueba de regresión propuesta.

No pruebe ataques sobre instalaciones ajenas o productivas sin autorización. No copie bases reales para hacer una reproducción pública. La coordinación de divulgación, responsable y plazos debe pactarse; no hay SLA o programa de recompensas anunciado.

## Respuesta operativa recomendada

El responsable de la instalación debe registrar la incidencia y su alcance, preservar evidencia saneada, limitar exposición y acordar una corrección con el mantenedor. Ante credenciales comprometidas, cambie las afectadas y revoque sesiones/autorizaciones usando los controles documentados. No borre registros fiscales, historial de auditoría ni restaure una base anterior para ocultar la incidencia.

Una corrección se verifica con reproducción aislada, prueba negativa, regresión, revisión de migraciones y release controlado. No se publican automáticamente cambios o avisos en nombre del propietario.

## Documentación y controles

- [Arquitectura de seguridad](docs/arquitectura/SEGURIDAD.md): controles implementados y límites de confianza.
- [Matriz de roles y permisos](docs/ROLE_PERMISSION_MATRIX.md): rutas, servicios, elevación y scopes.
- [Guía Superadmin](docs/manuales/GUIA_SUPERADMIN.md): soporte, credenciales, auditoría y mantenimiento.
- [Guía DEMO Windows](docs/GUIA_WINDOWS_DEMO.md): instancia aislada y credenciales aleatorias privadas.
- [Proceso de release](RELEASE_PROCESS.md): revisión previa y distribución controlada.
- [Informe de release](docs/RELEASE_REPORT.md): evidencias y bloqueos reales.

No existe backdoor de soporte ni contraseña predeterminada. PIN no eleva; contraseña reforzada no equivale a MFA independiente. Los roles no aíslan a un administrador del sistema operativo capaz de reemplazar archivos/código. Las copias se cifran, pero la SQLite operativa no incorpora cifrado integral.

Antes de distribuir deben definirse titular, canal privado, responsables y política de mantenimiento. Las condiciones de uso y redistribución del software están en [LICENSE](LICENSE); este documento no declara una certificación de seguridad.
