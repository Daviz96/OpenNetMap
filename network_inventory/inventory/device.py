"""Device model used by the inventory pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Return the current UTC timestamp as ISO 8601 text."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class Device:
    """Represents a discovered network device."""

    ip: str
    mac: str | None = None
    vendor: str | None = None
    hostname: str | None = None
    device_type: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    firmware: str | None = None
    open_ports: list[int] = field(default_factory=list)
    services: dict[str, object] = field(default_factory=dict)
    snmp_info: dict[str, object] = field(default_factory=dict)
    mdns_info: dict[str, object] = field(default_factory=dict)
    netbios_info: dict[str, object] = field(default_factory=dict)
    tls_info: dict[str, object] = field(default_factory=dict)
    os_guess: str | None = None
    response_time_ms: float | None = None
    discovery_methods: list[str] = field(default_factory=list)
    discovery_confidence: float = 0.0
    first_seen: str = field(default_factory=utc_now_iso)
    last_seen: str = field(default_factory=utc_now_iso)
    classification_confidence: float = 0.0
    classification_reasons: list[str] = field(default_factory=list)
    security_score: int = 100
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    confidence: dict[str, float] = field(default_factory=dict)
    sources: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "ip": self.ip,
            "mac": self.mac,
            "vendor": self.vendor,
            "hostname": self.hostname,
            "device_type": self.device_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "firmware": self.firmware,
            "open_ports": self.open_ports,
            "services": self.services,
            "snmp_info": self.snmp_info,
            "mdns_info": self.mdns_info,
            "netbios_info": self.netbios_info,
            "tls_info": self.tls_info,
            "os_guess": self.os_guess,
            "response_time_ms": self.response_time_ms,
            "discovery_methods": self.discovery_methods,
            "discovery_confidence": self.discovery_confidence,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "classification_confidence": self.classification_confidence,
            "classification_reasons": self.classification_reasons,
            "security_score": self.security_score,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "confidence": self.confidence,
            "sources": self.sources,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Device":
        """Create a device from a report dictionary."""
        return cls(
            ip=str(data.get("ip") or ""),
            mac=_optional_str(data.get("mac")),
            vendor=_optional_str(data.get("vendor")),
            hostname=_optional_str(data.get("hostname")),
            device_type=_optional_str(data.get("device_type")),
            manufacturer=_optional_str(data.get("manufacturer")),
            model=_optional_str(data.get("model")),
            firmware=_optional_str(data.get("firmware")),
            open_ports=[
                int(str(port)) for port in _optional_list(data.get("open_ports"))
            ],
            services=_optional_mapping(data.get("services")),
            snmp_info=_optional_mapping(data.get("snmp_info")),
            mdns_info=_optional_mapping(data.get("mdns_info")),
            netbios_info=_optional_mapping(data.get("netbios_info")),
            tls_info=_optional_mapping(data.get("tls_info")),
            os_guess=_optional_str(data.get("os_guess")),
            response_time_ms=_optional_float(data.get("response_time_ms")),
            discovery_methods=[
                str(item) for item in _optional_list(data.get("discovery_methods"))
            ],
            discovery_confidence=_optional_float(data.get("discovery_confidence"))
            or 0.0,
            first_seen=_optional_str(data.get("first_seen")) or utc_now_iso(),
            last_seen=_optional_str(data.get("last_seen")) or utc_now_iso(),
            classification_confidence=_optional_float(
                data.get("classification_confidence")
            )
            or 0.0,
            classification_reasons=[
                str(item) for item in _optional_list(data.get("classification_reasons"))
            ],
            security_score=int(_optional_float(data.get("security_score")) or 100),
            findings=[str(item) for item in _optional_list(data.get("findings"))],
            recommendations=[
                str(item) for item in _optional_list(data.get("recommendations"))
            ],
            confidence={
                str(key): float(value)
                for key, value in _optional_mapping(data.get("confidence")).items()
                if isinstance(value, (int, float, str))
            },
            sources={
                str(key): [str(item) for item in value]
                for key, value in _optional_mapping(data.get("sources")).items()
                if isinstance(value, list)
            },
        )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _optional_float(value: object) -> float | None:
    if isinstance(value, (int, float, str)):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    return None


def _optional_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    return []


def _optional_mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): val for key, val in value.items()}
    return {}
