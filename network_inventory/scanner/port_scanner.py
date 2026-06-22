"""Concurrent TCP port scanner."""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed


def scan_ports(
    ip: str, ports: list[int], timeout: float = 1.0, threads: int = 32
) -> list[int]:
    """Return open TCP ports for an IP address."""
    open_ports: list[int] = []
    with ThreadPoolExecutor(max_workers=min(threads, max(len(ports), 1))) as executor:
        futures = {executor.submit(_is_open, ip, port, timeout): port for port in ports}
        for future in as_completed(futures):
            port = futures[future]
            if future.result():
                open_ports.append(port)
    return sorted(open_ports)


def grab_banner(ip: str, port: int, timeout: float = 1.0) -> str | None:
    """Try to retrieve a simple TCP banner."""
    try:
        with socket.create_connection((ip, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            if port in {80, 8080}:
                sock.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
            elif port in {22, 23}:
                pass
            else:
                sock.sendall(b"\r\n")
            data = sock.recv(512)
            return data.decode("utf-8", errors="ignore").strip() or None
    except OSError:
        return None


def _is_open(ip: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False
