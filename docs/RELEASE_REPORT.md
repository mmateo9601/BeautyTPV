# Informe de release — BeautyTPV 0.1.0

Fecha: 13-11-2026. Instalación local independiente por empresa. Django 5.2.19 + Bootstrap 5.3.8 + HTMX 2.0.8 + SQLite; Python 3.14.7 en Windows.

**Resultado: implementación local ejecutable y verificada; release fiscal productiva BLOQUEADA.** No se declara conformidad AEAT ni hardware físico verificado. El modo productivo está cerrado en código; los comprobantes TEST llevan aviso de falta de validez fiscal productiva.

## Comprobaciones del coordinador

| Comprobación | Resultado | Evidencia / alcance |
|---|---|---|
| Inventario, contratos y ocho especialistas | VERIFICADO | CONTRACTS.md, ADRs, agentes architect/backend/frontend/fiscal/hardware/security/qa/devops utilizados con propietarios exclusivos |
| Django check | VERIFICADO | `manage.py check`: 0 incidencias |
| Migraciones | VERIFICADO | `migrate --noinput` aplicado; `makemigrations --check --dry-run`: sin cambios |
| Suite completa | VERIFICADO: 112 PASS, 73,33 s | evidence/final-tests.xml. Dos avisos: override DATABASES en prueba aislada y deprecación de fixture del plugin pytest para versión10; sin fallos |
| Análisis estático | VERIFICADO | `ruff check .` limpio y `ruff format --check .`: 192 archivos formateados |
| Instalador en instancia nueva | VERIFICADO | `scripts/install.py --instance-dir <temporal nuevo> --no-user`: EXIT0, pip editable, SQLite nuevo, migraciones, bootstrap, check y collectstatic. Segunda instancia nueva con requirements.lock.txt también EXIT0. Entorno Python/venv ya preparado; no se afirma máquina virgen ni instalación de SO |
| Arranque y workers | VERIFICADO | `scripts/service.py --development`: HTTP200 acceso, Bootstrap232111 bytes y HTMX51250 bytes; servidor/workers activos impiden lock exclusivo de restore; parada controlada de procesos y integrity_check OK; usuarios semilla0 |
| Backup/restore real por CLI | VERIFICADO | `backup.py` y `restore.py --offline --confirm "RESTORE OFFLINE"`: EXIT0 en instancia sintética, copia cifrada y marcador de retención presentes; E12 adicional conserva facturas/cadena y bloquea duplicados |
| Paquete completo y actualización real | VERIFICADO LOCAL | ZIP con release.json y SHA256 validado; `update.py --offline` aplicado a copia temporal completa del código, migrate/check/collectstatic EXIT0. Rollback de código sin revertir BD probado además por tests; no se actualizó un negocio real |
| Interfaz y PDF | VERIFICADO VISUAL LOCAL | evidence/floor-desktop.png, ticket-tablet.png e invoice-test.png/PDF: revisados por QA y coordinador; sin solapamientos. PDF de una página con QR, snapshots y desglose |
| CI | NO VERIFICADO REMOTO | Workflow incluido con Chromium; no se afirma ejecución en GitHub |
| Seguridad despliegue | VERIFICADO CONFIGURACIÓN / PENDIENTE EQUIPO | Diagnóstico producción: sin errores, avisos W005/W021 por no activar HSTS para subdominios/preload. Decisión dependiente del dominio del negocio. TLS/proxy/firewall/arranque automático en destino no se han instalado ni validado |

## E01–E16

El detalle requisito→test→límite está en [ACCEPTANCE_MATRIX.md](ACCEPTANCE_MATRIX.md).

