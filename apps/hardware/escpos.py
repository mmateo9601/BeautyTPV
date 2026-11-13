"""ESC/POS receipt bytes. Real code-page/QR/cutter compatibility requires device QA."""

import struct

INIT = b"\x1b@"
CUT = b"\x1dV\x00"
DRAWER = b"\x1bp\x00\x19\xfa"


def safe_text(value):
    # Never allow user text to inject ESC/POS control commands.
    return "".join(c for c in str(value) if ord(c) >= 32 or c == "\n")


def qr_command(value):
    data = value.encode("ascii")
    if len(data) > 2048:
        raise ValueError("QR demasiado largo")
    return (
        b"\x1d(k\x04\x001A2\x00"
        + b"\x1d(k\x03\x001C\x06"
        + b"\x1d(k\x03\x001E0"
        + b"\x1d(k"
        + struct.pack("<H", len(data) + 3)
        + b"1P0"
        + data
        + b"\x1d(k\x03\x001Q0"
    )


def render_receipt(invoice, copy=False, open_drawer=False, encoding="cp858", codepage=19):
    from apps.verifactu.protocol import qr_url

    lines = ["BeautyTPV", "COPIA" if copy else "ORIGINAL"]
    if invoice.fiscal_mode != "PRODUCTION":
        lines.append("PRUEBAS - SIN VALIDEZ FISCAL")
    lines += [
        invoice.issuer.get("name", ""),
        "NIF: " + invoice.issuer.get("tax_id", ""),
        invoice.issuer.get("address", ""),
        invoice.full_number,
        invoice.issued_at.isoformat(),
        "-" * 42,
    ]
    for line in invoice.lines.all():
        lines += [
            safe_text(line.description)[:42],
            f"{line.quantity} x {line.unit_price:.2f}  {line.total:.2f} EUR",
            f"IVA {line.tax_rate}%  Base {line.net_total:.2f} Cuota {line.tax_total:.2f}",
        ]
    lines += [
        "-" * 42,
        f"BASE {invoice.net_total:.2f} EUR",
        f"IVA {invoice.tax_total:.2f} EUR",
        f"TOTAL {invoice.total:.2f} EUR",
        "VERI*FACTU",
        "",
    ]
    content = "\n".join(safe_text(x) for x in lines).encode(encoding, errors="replace")
    return (
        INIT
        + b"\x1bt"
        + bytes([codepage])
        + content
        + qr_command(qr_url(invoice))
        + b"\n\n\n"
        + CUT
        + (DRAWER if open_drawer and not copy else b"")
    )


def render_test(encoding="cp858", codepage=19, drawer=False):
    return (
        INIT
        + b"\x1bt"
        + bytes([codepage])
        + "BeautyTPV - PRUEBA 80mm\nÁÉÍÓÚ ñ €\n".encode(encoding, errors="replace")
        + b"\n\n"
        + CUT
        + (DRAWER if drawer else b"")
    )
