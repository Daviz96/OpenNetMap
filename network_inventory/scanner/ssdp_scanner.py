"""SSDP/UPnP discovery via UDP multicast M-SEARCH."""

from __future__ import annotations

import socket

_SSDP_ADDR = "239.255.255.250"
_SSDP_PORT = 1900
_MSEARCH = (
    "M-SEARCH * HTTP/1.1\r\n"
    f"HOST: {_SSDP_ADDR}:{_SSDP_PORT}\r\n"
    'MAN: "ssdp:discover"\r\n'
    "MX: 1\r\n"
    "ST: ssdp:all\r\n"
    "\r\n"
)


def scan_ssdp(ip: str, timeout: float = 2.0) -> dict[str, object]:
    """Send an SSDP M-SEARCH and return UPnP info for *ip*.

    Because SSDP is a multicast protocol, we broadcast the M-SEARCH to the
    LAN segment and collect every response received within *timeout* seconds,
    returning only the entry (if any) whose response originated from *ip*.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.settimeout(timeout)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(_MSEARCH.encode(), (_SSDP_ADDR, _SSDP_PORT))
    except OSError:
        return {}

    result: dict[str, object] = {}
    services: list[str] = []

    try:
        while True:
            try:
                data, addr = sock.recvfrom(4096)
            except TimeoutError:
                break
            if addr[0] != ip:
                continue
            parsed = _parse_response(data.decode(errors="replace"))
            if not result:
                result.update(
                    {
                        "server": parsed.get("server", ""),
                        "location": parsed.get("location", ""),
                    }
                )
            st = parsed.get("st", "")
            if st and st not in services:
                services.append(st)
    finally:
        sock.close()

    if not result and not services:
        return {}
    if services:
        result["services"] = services
    return result


def _parse_response(raw: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in raw.splitlines()[1:]:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        headers[key.strip().lower()] = value.strip()
    return headers
