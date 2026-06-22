"""Service banner helpers."""

from __future__ import annotations

from network_inventory.scanner.port_scanner import grab_banner


def collect_banners(ip: str, ports: list[int], timeout: float = 1.0) -> dict[int, str]:
    """Collect banners for ports where this is useful."""
    banners: dict[int, str] = {}
    for port in ports:
        banner = grab_banner(ip, port, timeout)
        if banner:
            banners[port] = banner
    return banners

