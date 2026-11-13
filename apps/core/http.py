from django.core.exceptions import ValidationError


def form_pk(value):
    try:
        if (
            not isinstance(value, str)
            or not value.isascii()
            or not value.isdigit()
            or len(value) > 19
        ):
            raise ValueError
        identifier = int(value)
        if not 0 < identifier < 2**63:
            raise ValueError
        return identifier
    except (TypeError, ValueError):
        raise ValidationError("Identificador no valido.") from None
