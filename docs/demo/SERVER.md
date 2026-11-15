# Servidor dedicado para BeautyTPV DEMO Windows

Fecha: 15-11-2026. Propiedad de esta entrega: `scripts/demo_server.py`, `tests/test_demo_server.py` y este documento. Se leyeron AGENTS.md, PLAYBOOK.md y el contrato DEMO. No se modificaron módulos funcionales ni scripts del coordinador.

## Implementación

- Waitress sirve la aplicación WSGI en **127.0.0.1:8000**, con cuatro hilos. No usa `runserver` ni permite seleccionar otra dirección/puerto desde su CLI.
- CLI interna: `demo_server.py --instance-dir <DEMO> --token <identidad aleatoria de 64 hex>`. La identidad no se escribe en log ni URL. El lanzador del coordinador genera y custodia esa identidad para cada ejecución.
- Se fuerza `DJANGO_SETTINGS_MODULE=config.demo_settings` y `BEAUTYTPV_DEMO_DIR`. Antes de servir se exige perfil DEMO explícito, DEBUG=False, HARDWARE_SIMULATOR=True, SQLite existente dentro del directorio de instancia, fiscal TEST, guard productivo cerrado, FISCAL_RESTORE_HOLD=True y certificado/clave vacíos tanto en settings como TechnicalSettings. La configuración fiscal de la empresa también debe ser TEST.
- El servidor rechaza arrancar con impresoras físicas habilitadas. El ciclo automático procesa exclusivamente trabajos PENDING asociados a SIMULATOR local sin terminal. Una impresora física no se consume aunque aparezca en la DB; el coordinador añade además la defensa del driver DEMO para pruebas solicitadas desde interfaz.
- Solo se ejecutan tareas de impresión simulada, recuperación segura de leases y política de backup existente. **No se importa ni ejecuta `operations_worker` ni `send_one` en el circuito DEMO**. Los registros fiscales generados por cobro permanecen pendientes, sin transmisiones inventadas.
- Un audit hook exclusivo de este proceso bloquea `socket.getaddrinfo` y `socket.connect` hacia destinos externos antes de DNS/conexión. Solo admite loopback. No altera el comportamiento del servicio productivo.
- Hay heartbeat de servicio, simulador y tareas locales; el código identifica que las tareas DEMO carecen de transporte fiscal. Mantenimiento pausa la impresión, sin recobrar ni reemitir.

## Identidad y parada

`GET /__demo_ready__` requiere cabecera `X-BeautyTPV-Demo` con la identidad exacta. Devuelve `{demo:true,pid,identity:sha256(token),mode:"TEST"}` con no-store. Cabecera ausente/incorrecta, texto no ASCII o método distinto de GET producen 404; clientes no locales producen403. El resto de rutas pasa a Django con sus controles habituales.

`WindowsEvent(token, create=True)` crea una señal manual-reset bajo `Local\BeautyTPV-DEMO-<token>`. Si ya existe rechaza reutilizarla. `create=False` abre una señal existente con permisos mínimos. Métodos públicos: `set()`, `wait(timeout_seconds)` y `close()`, además de contexto `with`.

El monitor espera esa señal y cierra Waitress mediante el cierre ya disponible en `scripts/service.py`; los hilos locales se detienen y se cierran las conexiones. No se buscan procesos Python ni se usa `taskkill`. El lanzador externo debe validar PID+creación+readiness antes de abrir/señalar el evento; esta responsabilidad permanece en el archivo del coordinador.

## Pruebas de esta entrega

`python -m pytest -q tests/test_demo_server.py`: **29 PASS, 2,16s**. Ruff check y format correctos.

Incluye evento Windows real con dos identidades independientes; cabecera privada/nonce/Unicode y alcance localhost del wrapper; bloqueo real de API `socket.getaddrinfo` en subproceso antes de resolver AEAT; rechazo de perfil productivo/certificados/DB fuera de DEMO; ciclo real sobre ORM que consume solo el simulador, conserva trabajo físico PENDING y verifica cero FiscalTransmission. El proceso de prueba no usa una impresora ni hace una petición AEAT.

El coordinador verifica aparte el ciclo completo del lanzador, puerto ocupado, HTTP/estáticos, parada real y navegación con el perfil/semilla definitivo. Estas pruebas unitarias no afirman esas comprobaciones operacionales, hardware físico ni ejecución en todas las versiones de Windows10/11.
