"""Score-based device classifier."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from network_inventory.inventory.device import Device


@dataclass(slots=True)
class ClassificationResult:
    """Classification result with explainability."""

    device_type: str
    os_guess: str | None
    confidence: float
    reasons: list[str]


def classify(device: Device) -> tuple[str, str | None]:
    """Classify a device using vendor, hostname, ports, banners and protocol data."""
    result = classify_with_details(device)
    return result.device_type, result.os_guess


def classify_with_details(device: Device) -> ClassificationResult:
    """Classify a device and return confidence plus reasons."""
    scores: dict[str, int] = defaultdict(int)
    reasons: dict[str, list[str]] = defaultdict(list)
    haystack = " ".join(
        str(value).lower()
        for value in [
            device.vendor,
            device.hostname,
            device.services,
            device.snmp_info,
            device.mdns_info,
            device.netbios_info,
        ]
        if value
    )
    ports = set(device.open_ports)

    _score_ports(scores, reasons, ports)
    _score_text(scores, reasons, haystack)

    if device.snmp_info:
        scores["network_device"] += 20
        reasons["network_device"].append("SNMP disponibile")
        if "printer" in haystack or "laserjet" in haystack:
            scores["printer"] += 35
            reasons["printer"].append("SNMP contiene indizi stampante")

    if 445 in ports or 139 in ports:
        if device.netbios_info:
            scores["windows_pc"] += 35
            reasons["windows_pc"].append("NetBIOS/SMB presente")
        scores["nas"] += 10
        reasons["nas"].append("SMB presente")

    if not scores:
        return ClassificationResult("unknown", None, 0.0, [])

    device_type, best_score = max(scores.items(), key=lambda item: item[1])
    total_score = max(sum(score for score in scores.values() if score > 0), 1)
    confidence = round(min(best_score / total_score, 1.0), 2)
    os_guess = _guess_os(haystack, ports)
    return ClassificationResult(_normalize_type(device_type), os_guess, confidence, reasons[device_type])


def _score_ports(scores: dict[str, int], reasons: dict[str, list[str]], ports: set[int]) -> None:
    if 9100 in ports or 515 in ports or 631 in ports:
        scores["printer"] += 50
        reasons["printer"].append("porte stampa aperte")
    if 3389 in ports or 135 in ports:
        scores["windows_pc"] += 45
        reasons["windows_pc"].append("porte Windows/RDP aperte")
    if 22 in ports:
        scores["linux_pc"] += 20
        scores["server"] += 20
        reasons["linux_pc"].append("SSH aperto")
        reasons["server"].append("SSH aperto")
    if 80 in ports or 443 in ports or 8080 in ports or 8443 in ports:
        scores["network_device"] += 15
        scores["camera"] += 8
        reasons["network_device"].append("interfaccia HTTP/HTTPS presente")
    if 53 in ports:
        scores["router"] += 35
        reasons["router"].append("DNS aperto")
    if 161 in ports:
        scores["switch"] += 25
        scores["router"] += 25
        reasons["switch"].append("SNMP aperto")
        reasons["router"].append("SNMP aperto")
    if 445 in ports:
        scores["windows_pc"] += 20
        scores["nas"] += 25
        reasons["windows_pc"].append("SMB aperto")
        reasons["nas"].append("SMB aperto")
    if 10001 in ports:
        scores["access_point"] += 35
        reasons["access_point"].append("porta discovery/AP aperta")


def _score_text(scores: dict[str, int], reasons: dict[str, list[str]], text: str) -> None:
    keywords = {
        "printer": ("printer", "epson", "laserjet", "brother", "canon", "xerox", "ipp", "jetdirect"),
        "router": ("router", "gateway", "mikrotik", "openwrt", "fritz", "tplink", "tp-link", "netgear"),
        "switch": ("switch", "catalyst", "procurve", "aruba", "juniper"),
        "access_point": ("unifi", "ubiquiti", "access point", "ap-", "u6 pro"),
        "nas": ("synology", "qnap", "nas", "diskstation", "truenas"),
        "camera": ("camera", "hikvision", "dahua", "axis", "rtsp"),
        "smart_tv": ("tv", "chromecast", "roku", "samsung", "lg webos"),
        "smartphone": ("iphone", "android", "pixel", "galaxy"),
        "tablet": ("ipad", "tablet"),
        "mac": ("apple", "macbook", "imac", "darwin"),
        "iot": ("iot", "esp32", "shelly", "philips hue", "sonoff"),
        "server": ("server", "ubuntu", "debian", "centos", "nginx", "apache"),
    }
    for device_type, words in keywords.items():
        for word in words:
            if word in text:
                scores[device_type] += 25
                reasons[device_type].append(f"keyword '{word}' rilevata")


def _guess_os(text: str, ports: set[int]) -> str | None:
    if any(word in text for word in ("windows", "microsoft")) or 3389 in ports:
        return "Windows"
    if any(word in text for word in ("linux", "ubuntu", "debian", "centos")):
        return "Linux"
    if any(word in text for word in ("apple", "darwin", "macos", "iphone", "ipad")):
        return "Apple"
    if 22 in ports and not ({135, 139, 445} & ports):
        return "Unix/Linux"
    return None


def _normalize_type(device_type: str) -> str:
    mapping = {
        "windows_pc": "PC Windows",
        "linux_pc": "PC Linux",
        "mac": "Mac",
        "server": "Server",
        "nas": "NAS",
        "printer": "Stampante",
        "router": "Router",
        "switch": "Switch",
        "access_point": "Access Point",
        "camera": "Telecamera IP",
        "smartphone": "Smartphone",
        "tablet": "Tablet",
        "smart_tv": "Smart TV",
        "iot": "Dispositivo IoT",
        "network_device": "Dispositivo di rete",
    }
    return mapping.get(device_type, "Dispositivo sconosciuto")
