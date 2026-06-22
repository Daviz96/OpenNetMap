"""JSON report writer."""

from __future__ import annotations

import json
from pathlib import Path

from network_inventory.inventory.device import Device


def write_json(devices: list[Device], stats: dict[str, object], output_dir: str | Path) -> Path:
    """Write inventory JSON report."""
    path = Path(output_dir) / "inventory.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"stats": stats, "devices": [device.to_dict() for device in devices]}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

