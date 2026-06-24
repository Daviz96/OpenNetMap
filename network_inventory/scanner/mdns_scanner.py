"""mDNS scanner using zeroconf for local service discovery."""

from __future__ import annotations

import socket
import threading
from typing import Any

_SERVICE_TYPES = [
    "_http._tcp.local.",
    "_https._tcp.local.",
    "_smb._tcp.local.",
    "_printer._tcp.local.",
    "_ipp._tcp.local.",
    "_airplay._tcp.local.",
    "_ssh._tcp.local.",
    "_ftp._tcp.local.",
    "_sftp-ssh._tcp.local.",
    "_device-info._tcp.local.",
]


def scan_mdns(ip: str, timeout: float = 2.0) -> dict[str, object]:
    """Browse mDNS/Bonjour services on the local network and return entries for *ip*.

    zeroconf is broadcast-oriented: we browse all known service types for
    *timeout* seconds, collect every advertised service, then filter by the
    resolved IP address to return only records belonging to the target host.
    """
    try:
        from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
    except ImportError:
        return {}

    found: dict[str, list[dict[str, object]]] = {}
    lock = threading.Lock()

    class _Listener(ServiceListener):
        def add_service(self, zc: Any, stype: str, name: str) -> None:
            info = zc.get_service_info(stype, name)
            if info is None:
                return
            addresses = [socket.inet_ntoa(a) for a in info.addresses]
            if ip not in addresses:
                return
            entry: dict[str, object] = {
                "name": name.replace(f".{stype}", "").strip("."),
                "type": stype.rstrip("."),
                "port": info.port,
                "server": info.server.rstrip(".") if info.server else None,
            }
            with lock:
                found.setdefault("services", []).append(entry)
                if info.server and "hostname" not in found:
                    found["hostname"] = info.server.rstrip(".")

        def remove_service(self, zc: Any, stype: str, name: str) -> None:
            pass

        def update_service(self, zc: Any, stype: str, name: str) -> None:
            pass

    zc = Zeroconf()
    try:
        browsers = [ServiceBrowser(zc, stype, _Listener()) for stype in _SERVICE_TYPES]
        done = threading.Event()
        done.wait(timeout=timeout)
        for b in browsers:
            b.cancel()
    finally:
        zc.close()

    return dict(found)
