import io
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.accounts.permissions import require_role
from apps.audit.services import record
from apps.core.models import CompanySettings

from .models import Invoice, InvoiceLine, InvoiceSequence, Refund


def production_guard(company, *, mode=None):
    if (mode or company.fiscal_mode) == "PRODUCTION":
        if not getattr(settings, "FISCAL_PRODUCTION_APPROVED", False):
            raise ValidationError(
                "Facturación productiva bloqueada: completar validación AEAT y revisión experta."
            )
        if not getattr(settings, "FISCAL_APPROVAL_EVIDENCE", ""):
            raise ValidationError("Falta evidencia de aprobación fiscal productiva.")
        if not all(
            [
                company.name,
                company.tax_id,
                company.address,
                company.producer_name,
                company.producer_tax_id,
            ]
        ):
            raise ValidationError("Datos fiscales/productor incompletos.")


def _number(series, year):
    sequence, _ = InvoiceSequence.objects.get_or_create(series=series, year=year)
    InvoiceSequence.objects.filter(pk=sequence.pk).update(next_number=F("next_number") + 1)
    sequence.refresh_from_db()
    return sequence.next_number - 1


@transaction.atomic
def issue_invoice(sale, actor):
    from apps.core.guards import require_operational

    require_operational()
    require_role(actor, "EMPLOYEE")
    existing = Invoice.objects.filter(sale=sale).first()
    if existing:
        return existing
    company = CompanySettings.load()
    production_guard(company)
    now = timezone.now().astimezone(ZoneInfo(company.timezone))
    lines = list(sale.ticket.lines.all())
    customer = sale.customer
    snapshot = (
        {key: getattr(customer, key) for key in ["name", "tax_id", "address"]} if customer else {}
    )
    complete = bool(snapshot.get("tax_id") and snapshot.get("address"))
    if not complete and sale.total > Decimal("400.00"):
        raise ValidationError(
            "Importe superior a 400 EUR: se requiere cliente con NIF y domicilio para factura completa."
        )
    series = (
        getattr(company, "full_series", "F")
        if complete
        else getattr(company, "simplified_series", "S")
    )
    issuer = {
        key: getattr(company, key)
        for key in [
            "name",
            "tax_id",
            "address",
            "timezone",
            "producer_name",
            "producer_tax_id",
            "installation_number",
        ]
    }
    from apps.support.versioning import application_version

    issuer["software_name"] = company.software_name
    issuer["software_version"] = application_version(root=settings.BASE_DIR)
    invoice = Invoice.objects.create(
        sale=sale,
        series=series,
        year=now.year,
        number=_number(series, now.year),
        invoice_type="F1" if complete else "F2",
        issued_at=now,
        issuer=issuer,
        customer=snapshot,
        total=sale.total,
        net_total=sum((line.net_total for line in lines), Decimal("0.00")),
        tax_total=sum((line.tax_total for line in lines), Decimal("0.00")),
        fiscal_mode=company.fiscal_mode,
        created_by=actor,
    )
    for line in lines:
        InvoiceLine.objects.create(
            invoice=invoice,
            **{
                key: getattr(line, key)
                for key in [
                    "description",
                    "quantity",
                    "unit_price",
                    "discount_percent",
                    "tax_rate",
                    "net_total",
                    "tax_total",
                    "total",
                ]
            },
        )
    from apps.verifactu.services import create_record

    create_record(invoice)
    record(actor, "invoice.issue", invoice.full_number)
    return invoice


