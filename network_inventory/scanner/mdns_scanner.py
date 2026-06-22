"""mDNS scanner placeholder using zeroconf when available."""

from __future__ import annotations


def scan_mdns(ip: str, timeout: float = 1.0) -> dict[str, object]:
    """Return mDNS data for an IP.

    Zeroconf service discovery is broadcast oriented and not naturally keyed by
    a target IP in a small synchronous probe, so this function currently keeps a
    stable extension point for richer discovery.
    """
    try:
        import zeroconf  # noqa: F401
    except ImportError:
        return {}
    return {
        "available": True,
        "note": "zeroconf installed; targeted mDNS lookup not implemented",
    }
