"""Tests for the score-based device classifier."""

from network_inventory.fingerprint.classifier import classify_with_details
from network_inventory.inventory.device import Device


def _device(**kwargs) -> Device:
    return Device(ip="192.168.1.1", **kwargs)


# --- Classificazione per porte ---


def test_classifier_printer_by_print_port():
    device = _device(open_ports=[9100])
    result = classify_with_details(device)
    assert result.device_type == "Stampante"
    assert result.confidence > 0


def test_classifier_printer_by_ipp_port():
    device = _device(open_ports=[631])
    result = classify_with_details(device)
    assert result.device_type == "Stampante"


def test_classifier_windows_pc_by_rdp_and_smb():
    device = _device(open_ports=[3389, 445, 135])
    result = classify_with_details(device)
    assert result.device_type == "PC Windows"
    assert result.os_guess == "Windows"


def test_classifier_router_by_dns_port():
    device = _device(open_ports=[53, 80])
    result = classify_with_details(device)
    assert result.device_type == "Router"


def test_classifier_access_point_by_discovery_port():
    device = _device(open_ports=[10001])
    result = classify_with_details(device)
    assert result.device_type == "Access Point"


def test_classifier_linux_server_by_ssh():
    device = _device(open_ports=[22])
    result = classify_with_details(device)
    assert result.device_type in {"PC Linux", "Server"}
    assert result.os_guess == "Unix/Linux"


# --- Classificazione per keyword vendor/hostname ---


def test_classifier_printer_by_vendor_epson():
    device = _device(vendor="Epson Corporation")
    result = classify_with_details(device)
    assert result.device_type == "Stampante"


def test_classifier_router_by_hostname_mikrotik():
    device = _device(hostname="MikroTik-router")
    result = classify_with_details(device)
    assert result.device_type == "Router"


def test_classifier_access_point_by_vendor_unifi():
    device = _device(vendor="Ubiquiti", hostname="UniFi U6 Pro")
    result = classify_with_details(device)
    assert result.device_type == "Access Point"


def test_classifier_nas_by_vendor_synology():
    device = _device(vendor="Synology", open_ports=[445])
    result = classify_with_details(device)
    assert result.device_type == "NAS"


def test_classifier_camera_by_vendor_hikvision():
    device = _device(vendor="Hikvision", open_ports=[80])
    result = classify_with_details(device)
    assert result.device_type == "Telecamera IP"


def test_classifier_mac_by_vendor_apple():
    device = _device(vendor="Apple, Inc.")
    result = classify_with_details(device)
    assert result.device_type == "Mac"
    assert result.os_guess == "Apple"


def test_classifier_iot_by_keyword():
    device = _device(hostname="shelly-device-1")
    result = classify_with_details(device)
    assert result.device_type == "Dispositivo IoT"


# --- Caso limite: nessuna informazione ---


def test_classifier_unknown_when_no_data():
    device = _device()
    result = classify_with_details(device)
    assert result.device_type == "Dispositivo sconosciuto"
    assert result.confidence == 0.0
    assert result.os_guess is None


# --- Reasons e confidence ---


def test_classifier_returns_reasons():
    device = _device(open_ports=[9100], vendor="Brother Industries")
    result = classify_with_details(device)
    assert len(result.reasons) > 0


def test_classifier_confidence_is_normalized():
    device = _device(open_ports=[3389, 445, 135], vendor="Microsoft")
    result = classify_with_details(device)
    assert 0.0 <= result.confidence <= 1.0
