# Verificación independiente del lanzador DEMO Windows

Fecha: 15-11-2026. Alcance: instalación sintética aislada, arranque y parada de la DEMO; no se aprueba producción fiscal ni hardware físico.

## Pruebas de seguridad de ciclo de vida

Archivo propietario: `tests/test_windows_demo.py`. Los datos de prueba se crean en `tmp_path`; no se utiliza la instancia real de LOCALAPPDATA. Ningún valor de contraseña, PIN o clave aparece en los mensajes de aserción.

| Requisito | Prueba ejecutada | Condición verificada |
|---|---|---|
| No reutilizar una configuración ajena | `test_setup_refuses_an_unrelated_existing_configuration` | Marker ajeno y fichero centinela byte a byte intactos; no aparece SQLite DEMO |
| Reinicialización exclusivamente explícita | `test_reset_requires_explicit_confirmation_without_mutating_instance` | Confirmación incorrecta no crea ni elimina datos |
| No heredar base/certificados/productivo | `test_setup_does_not_follow_a_database_inherited_from_environment` | Configuración heredada hostil se ignora; centinela principal intacto y nueva DB DEMO separada |
| No resetear al iniciar/configurar de nuevo | `test_repeated_setup_preserves_the_existing_demo_database` | Tabla centinela persiste tras repetir setup |
| No cerrar procesos Python ajenos | `test_stale_state_cannot_stop_an_unrelated_python_process` | PID creado por el test con tiempo de creación incorrecto permanece vivo después de stop |
| No escribir mediante enlaces físicos a datos ajenos | `test_configuration_guard_rejects_hardlinks_before_any_write` (dos archivos) y `test_setup_rejects_a_hardlinked_database_before_migrating_it` | Guard rechaza hardlinks a SQLite y credenciales; migración no altera SQLite centinela externa |

El proceso centinela del último caso se termina únicamente mediante el objeto Popen creado por la propia prueba, en su limpieza. No se mata por nombre, puerto ni enumeración global.

## Revisión independiente inicial del servidor

`scripts/demo_server.py` usa Waitress en 127.0.0.1:8000; el readiness requiere un token por cabecera y devuelve su huella, no su valor. La parada es cooperativa por evento Windows con identidad aleatoria. El proceso no inicia workers fiscales y su bucle de impresión selecciona únicamente SIMULATOR sin terminal remota. El hook de red se instala en el proceso DEMO y rechaza DNS/conexiones externas; no se instala globalmente al importar el módulo en pytest.

Esta revisión estática no prueba por sí sola el arranque, HTTP ni el comportamiento de un acceso directo. El coordinador debe registrar pruebas reales de inicio/doble inicio/puerto ocupado/parada/reinicio, ACL, navegación y fiscal sin envíos. Las pruebas de servicios del servidor y semilla son archivos de sus propietarios, no sustituyen las comprobaciones independientes anteriores.

## Defecto independiente encontrado y corregido

La primera versión de `scripts/demo_config.py::read_configuration` solo rechazaba symlinks y junctions. Una SQLite externa podía tener un enlace físico dentro de DEMO y pasar a `migrate` antes de que el guard de la semilla comprobara `st_nlink`. El mismo problema afectaba al archivo de credenciales.

Se reprodujo con dos hardlinks reales en carpetas temporales: **2 FAIL, DID NOT RAISE**, comunicado al coordinador sin cambiar sus fuentes. El coordinador añadió la validación `st_nlink == 1` antes de migrar/escribir y extendió la protección a otros artefactos locales. Las tres regresiones correspondientes pasan ahora y los centinelas externos permanecen intactos. No se alteró una instalación real.

Se señaló también la normalización de mayúsculas de Windows para el nombre del mutex por ruta; el coordinador aplicó `os.path.normcase`. No se afirma prueba de concurrencia por dos capitalizaciones distintas solo por revisar ese cambio.

## Resultados ejecutados

- `pytest -q tests/test_windows_demo.py --junitxml=docs/evidence/demo-qa-tests.xml -o junit_family=xunit1`: **8 PASS, 60,50 s**, sin omitidos ni fallos.
- Ruff check y format del archivo: correctos.
- Evidencia: [JUnit independiente](../evidence/demo-qa-tests.xml).
- Una ejecución previa de los cinco casos sin hardlinks pasó en58,32s. El sandbox impedía crear enlaces físicos con WinError5; los casos de hardlinks se ejecutaron fuera del sandbox, en TEMP y sin usar LOCALAPPDATA real.

No se afirma que estos ocho tests creen accesos directos o naveguen por la aplicación. Inicio/HTTP/parada/reinicio/navegación y ubicaciones exactas de `.lnk` reales corresponden al smoke del coordinador, registrado en la guía de Windows. No se ha enviado ningún registro AEAT ni utilizado hardware físico en esta verificación independiente.
