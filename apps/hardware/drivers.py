import socket

from django.conf import settings
from django.core.exceptions import ValidationError


class DeliveryUnknown(Exception):
    """Device may have consumed bytes. Never retry this automatically."""


class DriverUnavailable(Exception):
    """No receipt bytes were sent; retry is safe."""


def simulator_allowed():
    demo = (
        getattr(settings, "LOCAL_DEMO_ONLY", False)
        and settings.SETTINGS_MODULE == "config.demo_settings"
    )
    return getattr(settings, "HARDWARE_SIMULATOR", False) and (settings.DEBUG or demo)


def send(printer, payload):
    payload = bytes(payload)
    if getattr(settings, "LOCAL_DEMO_ONLY", False) and printer.connection_type != "SIMULATOR":
        raise DriverUnavailable("La DEMO no envia datos a dispositivos fisicos.")
    if printer.connection_type == "SIMULATOR":
        if not simulator_allowed():
            raise DriverUnavailable("Simulador deshabilitado fuera de desarrollo")
        return len(payload)
    if printer.connection_type == "TCP":
        try:
            connection = socket.create_connection((printer.address, printer.port), timeout=5)
        except OSError as exc:
            raise DriverUnavailable("No se pudo conectar a la impresora TCP") from exc
        try:
            with connection:
                connection.settimeout(10)
                connection.sendall(payload)
        except OSError as exc:
            raise DeliveryUnknown("Conexión perdida durante envío TCP") from exc
        return len(payload)
    if printer.connection_type == "USB":
        import usb.core

        try:
            device = usb.core.find(idVendor=printer.usb_vendor, idProduct=printer.usb_product)
            if device is None:
                raise DriverUnavailable("Impresora USB no encontrada")
            device.set_configuration()
        except usb.core.USBError as exc:
            raise DriverUnavailable("USB no disponible o sin permiso") from exc
        try:
            count = device.write(printer.usb_endpoint, payload, timeout=10000)
            if count != len(payload):
                raise DeliveryUnknown("Envío USB parcial")
        except usb.core.USBError as exc:
            raise DeliveryUnknown("Error durante envío USB") from exc
        return len(payload)
    if printer.connection_type == "SERIAL":
        import serial

        try:
            device = serial.Serial(
                printer.address, baudrate=printer.port, timeout=5, write_timeout=10
            )
        except serial.SerialException as exc:
            raise DriverUnavailable("Puerto serie no disponible") from exc
        try:
            with device:
                count = device.write(payload)
                device.flush()
                if count != len(payload):
                    raise DeliveryUnknown("Envío serie parcial")
        except (serial.SerialException, OSError) as exc:
            raise DeliveryUnknown("Error durante envío serie") from exc
        return len(payload)
    raise ValidationError("Tipo de dispositivo desconocido")
