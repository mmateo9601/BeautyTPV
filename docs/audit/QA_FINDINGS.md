# Verificación transversal

Referencia `4ce821e`: 112 pruebas originales ejecutadas en copia aislada. Resultado actual definitivo: consultar `../evidence/audit-final-tests.xml` y `../../AUDITORIA_COMPLETA.md`.

`tests/test_audit_matrix.py` exige una política explícita por ruta, comprueba cuatro roles y anónimo con objetos existentes, elevación, scopes PII, CSRF y enlaces visibles. Un POST inválido solo demuestra autorización y control de errores; las operaciones positivas están en `test_audit_forms.py` y Chromium.

Diez pruebas Chromium cubren los recorridos originales, recuperación de cuentas, estado en cobro, HTMX, navegación por rol, responsive y formularios técnicos de terminales, impresoras, certificado y preparación de restore. Los controles visuales complementan las aserciones, no las reemplazan.

Procesos independientes prueban dobles cobros y caída antes del commit; CLI real comprueba migración desde la referencia, backup cifrado, restore, hold y nueva instalación sin usuarios predeterminados. Benchmark local separado mide 1/3/6 procesos. No acredita rendimiento de una LAN comercial.

Validación oficial AEAT, papel/QR/cajón físicos, despliegue en destino y aceptación humana siguen BLOQUEADOS. CI remota no ejecutada; no se presenta como pasada.
