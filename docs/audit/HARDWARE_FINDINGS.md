# Auditoria hardware — referencia 4ce821e

Propiedad: apps/hardware/, tests/test_audit_hardware.py; coordinacion con principal
para core.Terminal/OpenTicket.terminal. Fecha de ejecucion: 13-11-2026.

## Hallazgos corregidos y evidencia

| ID | Requisito | Estado en 4ce821e | Correccion final | Evidencia automatizada |
|---|---|---|---|---|
| A-HW01 | Dispositivos configurables sin romper cobro | PARCIAL: encoding no valido y codepage>255 hacian fallar render/spool dentro de checkout | Printer.clean valida codec, codepage y conexion. Un dispositivo invalido existente genera trabajo pendiente sin destino con incidencia; no aborta la factura | test_invalid_device_configuration_rejected (4 casos), test_invalid_device_does_not_roll_back_invoice_spooling |
| A-HW02 | Acciones tecnicas bajo autorizacion temporal | PARCIAL: test/retry solo requerian Superadmin elevado | Ambos endpoints requieren autorizacion TECHNICAL activa; servicios mantienen permisos backend | test_test_and_retry_endpoints_require_technical_authorization |
| A-HW03 | Intencion de impresion y auditoria inmutables | PARCIAL: queryset.update y SQL OR REPLACE eludian save | Migracion0003 protege cambios/delete/replace de intencion y update/delete/replace de HardwareEvent; estado de cola sigue mutable | test_print_intent_and_hardware_events_cannot_be_changed_by_queryset; test_sql_replace_cannot_replace_print_intent_or_hardware_history |
| A-HW04 | Recuperacion de entrega incierta | PARCIAL: el proceso podia retornar True y registrar DONE despues de lease expirada, aunque fila quedaba UNKNOWN | CAS final verifica lease propia; al perderla devuelve falso y registra UNKNOWN | test_lease_expired_during_send_is_not_falsely_reported_done |
| A-HW05 | Codificacion consistente al reasignar impresora | PARCIAL: payload ya codificado podia mandarse a configuracion distinta | Encoding/codepage congelados en PrintJob; reintento incompatible rechazado y copia explicita disponible | test_retry_different_encoding_is_rejected |
| A-HW06 | Ticket completo F1/rectificativa | PARCIAL: faltaban cliente, referencia/motivo rectificado y fecha fiscal local | Snapshot de destinatario, referencia/motivo y fiscal_date de factura | test_full_receipt_contains_customer_and_rectification_reference |
| A-HW07 | Operacion local y por terminal LAN | PENDIENTE: siempre primera impresora y bridge solo misma BD local | Printer.terminal; seleccion especifica/fallback local; API claim/ack autenticada; agente HTTPS remoto sin acceder a SQLite | test_terminal_routing_prefers_its_device_and_has_explicit_local_fallback; test_bridge_claim_ack_are_token_scoped_and_idempotent; test_remote_agent_complete_claim_print_ack_and_restart_safety |
| A-HW08 | No duplicar cajon/ticket tras reiniciar agente o perder ACK | PENDIENTE para agente remoto | Journal durable antes del IO; restart sin resultado -> UNKNOWN; ACK perdido se reintenta sin volver a enviar bytes | test_agent_ack_network_failure_retries_ack_without_reprinting; test_bridge_expired_delivery_is_quarantined_and_remote_jobs_not_locally_sent |
| A-HW09 | Restore no reimprime ni abre cajon | PARCIAL: worker caia al arrancar con hold | Worker queda pausado; recover/retry/process/claim respetan hold, ACK anterior puede conservar evidencia de una entrega ya iniciada | test_bridge_restore_hold_prevents_claim; tests/test_regressions.py prueba process_job retenido |
| A-HW10 | Transporte TCP real | Solo mocks previos | Socket TCP loopback envia bytes exactos; no dispositivo real | test_tcp_loopback_transmits_exact_bytes_without_physical_device |

