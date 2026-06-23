"""Local network discovery helpers."""

from __future__ import annotations

import ipaddress
import socket
import subprocess
from dataclasses import dataclass

import psutil


@dataclass(slots=True)
class NetworkInfo:
    """Information about the local network."""

    local_ip: str
    netmask: str
    gateway: str | None
    cidr: str


def detect_local_network() -> NetworkInfo:
    """Detect the primary local IPv4 network.

    Returns:
        Detected local network details.

    Raises:
        RuntimeError: If no usable IPv4 interface is found.
    """
    gateway = _default_gateway()
    gateway_iface = _gateway_interface(gateway)

    candidates: list[tuple[str, str, str]] = []
    for iface_name, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family != socket.AF_INET or not addr.address or not addr.netmask:
                continue
            if addr.address.startswith("127."):
                continue
            candidates.append((iface_name, addr.address, addr.netmask))

    if gateway_iface:
        candidates.sort(key=lambda item: item[0] != gateway_iface)

    if not candidates:
        raise RuntimeError("No usable IPv4 network interface found.")

    _, local_ip, netmask = candidates[0]
    network = ipaddress.IPv4Network(f"{local_ip}/{netmask}", strict=False)
    return NetworkInfo(
        local_ip=local_ip, netmask=netmask, gateway=gateway, cidr=str(network)
    )


def subnet_stats(cidr: str, active_hosts: int) -> dict[str, object]:
    """Calculate basic subnet utilization statistics."""
    network = ipaddress.ip_network(cidr, strict=False)
    total_hosts = (
        max(network.num_addresses - 2, 0)
        if network.version == 4
        else network.num_addresses
    )
    free_hosts = max(total_hosts - active_hosts, 0)
    utilization = round((active_hosts / total_hosts) * 100, 2) if total_hosts else 0.0
    return {
        "subnet": str(network),
        "total_hosts": total_hosts,
        "active_hosts": active_hosts,
        "free_hosts": free_hosts,
        "utilization_percent": utilization,
    }


def _default_gateway() -> str | None:
    stats = psutil.net_if_stats()
    if not stats:
        return None
    try:
        output = subprocess.run(
            ["route", "print", "0.0.0.0"],
            capture_output=True,
            check=False,
            text=True,
            timeout=3,
        ).stdout
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
                return parts[2]
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def _gateway_interface(gateway: str | None) -> str | None:
    if gateway is None:
        return None
    gateway_ip = ipaddress.ip_address(gateway)
    for iface_name, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family != socket.AF_INET or not addr.address or not addr.netmask:
                continue
            network = ipaddress.ip_network(
                f"{addr.address}/{addr.netmask}", strict=False
            )
            if gateway_ip in network:
                return str(iface_name)
    return None
