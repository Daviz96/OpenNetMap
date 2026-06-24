"""NetBIOS scanner using nbtstat (Windows) or nmblookup (Linux/macOS)."""

from __future__ import annotations

import re
import subprocess


def scan_netbios(ip: str, timeout: float = 2.0) -> dict[str, object]:
    """Collect NetBIOS names for *ip*.

    Tries ``nbtstat -A`` first (Windows); falls back to ``nmblookup -A``
    (Samba, available on Linux/macOS) if nbtstat is not found.
    """
    result = _try_nbtstat(ip, timeout)
    if result is not None:
        return result
    result = _try_nmblookup(ip, timeout)
    if result is not None:
        return result
    return {}


def _run(cmd: list[str], timeout: float) -> str | None:
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def _try_nbtstat(ip: str, timeout: float) -> dict[str, object] | None:
    output = _run(["nbtstat", "-A", ip], timeout)
    if output is None:
        return None
    return _parse_nbtstat(output)


def _try_nmblookup(ip: str, timeout: float) -> dict[str, object] | None:
    output = _run(["nmblookup", "-A", ip], timeout)
    if output is None:
        return None
    return _parse_nmblookup(output)


def _parse_nbtstat(output: str) -> dict[str, object]:
    names: list[str] = []
    workgroup = None
    for line in output.splitlines():
        match = re.search(r"^\s*([^\s<]+)\s+<([0-9A-Fa-f]{2})>\s+(\w+)", line)
        if not match:
            continue
        name, suffix, kind = match.groups()
        if suffix == "00" and kind.upper() == "UNIQUE":
            names.append(name)
        elif suffix == "00" and kind.upper() == "GROUP":
            workgroup = name
    return {"names": names, "workgroup": workgroup}


def _parse_nmblookup(output: str) -> dict[str, object]:
    # nmblookup output lines: "\t<name>     <00> -         <ACTIVE>"
    # or: "Looking up status of <ip>" header lines
    names: list[str] = []
    workgroup = None
    for line in output.splitlines():
        match = re.search(r"^\s+(\S+)\s+<([0-9A-Fa-f]{2})>\s+-\s+(\S+)", line)
        if not match:
            continue
        name, suffix, flags = match.groups()
        if suffix == "00":
            if "<GROUP>" in flags or "GROUP" in flags.upper():
                workgroup = name
            else:
                names.append(name)
    return {"names": names, "workgroup": workgroup}
