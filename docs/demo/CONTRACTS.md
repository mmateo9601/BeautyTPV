# Contrato de ejecución DEMO Windows

Fecha: 14-11-2026. Objetivo: ejecutar el código actual localmente, sin reconstruir módulos funcionales ni utilizar la base principal. Lecturas: AGENTS.md, PLAYBOOK.md, configuración y scripts de instalación/servicio existentes.

## Propiedad y límites

| Propietario | Archivos / responsabilidad |
|---|---|
| Principal | scripts/windows_demo.py, scripts .bat de raíz, crear_acceso_directo.ps1, config/demo_settings.py, integración y guía |
| devops | scripts/demo_server.py: Waitress, identidad de proceso, parada y ciclo del simulador |
| backend | scripts/demo_seed.py: preparación exclusiva de la DEMO, datos sintéticos y usuarios |
| security | Revisión de aislamiento, credenciales y parada; pruebas propias sin editar archivos de otros |
| fiscal / hardware | Revisar ausencia de remisión y simulador, respectivamente; no ampliar funcionalidad |
| frontend / QA | Verificar navegación real y ciclo de vida; evidencia sin contraseñas |
| architect | Este contrato; no edita módulos ajenos |

Los propietarios comunican interfaces antes de consumidores. El principal integra tras la entrega. No se autorizan escrituras simultáneas sobre el mismo archivo.

## Configuración aislada

- Directorio predeterminado: `%LOCALAPPDATA%\BeautyTPV-DEMO`. Contiene marcador/configuración DEMO, SQLite, logs, estado efímero y copia privada de credenciales si se adopta entrega por archivo. Todo fuera del repositorio; ACL limitada al usuario actual y SYSTEM antes de persistir secretos.
- Configuración con identificador de clase DEMO y versión; validar ruta canónica, marcador y relación de los archivos con ese directorio. No aceptar una ruta de DB heredada de instance.json productivo. El entorno del subproceso elimina variables BeautyTPV/Django heredadas y fija el módulo `config.demo_settings`.
- `config.demo_settings` importa la base existente pero fija DB independiente, host `127.0.0.1`, fiscal TEST, aprobación productiva falsa, certificado/clave vacíos y secretos aleatorios externos. HTTP y cookies sin Secure son excepción explícita de loopback DEMO; no cambian la configuración productiva.
- Preferencia: DEBUG=False con Waitress; los archivos estáticos se preparan antes del arranque y su raíz DEMO puede estar separada para no interferir con instalaciones existentes. Nunca usar runserver productivo. No modificar firewall, red ni registros de arranque de otras aplicaciones.
- Hallazgo: el simulador actual exige DEBUG además de HARDWARE_SIMULATOR en drivers/formulario. Si se conserva DEBUG=False, hace falta una extensión mínima y cerrada que admita **solo** settings DEMO explícitos/validados; no relajar la condición productiva global. Esta decisión se integra como defecto que impide la comprobación DEMO y requiere prueba negativa de producción.

## Preparación y usuarios

- Backend proporciona una función de preparación invocable tras configurar Django; debe comprobar módulo/marcador/ruta DEMO antes de cualquier ORM mutante. Aplicar migrate, bootstrap y semilla idempotente, en ese orden.
- Empresa, secciones, puestos, categorías, servicios, productos, clientes y caja son sintéticos y se identifican como DEMO. TEST obligatorio en CompanySettings y TechnicalSettings. Impresora SIMULATOR; sin credenciales de dispositivos externos.
- Cuatro usuarios de roles internos, contraseñas aleatorias independientes y PIN aleatorios con hash Django. Usernames estables de demo no son contraseñas predeterminadas. No introducir claves fijas en código, argumentos de proceso, logs, capturas ni chat.
- Generar/configurar credenciales una vez por instancia; arranques sucesivos no las rotan ni resetean. Restablecimiento explícito, con confirmación, revoca sesiones anteriores. Entrega al usuario por diálogo local o archivo privado externo con ACL, nunca documentación versionada.
- Reinicializar exige que DEMO esté parada y confirmación literal. Verificar canónicamente que cada objetivo pertenece al directorio DEMO y posee marcador antes de mover/eliminar; no utilizar búsqueda por nombres de procesos ni rutas derivadas de datos fiscales.

