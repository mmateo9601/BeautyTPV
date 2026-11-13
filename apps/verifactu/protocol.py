"""AEAT tike v1.0 protocol. Sources and checksums: schemas/aeat/."""

import hashlib
from decimal import Decimal
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


def build_xml(
    invoice,
    previous,
    generated_at,
    fingerprint,
    record_type="ALTA",
    correction=False,
    without_previous=False,
    rejected_previous=True,
):
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
            if rejected_previous:
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
    elif record_type == "ANULACION":
        if without_previous:
            child(entry, "SinRegistroPrevio", "S")
        if correction and rejected_previous:
            child(entry, "RechazoPrevio", "S")
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
    from apps.core.models import CompanySettings
    from apps.support.versioning import application_version

    company = CompanySettings.load()
    producer = getattr(settings, "FISCAL_PRODUCER", {}) or {
        "name": company.producer_name,
        "tax_id": company.producer_tax_id,
        "installation_id": company.installation_number,
    }
    for key, value in [
        ("NombreRazon", producer.get("name", "PENDIENTE CONFIGURAR")),
        ("NIF", producer.get("tax_id", "")),
        ("NombreSistemaInformatico", company.software_name),
        ("IdSistemaInformatico", "BT"),
        ("Version", application_version(root=settings.BASE_DIR)),
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


def validate_response(content, invoice, record_type="ALTA"):
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
    operations = results[0].xpath(
        "./*[local-name()='RespuestaLinea']/*[local-name()='Operacion']/*[local-name()='TipoOperacion']/text()"
    )
    if operations != ["Alta" if record_type == "ALTA" else "Anulacion"]:
        raise ValueError("Respuesta fiscal de operacion distinta.")
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


def response_wait_seconds(content):
    """AEAT service specification 1.0.3, section 6.4.4.1 flow control."""
    root = etree.fromstring(content, etree.XMLParser(resolve_entities=False, no_network=True))
    values = root.xpath("//*[local-name()='TiempoEsperaEnvio']/text()")
    if len(values) != 1 or not values[0].isdigit():
        raise ValueError("Respuesta fiscal sin espera de flujo valida.")
    return int(values[0])


def verify_record_snapshot(record, previous):
    """Compare stored XML, its hash inputs and the immutable invoice snapshot.

    This detects inconsistent local data; it cannot authenticate an attacker who
    rewrites the entire database and its history. External evidence remains required.
    """
    namespaces = {"sf": SF, "lr": LR}
    root = etree.fromstring(
        record.xml.encode(), etree.XMLParser(resolve_entities=False, no_network=True)
    )
    if root.tag != f"{{{LR}}}RegFactuSistemaFacturacion":
        return False
    entries = root.findall("lr:RegistroFactura/*", namespaces)
    if len(entries) != 1 or record.record_type not in HASH_FIELDS:
        return False
    entry = entries[0]
    expected_tag = "RegistroAlta" if record.record_type == "ALTA" else "RegistroAnulacion"
    if entry.tag != f"{{{SF}}}{expected_tag}":
        return False

    def text(parent, path):
        matches = parent.findall(path, namespaces)
        if len(matches) != 1:
            raise ValueError("Campo fiscal ausente o duplicado.")
        return matches[0].text or ""

    invoice = record.invoice
    suffix = "Anulada" if record.record_type == "ANULACION" else ""
    values = {
        "IDEmisorFactura" + suffix: invoice.issuer.get("tax_id", ""),
        "NumSerieFactura" + suffix: invoice.full_number,
        "FechaExpedicionFactura" + suffix: fiscal_date(invoice),
        "TipoFactura": invoice.invoice_type,
        "CuotaTotal": format(invoice.tax_total, ".2f"),
        "ImporteTotal": format(invoice.total, ".2f"),
        "Huella": previous.fingerprint if previous else "",
        "FechaHoraHusoGenRegistro": record.generated_at,
    }
    canonical, fingerprint = canonical_hash(values, record.record_type)
    if record.canonical_payload != canonical or record.fingerprint != fingerprint:
        return False
    for key in HASH_FIELDS[record.record_type]:
        if key == "Huella":
            continue
        path = (
            "sf:IDFactura/sf:" + key
            if key.startswith(("IDEmisor", "NumSerie", "FechaExpedicion"))
            else "sf:" + key
        )
        if text(entry, path) != values[key]:
            return False
    if text(entry, "sf:Huella") != fingerprint:
        return False
    if text(root, "lr:Cabecera/sf:ObligadoEmision/sf:NIF") != invoice.issuer.get("tax_id", ""):
        return False
    if text(root, "lr:Cabecera/sf:ObligadoEmision/sf:NombreRazon") != invoice.issuer.get(
        "name", ""
    ):
        return False
    if previous:
        expected = {
            "IDEmisorFactura": previous.invoice.issuer.get("tax_id", ""),
            "NumSerieFactura": previous.invoice.full_number,
            "FechaExpedicionFactura": fiscal_date(previous.invoice),
            "Huella": previous.fingerprint,
        }
        for key, value in expected.items():
            if text(entry, "sf:Encadenamiento/sf:RegistroAnterior/sf:" + key) != value:
                return False
    elif text(entry, "sf:Encadenamiento/sf:PrimerRegistro") != "S":
        return False
    if record.record_type == "ALTA":
        if text(entry, "sf:NombreRazonEmisor") != invoice.issuer.get("name", ""):
            return False
        if text(entry, "sf:DescripcionOperacion") != (
            invoice.reason or "Servicios y productos de estética"
        ):
            return False
        if invoice.invoice_type in ("F1", "R1") and invoice.customer.get("tax_id"):
            for key, value in {
                "NombreRazon": invoice.customer["name"],
                "NIF": invoice.customer["tax_id"],
            }.items():
                if text(entry, "sf:Destinatarios/sf:IDDestinatario/sf:" + key) != value:
                    return False
        if invoice.rectifies_id:
            if text(entry, "sf:TipoRectificativa") != "I":
                return False
            for key, value in {
                "IDEmisorFactura": invoice.rectifies.issuer.get("tax_id", ""),
                "NumSerieFactura": invoice.rectifies.full_number,
                "FechaExpedicionFactura": fiscal_date(invoice.rectifies),
            }.items():
                if (
                    text(entry, "sf:FacturasRectificadas/sf:IDFacturaRectificada/sf:" + key)
                    != value
                ):
                    return False
        expected_groups = {}
        for line in invoice.lines.all():
            net, tax = expected_groups.get(line.tax_rate, (Decimal("0"), Decimal("0")))
            expected_groups[line.tax_rate] = (net + line.net_total, tax + line.tax_total)
        actual_groups = {}
        for row in entry.findall("sf:Desglose/sf:DetalleDesglose", namespaces):
            if any(
                text(row, "sf:" + key) != value
                for key, value in {
                    "Impuesto": "01",
                    "ClaveRegimen": "01",
                    "CalificacionOperacion": "S1",
                }.items()
            ):
                return False
            rate = Decimal(text(row, "sf:TipoImpositivo"))
            if rate in actual_groups:
                return False
            actual_groups[rate] = (
                Decimal(text(row, "sf:BaseImponibleOimporteNoSujeto")),
                Decimal(text(row, "sf:CuotaRepercutida")),
            )
        if expected_groups != actual_groups:
            return False
        totals = list(invoice.lines.all())
        if sum((line.total for line in totals), Decimal("0")) != invoice.total:
            return False
        if sum((line.net_total for line in totals), Decimal("0")) != invoice.net_total:
            return False
        if sum((line.tax_total for line in totals), Decimal("0")) != invoice.tax_total:
            return False
    return True
