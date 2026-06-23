"""Local OUI database support."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.request import Request, urlopen

IEEE_OUI_URL = "https://standards-oui.ieee.org/oui/oui.txt"


class OuiDatabase:
    """Lookup MAC vendors from a local IEEE OUI text file."""

    def __init__(self, path: str | Path = "oui.txt") -> None:
        self.path = Path(path)
        self._vendors = self._load()

    def lookup(self, mac: str | None) -> str | None:
        """Return vendor name for a MAC address, if known."""
        if not mac:
            return None
        prefix = re.sub(r"[^0-9A-Fa-f]", "", mac).upper()[:6]
        return self._vendors.get(prefix)

    def _load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}

        vendors: dict[str, str] = {}
        for line in self.path.read_text(encoding="utf-8", errors="ignore").splitlines():
            clean = line.strip()
            if not clean:
                continue
            match = re.match(r"^([0-9A-Fa-f]{2}[-:]){2}[0-9A-Fa-f]{2}\s+(.+)$", clean)
            if match:
                prefix = re.sub(r"[^0-9A-Fa-f]", "", clean[:8]).upper()
                vendors[prefix] = clean[9:].strip()
                continue
            match = re.search(r"([0-9A-Fa-f]{6})\s+\(base 16\)\s+(.+)", clean)
            if match:
                vendors[match.group(1).upper()] = match.group(2).strip()
                continue
            match = re.search(
                r"^([0-9A-Fa-f]{2})-([0-9A-Fa-f]{2})-([0-9A-Fa-f]{2})\s+\(hex\)\s+(.+)",
                clean,
            )
            if match:
                vendors["".join(match.groups()[:3]).upper()] = match.group(4).strip()
        return vendors


def update_oui_database(path: str | Path = "oui.txt") -> Path:
    """Download the IEEE OUI database to a local file."""
    target = Path(path)
    request = Request(
        IEEE_OUI_URL, headers={"User-Agent": "Mozilla/5.0 network-inventory-tool"}
    )
    with urlopen(request, timeout=30) as response:
        target.write_bytes(response.read())
    return target
