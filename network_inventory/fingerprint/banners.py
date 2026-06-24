"""Service banner collection and signature matching."""

from __future__ import annotations

import json
import re
from pathlib import Path

from network_inventory.scanner.port_scanner import grab_banner

_SIGNATURES_PATH = Path(__file__).parent.parent / "signatures" / "banners.json"
_signatures: dict[str, list[dict[str, object]]] | None = None


def _load_signatures() -> dict[str, list[dict[str, object]]]:
    global _signatures
    if _signatures is None:
        try:
            _signatures = json.loads(_SIGNATURES_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            _signatures = {}
    return _signatures


def match_banner(banner: str) -> dict[str, object] | None:
    """Match *banner* against known signatures.

    Returns a dict with ``vendor``, ``product``, ``device_type`` and
    optionally ``version`` on a match, or *None* if no signature matches.
    """
    if not banner:
        return None
    sigs = _load_signatures()
    for _category, entries in sigs.items():
        for entry in entries:
            pattern = str(entry.get("pattern", ""))
            if not pattern:
                continue
            m = re.search(pattern, banner, re.IGNORECASE)
            if m is None:
                continue
            result: dict[str, object] = {
                "vendor": entry.get("vendor", ""),
                "product": entry.get("product", ""),
                "device_type": entry.get("device_type", ""),
            }
            capture_field = entry.get("capture")
            if capture_field and m.lastindex:
                result["version"] = m.group(1)
            return result
    return None


def collect_banners(ip: str, ports: list[int], timeout: float = 1.0) -> dict[int, str]:
    """Collect banners for ports where this is useful."""
    banners: dict[int, str] = {}
    for port in ports:
        banner = grab_banner(ip, port, timeout)
        if banner:
            banners[port] = banner
    return banners