@transaction.atomic
def rectify_invoice(invoice, actor, reason, method="CARD", cash_session=None, reference=""):
    from apps.core.guards import require_operational

    require_operational()
    require_role(actor, "MANAGER")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
        raise ValidationError("Indique motivo de rectificación.")
    if not isinstance(reference, str) or len(reference) > 100:
        raise ValidationError("Referencia de devolucion no valida.")
    if invoice.rectifies_id or invoice.rectifications.exists():
        raise ValidationError("Esta factura ya está rectificada o es rectificativa.")
    if method not in ("CASH", "CARD"):
        raise ValidationError("Método de devolución inválido.")
    if method == "CASH":
        from apps.cash.models import CashSession

        cash_session = CashSession.objects.filter(pk=getattr(cash_session, "pk", None)).first()
        if not cash_session or cash_session.closed_at:
            raise ValidationError("Se requiere caja abierta para devolución en efectivo.")
        if cash_session.expected_balance < invoice.total:
            raise ValidationError("Saldo insuficiente para devolución en efectivo.")
    if method == "CARD" and not reference.strip():
        raise ValidationError("Confirme referencia de devolución del datáfono.")
    company = CompanySettings.load()
    production_guard(company, mode=invoice.fiscal_mode)
    # First writer is the sequence CAS; no SQLite row-lock assumption.
    now = timezone.now().astimezone(ZoneInfo(company.timezone))
    series = getattr(company, "rectification_series", "R")
    number = _number(series, now.year)
    if Invoice.objects.filter(rectifies=invoice).exists():
        raise ValidationError("Factura ya rectificada.")
    rectification = Invoice.objects.create(
        series=series,
        year=now.year,
        number=number,
        invoice_type="R5" if invoice.invoice_type == "F2" else "R1",
        issued_at=now,
        issuer=invoice.issuer,
        customer=invoice.customer,
        total=-invoice.total,
        net_total=-invoice.net_total,
        tax_total=-invoice.tax_total,
        rectifies=invoice,
        reason=reason,
        fiscal_mode=invoice.fiscal_mode,
        created_by=actor,
    )
    for line in invoice.lines.all():
        values = {
            key: getattr(line, key)
            for key in ["description", "unit_price", "discount_percent", "tax_rate"]
        }
        values.update(
            {key: -getattr(line, key) for key in ["quantity", "net_total", "tax_total", "total"]}
        )
        InvoiceLine.objects.create(invoice=rectification, **values)
    Refund.objects.create(
        invoice=rectification,
        method=method,
        amount=invoice.total,
        cash_session=cash_session if method == "CASH" else None,
        reference=reference,
        actor=actor,
    )
    from apps.verifactu.services import create_record

    create_record(rectification)
    record(actor, "invoice.rectify", rectification.full_number)
    return rectification


def render_pdf(invoice):
    from xml.sax.saxutils import escape

    import qrcode
    from qrcode.constants import ERROR_CORRECT_M
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    from apps.verifactu.protocol import fiscal_date, qr_url

    target = io.BytesIO()
    styles = getSampleStyleSheet()
    elements = []
    if invoice.fiscal_mode == "TEST":
        elements.append(Paragraph("PRUEBAS - SIN VALIDEZ FISCAL PRODUCTIVA", styles["Heading2"]))
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=4)
    qr.add_data(qr_url(invoice))
    qr.make(fit=True)
    picture = io.BytesIO()
    qr.make_image().save(picture, format="PNG")
    picture.seek(0)
    elements.extend(
        [
            Paragraph("QR tributario:", styles["Normal"]),
            Image(picture, 35 * mm, 35 * mm),
            Paragraph("VERI*FACTU", styles["Normal"]),
            Spacer(1, 5 * mm),
        ]
    )
    for text in [
        f"Factura {invoice.full_number}",
        f"Fecha: {fiscal_date(invoice)}",
        f"{invoice.issuer.get('name', '')} - NIF {invoice.issuer.get('tax_id', '')}",
        invoice.issuer.get("address", ""),
        f"Cliente: {invoice.customer.get('name', '')} {invoice.customer.get('tax_id', '')}",
        invoice.customer.get("address", ""),
    ]:
        elements.append(Paragraph(escape(text), styles["Normal"]))
    if invoice.rectifies_id:
        elements.append(
            Paragraph(
                escape(f"Rectifica {invoice.rectifies.full_number}: {invoice.reason}"),
                styles["Normal"],
            )
        )
    elements.append(Spacer(1, 5 * mm))
    rows = [["Concepto", "Cantidad", "IVA", "Total EUR"]]
    groups = {}
    for line in invoice.lines.all():
        net, tax = groups.get(line.tax_rate, (Decimal("0"), Decimal("0")))
        groups[line.tax_rate] = (net + line.net_total, tax + line.tax_total)
        rows.append(
            [
                Paragraph(
                    escape(line.description)
                    + f"<br/>Precio unitario IVA incl.: {line.unit_price:.2f} EUR; descuento: {line.discount_percent}%",
                    styles["Normal"],
                ),
                str(line.quantity),
                f"{line.tax_rate}%",
                f"{line.total:.2f}",
            ]
        )
    for rate, (net, tax) in sorted(groups.items()):
        rows.append([f"IVA {rate}% - base {net:.2f} EUR", "", "Cuota", f"{tax:.2f}"])
    rows += [
        ["Base", "", "", f"{invoice.net_total:.2f}"],
        ["Cuota IVA", "", "", f"{invoice.tax_total:.2f}"],
        ["TOTAL EUR", "", "", f"{invoice.total:.2f}"],
    ]
    table = Table(rows, colWidths=[95 * mm, 25 * mm, 20 * mm, 30 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9ecef")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    elements.append(table)
    SimpleDocTemplate(target, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm).build(elements)
    return target.getvalue()