## Arranque, identidad y parada

- Lanzador en pythonw para uso habitual; batch resuelve `.venv\Scripts\pythonw.exe` desde la ubicación del repositorio. Comprobar intérprete/dependencias, configuración, existencia de SQLite y migraciones antes de lanzar. Fallos se muestran por diálogo comprensible y log saneado.
- Un lock de instancia impide dos lanzamientos simultáneos. Puerto fijo `127.0.0.1:8000`: si lo ocupa otro proceso, informar y no cerrarlo ni cambiar puertos silenciosamente. Un segundo inicio de la misma DEMO solo reutiliza una identidad comprobada y abre navegador.
- Servidor dedicado `scripts/demo_server.py`, Waitress en loopback. Protocolo de readiness propio con nonce aleatorio por ejecución, separado de /health/ existente; responde únicamente desde la instancia correcta. No declarar listo por cualquier HTTP200 de ese puerto.
- Estado efímero registra PID, instante/identidad de creación del proceso, nonce y evento Windows de parada. Evento con nombre local derivado de identidad aleatoria de ejecución; el servidor lo espera y cierra Waitress y sus tareas al activarse.
- Parada valida estado e identidad (PID y creación, más readiness/nonce cuando esté disponible) antes de señalar el evento. Nunca ejecutar `taskkill /IM python.exe`, matar por puerto ni cerrar procesos Python ajenos. PID obsoleto no basta para autorizar terminación. Preferir parada cooperativa; si vence plazo, mostrar incidencia sin matar proceso desconocido.
- Accesos directos: escritorio resuelto mediante API de Windows (incluido escritorio redirigido), nombres `BeautyTPV DEMO` y `Detener BeautyTPV DEMO`; TargetPath y WorkingDirectory absolutos, rutas con espacios correctamente citadas. Script de creación idempotente solo sobre esos nombres.

## Fiscal y hardware

- No lanzar `operations_worker` ni `fiscal_worker` ni llamar `send_one` en la DEMO. El circuito UI genera factura/alta/outbox TEST y deja registros pendientes; nunca inventa aceptación oficial. Certificado y clave externa vacíos. No aprobar producción ni alterar guards.
- Los trabajadores DEMO solo procesan impresoras SIMULATOR. Una impresora TCP/USB/serie creada accidentalmente desde el panel no debe causar I/O físico por el ciclo automático DEMO. Se conservan trabajos y estados reales del spool; DONE significa consumo simulado identificado, no papel físico.
- Comprobar que startup/cobro/parada no generan FiscalTransmission. Una conexión diagnóstica TCP no es remisión; las evidencias deben describir exactamente si se ejecutó.

## Gates verificables

1. DB principal permanece intacta; DEMO crea y migra SQLite propia.
2. Inicio real, readiness con identidad, HTTP de acceso y estáticos correctos, doble inicio sin segundo servidor.
3. Puerto ocupado por proceso ajeno: rechazo seguro sin detenerlo.
4. Parada real libera8000 y preserva un proceso Python independiente; reinicio mantiene cuentas/datos.
5. Navegador: acceso de los cuatro roles; plano/cuenta/cobro/caja/clientes/catálogo/informes/administración/soporte/terminal/dispositivo/factura TEST con scopes existentes. Pruebas usan controles reales y no omiten elevación/PII.
6. Accesos .lnk reales en escritorio y guía con ubicación exacta, alta/recuperación de usuarios, parada/reinicio/reset DEMO y errores habituales.
7. Bloqueos honestos: este gate no valida Windows distintos del probado, fiscalidad productiva, AEAT oficial, impresora/cajón físicos ni despliegue LAN.
