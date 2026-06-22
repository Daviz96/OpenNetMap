"""ARP and host discovery scanner."""

from __future__ import annotations

import ipaddress
import platform
import re
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from network_inventory.inventory.device import Device
from network_inventory.utils.logger import get_logger

LOGGER = get_logger(__name__)


def scan_subnet(subnet: str, threads: int = 100, timeout: float = 1.0) -> list[Device]:
    """Discover active hosts in a subnet.

    The scanner first attempts a Scapy ARP scan. If Scapy is unavailable or the
    process lacks packet privileges, it falls back to concurrent ICMP ping plus
    local ARP cache parsing.
    """
    scapy_devices = _scan_with_scapy(subnet, timeout)
    if scapy_devices:
        return scapy_devices

    LOGGER.info("Using ping fallback scanner.")
    return _scan_with_ping(subnet, threads, timeout)


def reverse_dns(ip: str) -> str | None:
    """Resolve a hostname through reverse DNS."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except (OSError, socket.herror):
        return None


def _scan_with_scapy(subnet: str, timeout: float) -> list[Device]:
    try:
        from scapy.all import ARP, Ether, srp  # type: ignore
    except ImportError:
        return []

    try:
        packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)
        answered, _ = srp(packet, timeout=timeout, verbose=False)
    except Exception as exc:
        LOGGER.debug("Scapy ARP scan failed: %s", exc)
        return []

    devices: list[Device] = []
    for _, received in answered:
        devices.append(
            Device(
                ip=received.psrc,
                mac=received.hwsrc,
                hostname=reverse_dns(received.psrc),
                response_time_ms=None,
            )
        )
    return sorted(devices, key=lambda device: ipaddress.ip_address(device.ip))


def _scan_with_ping(subnet: str, threads: int, timeout: float) -> list[Device]:
    network = ipaddress.ip_network(subnet, strict=False)
    hosts = [str(host) for host in network.hosts()]
    devices: list[Device] = []

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(_ping_host, host, timeout): host for host in hosts}
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                devices.append(result)

    macs = _arp_cache()
    for device in devices:
        device.mac = macs.get(device.ip)
        device.hostname = reverse_dns(device.ip)

    return sorted(devices, key=lambda device: ipaddress.ip_address(device.ip))


def _ping_host(ip: str, timeout: float) -> Device | None:
    system = platform.system().lower()
    timeout_ms = max(int(timeout * 1000), 100)
    if "windows" in system:
        command = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    else:
        command = ["ping", "-c", "1", "-W", str(max(int(timeout), 1)), ip]

    start = time.perf_counter()
    try:
        completed = subprocess.run(command, capture_output=True, check=False, text=True, timeout=timeout + 1)
    except (OSError, subprocess.SubprocessError):
        return None
    elapsed = (time.perf_counter() - start) * 1000
    if completed.returncode == 0:
        return Device(ip=ip, response_time_ms=round(elapsed, 2))
    return None


def _arp_cache() -> dict[str, str]:
    try:
        output = subprocess.run(["arp", "-a"], capture_output=True, check=False, text=True, timeout=3).stdout
    except (OSError, subprocess.SubprocessError):
        return {}

    entries: dict[str, str] = {}
    for line in output.splitlines():
        match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:-]{11,17})", line)
        if match:
            entries[match.group(1)] = match.group(2).replace("-", ":").lower()
    return entries

