"""Inventory orchestration."""

from __future__ import annotations

import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import re

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from network_inventory.fingerprint.classifier import classify, classify_with_details
from network_inventory.fingerprint.services import fingerprint_services
from network_inventory.inventory.device import Device
from network_inventory.scanner.arp_scanner import scan_subnet
from network_inventory.scanner.mdns_scanner import scan_mdns
from network_inventory.scanner.netbios_scanner import scan_netbios
from network_inventory.scanner.port_scanner import scan_ports
from network_inventory.scanner.snmp_scanner import scan_snmp
from network_inventory.security.assessment import assess_device
from network_inventory.utils.config import ScanConfig
from network_inventory.utils.logger import get_logger
from network_inventory.utils.network import detect_local_network, subnet_stats
from network_inventory.utils.oui import OuiDatabase

LOGGER = get_logger(__name__)


class InventoryRunner:
    """Runs the full inventory pipeline."""

    def __init__(self, config: ScanConfig) -> None:
        self.config = config
        self.oui = OuiDatabase()

    def run(self) -> tuple[list[Device], dict[str, object]]:
        """Discover and fingerprint devices."""
        network_info = detect_local_network() if self.config.subnet is None else None
        subnet = self.config.subnet or network_info.cidr
        _validate_subnet_size(subnet)

        if network_info:
            LOGGER.info(
                "Local IP: %s | Netmask: %s | Gateway: %s | Subnet: %s",
                network_info.local_ip,
                network_info.netmask,
                network_info.gateway,
                network_info.cidr,
            )

        LOGGER.info("Scanning subnet %s", subnet)
        devices = scan_subnet(subnet, threads=self.config.threads, timeout=self.config.timeout)
        for device in devices:
            _mark_discovery(device)
        LOGGER.info("Discovered %d active host(s)", len(devices))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task("Fingerprinting devices", total=len(devices))
            with ThreadPoolExecutor(max_workers=max(min(self.config.threads, 64), 1)) as executor:
                futures = {executor.submit(self._fingerprint_device, device): device for device in devices}
                for future in as_completed(futures):
                    future.result()
                    progress.advance(task)

        stats = subnet_stats(subnet, len(devices))
        stats["started_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        return devices, stats

    def _fingerprint_device(self, device: Device) -> Device:
        device.vendor = self.oui.lookup(device.mac)
        device.manufacturer = device.vendor
        device.open_ports = scan_ports(
            device.ip,
            self.config.ports,
            timeout=self.config.timeout,
            threads=min(len(self.config.ports), 32),
        )
        fingerprint_services(device, timeout=self.config.timeout)

        if self.config.snmp_enabled or 161 in device.open_ports:
            device.snmp_info = scan_snmp(device.ip, timeout=self.config.timeout)
        if {5353, 80, 443} & set(device.open_ports):
            device.mdns_info = scan_mdns(device.ip, timeout=self.config.timeout)
        if {137, 139, 445} & set(device.open_ports):
            device.netbios_info = scan_netbios(device.ip, timeout=max(self.config.timeout, 2.0))

        enrich_device_identity(device)
        classification = classify_with_details(device)
        device.device_type = classification.device_type
        device.os_guess = classification.os_guess
        device.classification_confidence = classification.confidence
        device.classification_reasons = classification.reasons
        assessment = assess_device(device)
        device.security_score = assessment.score
        device.findings = assessment.findings
        device.recommendations = assessment.recommendations
        device.confidence["classification"] = classification.confidence
        device.confidence["discovery"] = device.discovery_confidence
        return device


def _validate_subnet_size(subnet: str) -> None:
    network = ipaddress.ip_network(subnet, strict=False)
    if network.version != 4:
        raise ValueError("Only IPv4 subnets are supported.")
    if network.num_addresses > 4096:
        raise ValueError("Subnet too large for the default scanner. Use /20 or smaller.")


def _mark_discovery(device: Device) -> None:
    methods = []
    if device.mac:
        methods.append("arp")
    if device.response_time_ms is not None:
        methods.append("icmp")
    if device.hostname:
        methods.append("reverse_dns")
    if not methods:
        methods.append("unknown")
    device.discovery_methods = methods
    known_methods = [method for method in methods if method != "unknown"]
    device.discovery_confidence = round(min(0.35 + (0.25 * len(known_methods)), 0.95), 2)
    device.sources["ip"] = methods.copy()
    if device.mac:
        device.sources["mac"] = ["arp_cache_or_arp_scan"]
    if device.hostname:
        device.sources["hostname"] = ["reverse_dns"]


def enrich_device_identity(device: Device) -> None:
    """Fill manufacturer, model and firmware when protocol metadata allows it."""
    text = " ".join(
        str(value)
        for value in [device.vendor, device.snmp_info, device.services, device.hostname]
        if value
    )
    if not device.manufacturer:
        device.manufacturer = device.vendor
    for marker in [
        "Epson",
        "Cisco",
        "UniFi",
        "Ubiquiti",
        "Synology",
        "Mikrotik",
        "MicroTik",
        "HP",
        "Hewlett Packard",
        "Brother",
        "Canon",
        "Zebra",
        "Dahua",
        "Hikvision",
        "Axis",
        "Microsoft",
        "Apple",
        "Dell",
        "Lenovo",
    ]:
        if marker.lower() in text.lower():
            device.manufacturer = marker
            break
    if not device.model and "description" in device.snmp_info:
        device.model = str(device.snmp_info["description"])[:120]
    if not device.model:
        device.model = _model_from_services(device.services)
    if not device.firmware and "firmware" in device.snmp_info:
        device.firmware = str(device.snmp_info["firmware"])


def _model_from_services(services: dict[str, object]) -> str | None:
    http = services.get("http")
    if not isinstance(http, dict):
        return None

    candidates: list[str] = []
    for metadata in http.values():
        if not isinstance(metadata, dict):
            continue
        for key in ("title", "www_authenticate", "server"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                candidates.append(value.strip())

    for candidate in candidates:
        model = _clean_model(candidate)
        if model:
            return model
    return None


def _clean_model(value: str) -> str | None:
    text = re.sub(r"\s+", " ", value).strip()
    text = re.sub(r"^Basic realm=", "", text).strip("\" ")
    text = re.sub(r"^Digest .*realm=", "", text).strip("\" ")
    ignored = {
        "app-webs/",
        "login",
        "login page",
        "log on",
        "secure area",
        "webserver",
    }
    lower = text.lower()
    if not text or lower in ignored or lower.startswith(("error ", "iis", "apache", "nginx", "microsoft-iis", "jetty")):
        return None
    return text[:120]
