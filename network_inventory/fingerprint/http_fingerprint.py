"""HTTP and HTTPS fingerprint helpers."""

from __future__ import annotations

import hashlib
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def fingerprint_http(ip: str, port: int, timeout: float = 2.0) -> dict[str, object]:
    """Collect basic HTTP metadata from a host."""
    scheme = "https" if port in {443, 8443} else "http"
    base_url = f"{scheme}://{ip}:{port}/"
    result: dict[str, object] = {"url": base_url}
    try:
        response = requests.get(base_url, timeout=timeout, verify=False)
    except requests.RequestException as exc:
        result["error"] = str(exc)
        return result

    result["status_code"] = response.status_code
    result["server"] = response.headers.get("Server")
    result["www_authenticate"] = response.headers.get("WWW-Authenticate")
    result["title"] = _title(response.text)
    result["favicon_hash"] = _favicon_hash(base_url, response.text, timeout)
    return result


def _title(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return None


def _favicon_hash(base_url: str, html: str, timeout: float) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    href = None
    for link in soup.find_all("link"):
        rel = " ".join(link.get("rel", [])).lower()
        if "icon" in rel:
            href = link.get("href")
            break
    favicon_url = urljoin(base_url, href or "/favicon.ico")
    try:
        response = requests.get(favicon_url, timeout=timeout, verify=False)
        if response.ok and response.content:
            return hashlib.md5(response.content).hexdigest()
    except requests.RequestException:
        return None
    return None

