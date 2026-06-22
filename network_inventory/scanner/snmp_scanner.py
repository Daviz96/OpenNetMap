"""SNMP scanner."""

from __future__ import annotations

from network_inventory.utils.config import SNMP_COMMUNITIES

OIDS = {
    "description": "1.3.6.1.2.1.1.1.0",
    "name": "1.3.6.1.2.1.1.5.0",
    "uptime": "1.3.6.1.2.1.1.3.0",
}


def scan_snmp(ip: str, timeout: float = 1.0) -> dict[str, object]:
    """Try common SNMP community strings and return basic system info."""
    try:
        from pysnmp.hlapi import (  # type: ignore
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            getCmd,
        )
    except ImportError:
        return {}

    for community in SNMP_COMMUNITIES:
        result: dict[str, object] = {"community": community}
        success = False
        for key, oid in OIDS.items():
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(community, mpModel=0),
                UdpTransportTarget((ip, 161), timeout=timeout, retries=0),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            )
            error_indication, error_status, _, var_binds = next(iterator)
            if error_indication or error_status:
                continue
            for _, value in var_binds:
                result[key] = str(value)
                success = True
        if success:
            return result
    return {}

