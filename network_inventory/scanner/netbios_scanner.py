"""NetBIOS scanner using nbtstat where available."""

from __future__ import annotations

import re
import subprocess


def scan_netbios(ip: str, timeout: float = 2.0) -> dict[str, object]:
    """Collect NetBIOS names with nbtstat if the command exists."""
    try:
        completed = subprocess.run(
            ["nbtstat", "-A", ip],
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return {}

    if completed.returncode != 0:
        return {}

    names: list[str] = []
    workgroup = None
    for line in completed.stdout.splitlines():
        match = re.search(r"^\s*([^\s<]+)\s+<([0-9A-Fa-f]{2})>\s+(\w+)", line)
        if not match:
            continue
        name, suffix, kind = match.groups()
        if suffix == "00" and kind.upper() == "UNIQUE":
            names.append(name)
        elif suffix == "00" and kind.upper() == "GROUP":
            workgroup = name
    return {"names": names, "workgroup": workgroup}
