"""CSV report writer."""

from __future__ import annotations

import csv
from pathlib import Path

from network_inventory.inventory.device import Device


def write_csv(devices: list[Device], output_dir: str | Path) -> Path:
    """Write inventory CSV report."""
    path = Path(output_dir) / "inventory.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "ip",
                "hostname",
                "mac",
                "vendor",
                "device_type",
                "classification_confidence",
                "security_score",
                "manufacturer",
                "model",
                "open_ports",
            ],
        )
        writer.writeheader()
        for device in devices:
            writer.writerow(
                {
                    "ip": device.ip,
                    "hostname": device.hostname,
                    "mac": device.mac,
                    "vendor": device.vendor,
                    "device_type": device.device_type,
                    "classification_confidence": device.classification_confidence,
                    "security_score": device.security_score,
                    "manufacturer": device.manufacturer,
                    "model": device.model,
                    "open_ports": " ".join(str(port) for port in device.open_ports),
                }
            )
    return path
