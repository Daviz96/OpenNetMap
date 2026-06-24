"""Configuration defaults for the network inventory tool."""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_PORTS = [
    22,
    23,
    53,
    80,
    135,
    139,
    443,
    445,
    515,
    631,
    9100,
    161,
    3389,
    8080,
    8443,
    10001,
]
TOP_PORTS = [22, 53, 80, 135, 139, 443, 445, 631, 9100, 161, 3389, 8080]
FULL_PORTS = sorted(
    set(DEFAULT_PORTS + [21, 25, 110, 143, 587, 993, 995, 3306, 5432, 5900])
)
SNMP_COMMUNITIES = ["public", "private"]


@dataclass(slots=True)
class ScanConfig:
    """Runtime scan configuration."""

    subnet: str | None = None
    ports: list[int] = field(default_factory=lambda: DEFAULT_PORTS.copy())
    threads: int = 100
    timeout: float = 1.0
    snmp_enabled: bool = False
    verify_ssl: bool = False
    verbose: bool = False
    report_formats: list[str] = field(default_factory=lambda: ["json"])
    output_dir: str = "reports_output"
