"""AEAT tike v1.0 protocol. Sources and checksums: schemas/aeat/."""

import hashlib
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone
from lxml import etree

SF = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
LR = SF.replace("SuministroInformacion", "SuministroLR")
SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
HASH_FIELDS = {
    "ALTA": (
        "IDEmisorFactura",
        "NumSerieFactura",
        "FechaExpedicionFactura",
        "TipoFactura",
        "CuotaTotal",
        "ImporteTotal",
        "Huella",
        "FechaHoraHusoGenRegistro",
    ),
    "ANULACION": (
        "IDEmisorFacturaAnulada",
        "NumSerieFacturaAnulada",
        "FechaExpedicionFacturaAnulada",
        "Huella",
        "FechaHoraHusoGenRegistro",
    ),
}
ENDPOINTS = {
    "TEST": "https://prewww1.aeat.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP",
    "PRODUCTION": "https://www1.agenciatributaria.gob.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP",
}


def canonical_hash(values, record_type="ALTA"):
    canonical = "&".join(
        f"{key}={str(values.get(key, '')).strip()}" for key in HASH_FIELDS[record_type]
    )
    return canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


def fiscal_date(invoice):
    issued = invoice.issued_at
    if timezone.is_aware(issued):
        issued = issued.astimezone(ZoneInfo(invoice.issuer.get("timezone", "Europe/Madrid")))
    return issued.strftime("%d-%m-%Y")


def qr_url(invoice):
    host = (
        "https://prewww2.aeat.es"
        if invoice.fiscal_mode == "TEST"
        else "https://www2.agenciatributaria.gob.es"
    )
    return (
        host
        + "/wlpl/TIKE-CONT/ValidarQR?"
        + urlencode(
            {
                "nif": invoice.issuer.get("tax_id", ""),
                "numserie": invoice.full_number,
                "fecha": fiscal_date(invoice),
                "importe": format(invoice.total, ".2f"),
            }
        )
    )


def child(parent, name, value=None, namespace=SF):
    elem = etree.SubElement(parent, f"{{{namespace}}}{name}")
    if value is not None:
        elem.text = str(value)
    return elem


def build_xml(invoice, previous, generated_at, fingerprint, record_type="ALTA", correction=False):
    root = etree.Element(f"{{{LR}}}RegFactuSistemaFacturacion", nsmap={"sum": LR, "sf": SF})
    header = child(root, "Cabecera", namespace=LR)
    issuer = child(header, "ObligadoEmision")
    child(issuer, "NombreRazon", invoice.issuer.get("name", ""))
    child(issuer, "NIF", invoice.issuer.get("tax_id", ""))
    wrapper = child(root, "RegistroFactura", namespace=LR)
    entry = child(wrapper, "RegistroAlta" if record_type == "ALTA" else "RegistroAnulacion")
    child(entry, "IDVersion", "1.0")
    identity = child(entry, "IDFactura")
    suffix = "Anulada" if record_type == "ANULACION" else ""
    child(identity, "IDEmisorFactura" + suffix, invoice.issuer.get("tax_id", ""))
    child(identity, "NumSerieFactura" + suffix, invoice.full_number)
    child(identity, "FechaExpedicionFactura" + suffix, fiscal_date(invoice))
    if record_type == "ALTA":
        child(entry, "NombreRazonEmisor", invoice.issuer.get("name", ""))
        if correction:
            child(entry, "Subsanacion", "S")
            child(entry, "RechazoPrevio", "X")
        child(entry, "TipoFactura", invoice.invoice_type)
        if invoice.rectifies_id:
            child(entry, "TipoRectificativa", "I")
            refs = child(entry, "FacturasRectificadas")
            ref = child(refs, "IDFacturaRectificada")
            child(ref, "IDEmisorFactura", invoice.rectifies.issuer.get("tax_id", ""))
            child(ref, "NumSerieFactura", invoice.rectifies.full_number)
            child(ref, "FechaExpedicionFactura", fiscal_date(invoice.rectifies))
        child(entry, "DescripcionOperacion", invoice.reason or "Servicios y productos de estética")
        if invoice.invoice_type in ("F1", "R1") and invoice.customer.get("tax_id"):
            recipient = child(child(entry, "Destinatarios"), "IDDestinatario")
            child(recipient, "NombreRazon", invoice.customer["name"])
            child(recipient, "NIF", invoice.customer["tax_id"])
        detail = child(entry, "Desglose")
        groups = {}
        for line in invoice.lines.all():
            net, tax = groups.get(line.tax_rate, (0, 0))
            groups[line.tax_rate] = (net + line.net_total, tax + line.tax_total)
        for rate, (net, tax) in groups.items():
            row = child(detail, "DetalleDesglose")
            child(row, "Impuesto", "01")
            child(row, "ClaveRegimen", "01")
            child(row, "CalificacionOperacion", "S1")
            child(row, "TipoImpositivo", format(rate, ".2f"))
            child(row, "BaseImponibleOimporteNoSujeto", format(net, ".2f"))
            child(row, "CuotaRepercutida", format(tax, ".2f"))
        child(entry, "CuotaTotal", format(invoice.tax_total, ".2f"))
        child(entry, "ImporteTotal", format(invoice.total, ".2f"))
    chain = child(entry, "Encadenamiento")
    if previous:
        prev = child(chain, "RegistroAnterior")
        child(prev, "IDEmisorFactura", previous.invoice.issuer.get("tax_id", ""))
        child(prev, "NumSerieFactura", previous.invoice.full_number)
        child(prev, "FechaExpedicionFactura", fiscal_date(previous.invoice))
        child(prev, "Huella", previous.fingerprint)
    else:
        child(chain, "PrimerRegistro", "S")
    software = child(entry, "SistemaInformatico")
    producer = getattr(settings, "FISCAL_PRODUCER", {}) or {
        "name": invoice.issuer.get("producer_name", ""),
        "tax_id": invoice.issuer.get("producer_tax_id", ""),
        "installation_id": invoice.issuer.get("installation_number", "1"),
    }
    for key, value in [
        ("NombreRazon", producer.get("name", "PENDIENTE CONFIGURAR")),
        ("NIF", producer.get("tax_id", "")),
        ("NombreSistemaInformatico", "BeautyTPV"),
        ("IdSistemaInformatico", "BT"),
        ("Version", getattr(settings, "APP_VERSION", "0.1.0")),
        ("NumeroInstalacion", producer.get("installation_id", "1")),
        ("TipoUsoPosibleSoloVerifactu", "S"),
        ("TipoUsoPosibleMultiOT", "N"),
        ("IndicadorMultiplesOT", "N"),
    ]:
        child(software, key, value)
    child(entry, "FechaHoraHusoGenRegistro", generated_at)
    child(entry, "TipoHuella", "01")
    child(entry, "Huella", fingerprint)
    return etree.tostring(root, encoding="unicode")