El test preexistente de empleado cambiaba role solo en memoria. Se actualizo la
fixture con save(update_fields=['role']) porque los permisos ahora usan el rol
persistido; se conserva la asercion de denegacion.

## Protocolo remoto ejecutable

- POST `/hardware/bridge/<terminal_pk>/claim/`, Authorization Bearer con token
  largo cuyo hash almacena Terminal. Exige terminal activa. Respuesta204 si cola
  vacia; respuesta200 contiene ID, lease_token, payload base64 y configuracion de
  un dispositivo ya autorizado para esa terminal. No acepta comandos/bytes/destinos
  aportados por el cliente. Registra claim y actualiza last_seen_at medido.
- POST `/hardware/bridge/<terminal_pk>/jobs/<job_pk>/ack/`, mismo Bearer y JSON
  `{status: DONE|FAILED|UNKNOWN, lease_token: ...}`. Solo acepta trabajo de la
  terminal y nonce de lease vigente. ACK repetido es idempotente. Lease expirada
  queda UNKNOWN y no vuelve a PENDING automaticamente.
- Los endpoints de maquina son CSRF-exempt porque usan Bearer, no cookies. El
  resto de acciones de navegador conserva CSRF y permisos del usuario.
- El worker del servidor solo procesa impresoras sin terminal. Las asignadas a
  terminal las procesa el agente: evita que servidor y terminal consuman ambos
  el mismo trabajo USB. Existe fallback explicito de terminal a impresora local.

En el PC de la terminal, instalar las dependencias del paquete y ejecutar:

```powershell
$env:BEAUTYTPV_TERMINAL_TOKEN = '<token generado por Superadmin, no predeterminado>'
python -m apps.hardware.agent --server https://tpv.nombre-local --terminal 1 --journal C:/BeautyTPV/agent-journal.json
```

No necesita configurar ni compartir una BD SQLite. HTTPS valida certificados con
requests por defecto; no hay verify=False. HTTP solo es admisible con bandera
`--development-loopback` y host127.0.0.1/localhost/::1. El journal guarda IDs y nonce,
no contenido de factura; debe permanecer fuera del repositorio y con permisos de
la cuenta operadora. Un restart con envio no confirmado no repite bytes. Un cambio
de instalacion/terminal con journal pendiente exige conciliacion manual.

La interfaz de gestion de dispositivos debe incluir terminal y proporcionar el
token de terminal mediante el flujo protegido de core/support integrado por el
principal; estos archivos pertenecen a otros propietarios.

## Comprobaciones ejecutadas

`.venv/Scripts/python -m pytest tests/test_audit_hardware.py tests/test_hardware.py -q`
ejecutado con permisos de red local: **35 passed en 2.04 s** (21 nuevos casos de
regresion +14 previos). Sin permisos de socket del sandbox, WinError10013 impide
el caso TCP loopback; no es una prueba fallida de impresora. Ruff check/format de
hardware y pruebas limpio. Migraciones nuevas0002 y0003 generadas.

El flujo de agente se verifica contra vistas Django y SQLite reales usando un
transporte HTTP de test y un sender identificadamente simulado; el transporte
TCP se prueba por separado en un socket real loopback. No se afirma que se haya
probado una LAN fisica ni HTTPS de equipo destino.

## Bloqueos externos y clasificacion final

- Spool/bridge/roles/routing/reinicio/ACK/copia/retencion: COMPLETO en software segun
  tests anteriores, sujeto a integracion UI del coordinador.
- USB y serie: implementados, comportamiento de error preparado, ejecucion con
  driver/dispositivo real BLOQUEADA. No hay VID/PID ni modelo/firmware proporcionados.
- E14: BLOQUEADO fisico. Falta ticket80mm, lectura QR en papel, apertura real del
  cajon, corte y codificaciones del modelo de impresora real. Un DONE significa
  bytes enviados al transporte, no una confirmacion de papel impreso.
- Instalacion/autoarranque del agente en equipo de terminal real y TLS de LAN:
  BLOQUEADO equipo externo no disponible; el comando y protocolo estan preparados.
