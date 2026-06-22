"""High-level service fingerprinting."""

from __future__ import annotations

from network_inventory.fingerprint.banners import collect_banners
from network_inventory.fingerprint.http_fingerprint import fingerprint_http
from network_inventory.inventory.device import Device

HTTP_PORTS = {80, 443, 8080, 8443}


def fingerprint_services(device: Device, timeout: float = 1.0) -> None:
    """Populate a device with service fingerprints."""
    services: dict[str, object] = {}

    banners = collect_banners(
        device.ip,
        [port for port in device.open_ports if port not in HTTP_PORTS],
        timeout,
    )
    if banners:
        services["banners"] = banners

    http = {}
    for port in device.open_ports:
        if port in HTTP_PORTS:
            http[port] = fingerprint_http(device.ip, port, timeout=max(timeout, 2.0))
    if http:
        services["http"] = http

    device.services = services