class LocalSchemaResolver(etree.Resolver):
    def resolve(self, url, public_id, context):
        if url.endswith("xmldsig-core-schema.xsd"):
            return self.resolve_filename(
                str(Path(settings.BASE_DIR) / "schemas/aeat/xmldsig-core-schema.xsd"), context
            )
        return None


def validate_xml(xml):
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    parser.resolvers.add(LocalSchemaResolver())
    schema = etree.XMLSchema(
        etree.parse(str(Path(settings.BASE_DIR) / "schemas/aeat/SuministroLR.xsd"), parser)
    )
    document = etree.fromstring(xml.encode(), parser)
    schema.assertValid(document)
    return True


def soap_envelope(xml):
    root = etree.Element(f"{{{SOAP}}}Envelope", nsmap={"soapenv": SOAP})
    body = etree.SubElement(root, f"{{{SOAP}}}Body")
    body.append(
        etree.fromstring(xml.encode(), etree.XMLParser(resolve_entities=False, no_network=True))
    )
    return etree.tostring(root, encoding="utf-8", xml_declaration=True)


def validate_response(content, invoice):
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    parser.resolvers.add(LocalSchemaResolver())
    root = etree.fromstring(content, parser)
    results = root.xpath("//*[local-name()='RespuestaRegFactuSistemaFacturacion']")
    if len(results) != 1:
        raise ValueError("Falta respuesta SOAP fiscal oficial única.")
    schema = etree.XMLSchema(
        etree.parse(str(Path(settings.BASE_DIR) / "schemas/aeat/RespuestaSuministro.xsd"), parser)
    )
    schema.assertValid(results[0])
    identities = results[0].xpath("./*[local-name()='RespuestaLinea']/*[local-name()='IDFactura']")
    if len(identities) != 1:
        raise ValueError("Respuesta no corresponde a envío de registro único.")
    expected = {
        "IDEmisorFactura": invoice.issuer.get("tax_id", ""),
        "NumSerieFactura": invoice.full_number,
        "FechaExpedicionFactura": fiscal_date(invoice),
    }
    for key, value in expected.items():
        actual = identities[0].xpath(f"./*[local-name()='{key}']/text()")
        if actual != [value]:
            raise ValueError("Respuesta fiscal de identidad distinta.")
    return True


def parse_response(content):
    root = etree.fromstring(content, etree.XMLParser(resolve_entities=False, no_network=True))
    if root.xpath("//*[local-name()='Fault']"):
        raise ValueError("SOAP Fault recibido; revisar transmisión fiscal.")
    states = root.xpath("//*[local-name()='EstadoRegistro']/text()")
    if len(states) != 1:
        raise ValueError("Respuesta no contiene un único estado de registro.")
    state = states[0]
    if state == "Correcto":
        return "ACCEPTED", ""
    if state == "AceptadoConErrores":
        return "ACCEPTED_WITH_ERRORS", "Aceptado con errores: requiere revisión."
    if state == "Incorrecto":
        duplicate = root.xpath("//*[local-name()='EstadoRegistroDuplicado']/text()")
        if duplicate:
            return (
                "DUPLICATE_REVIEW",
                "Duplicado informado por AEAT: conciliar estado original antes de aceptar.",
            )
        codes = root.xpath("//*[local-name()='CodigoErrorRegistro']/text()")
        return "REJECTED", ", ".join(codes)[:500]
    raise ValueError("Estado AEAT desconocido.")
