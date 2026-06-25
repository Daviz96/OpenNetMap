"""HTML report writer."""

from __future__ import annotations

from pathlib import Path

from network_inventory.inventory.device import Device
from network_inventory.templating import render


def write_html(
    devices: list[Device], stats: dict[str, object], output_dir: str | Path
) -> Path:
    """Write a searchable, self-contained HTML report."""
    path = Path(output_dir) / "inventory.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    document = render("report.html", devices=devices, stats=stats)
    path.write_text(document, encoding="utf-8")
    return path
