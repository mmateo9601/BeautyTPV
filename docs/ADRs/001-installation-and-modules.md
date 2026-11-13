# ADR 001 — Instalación independiente y límites de módulos

Estado: aceptada para implementación inicial por mandato del PLAYBOOK; revisión de integración pendiente.

Una instalación local por empresa, Django 5.2 LTS, Bootstrap 5, HTMX, SQLite. Sin tenant, portal externo, agenda ni SaaS. Cada módulo owns sus modelos/migraciones/servicios; config integra URLs/settings. Custom User desde primera migración. Datos comerciales de Customer separados de identidad operativa.

Las dependencias se expresan mediante FK string y servicios internos. Checkout es coordinador de transacción; facturación y encolado participan sin red ni hardware. Workers producen efectos externos después del commit. Se acepta acoplamiento pos→billing→verifactu y pos→hardware; se evita importación circular mediante imports locales. Contratos completos en ../CONTRACTS.md.

Consecuencia: vender no depende de impresora/red, pero sí de que factura y outbox queden persistidos atómicamente. No hay eventos en memoria como única garantía.