| Escenario | Estado de software | Validación externa |
|---|---|---|
| E01 efectivo, caja, factura, cola, liberar puesto | VERIFICADO servicio + navegador | Impresión/cajón físicos BLOQUEADOS |
| E02 A1/A2 independientes y persistentes | VERIFICADO procesos nuevos + navegador | Reinicio completo de SO NO VERIFICADO |
| E03 varios IVA y descuento autorizado | VERIFICADO servicio + CRUD navegador/F1 | Configuración de impuestos reales por negocio pendiente |
| E04 mixto y caja solo efectivo | VERIFICADO | Datáfono/banco real NO VERIFICADO |
| E05 doble cobro | VERIFICADO dos procesos: venta/factura/alta únicas | Carga/LAN real mayor NO VERIFICADA |
| E06 impresora caída | VERIFICADO simulador/errores, copia sin recobro | Dispositivo físico BLOQUEADO |
| E07 Internet/AEAT caída | VERIFICADO fallo de red simulado, outbox intacto | Entorno oficial BLOQUEADO |
| E08 rechazo y subsanación | VERIFICADO SOAP sintético validado XSD y origen conservado | Rechazo/subsanación oficiales BLOQUEADOS |
| E09 inmutabilidad y rectificación | VERIFICADO ORM/SQL y sellado de nuevas líneas/pagos | Revisión fiscal externa pendiente |
| E10 empleado denegado | VERIFICADO 403 y permisos de servicios | Aceptación con empleados reales NO VERIFICADA |
| E11 jerarquía, elevación y soporte auditado | VERIFICADO, PII requiere aprobación independiente temporal | Aceptación con responsable real NO VERIFICADA |
| E12 backup/restauración sin duplicados | VERIFICADO BD emitida + CLI + hold | Conciliación de acuses AEAT reales BLOQUEADA |
| E13 tres terminales | VERIFICADO tres procesos SQLite locales | Sin certificación de capacidad sostenida |
| E14 80mm, QR escaneado, cajón | SOLO SOFTWARE VERIFICADO: ESC/POS/QR/corte y políticas de cajón | BLOQUEADO FÍSICO completo |
| E15 devolución fiscal y conciliación | VERIFICADO rectificativa total, caja/IVA/métodos netos y rechazo caja obsoleta | Remisión y devolución bancaria reales BLOQUEADAS |
| E16 precio histórico | VERIFICADO snapshots y cambio de catálogo desde navegador | Sin bloqueo adicional identificado por estas pruebas |

## Fiscal y hardware: gates que impiden producción

1. No se ha proporcionado certificado ni autorización del obligado para remisión oficial AEAT. Ningún fixture representa aceptación real. Transporte mTLS, reintentos, respuesta validada XSD/identidad y cadena están preparados; deben ejecutarse y conservarse evidencias oficiales.
2. Falta revisión experta de los tipos de operación soportados, subsanaciones/rectificaciones y configuración fiscal aplicable; falta declaración responsable firmada/publicada por el productor. VERIFACTU_COMPLIANCE.md identifica fuentes oficiales, hashes y correspondencias. No se genera una firma ni declaración ficticia.
3. No se ha proporcionado impresora/cajón ni marca/modelo/firmware: falta imprimir 80mm, escanear QR real, USB/Ethernet, corte y apertura física. HARDWARE.md contiene el checklist.
4. Falta aceptación operativa con propietario, encargado, empleado y Superadmin reales en el equipo destino, además de TLS y arranque automático. Los datos usados aquí son sintéticos.

## Límites funcionales explícitos

- Facturación y hardware en TEST/simulador no autorizan facturar en producción. La activación exige evidencia y revisión; no hay conmutador web que eluda el gate.
- Devolución implementada: rectificación total de una factura; no devolución parcial ni conciliación bancaria automática.
- Tarjeta: confirmación de datáfono externo y referencia; no se simula cobro bancario ni se almacenan números de tarjeta.
- Actualización por paquete local/hash de canal confiable; no hay catálogo remoto ni autoactualización desde Internet. El SHA256 verifica integridad; no constituye firma digital de productor.
- Ensayo de concurrencia: tres procesos locales y dos sobre una misma venta. No establece capacidad comercial máxima. SQLite permanece en disco local del servidor, nunca SMB/NFS.
- Restaurar conserva backup previo y bloquea emisión/remisión/impresión hasta conciliación. El comando de retirada de hold registra hash del informe; no valida automáticamente su veracidad ni sustituye revisión AEAT.

## Arranque por el responsable

Siga [INSTALL.md](INSTALL.md). El instalador solicita el primer Superadmin de forma interactiva; no hay usuario, PIN ni contraseña predeterminados. Cree un Administrador operativo, configure empresa/catálogo/PIN y dispositivos. El acceso técnico a PII por Superadmin exige aprobación de otro administrador.

Documentos: README.md, USER_MANUAL.md, SUPERADMIN.md, SECURITY.md, HARDWARE.md, BACKUP_RESTORE.md, UPDATE.md, VERIFACTU_COMPLIANCE.md, IMPLEMENTATION_STATUS.md y ADRs.
