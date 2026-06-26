"""SNMP scanner (pysnmp 7.x, asyncio API)."""

from __future__ import annotations

import asyncio

from network_inventory.utils.config import SNMP_COMMUNITIES

OIDS = {
    "description": "1.3.6.1.2.1.1.1.0",
    "name": "1.3.6.1.2.1.1.5.0",
    "uptime": "1.3.6.1.2.1.1.3.0",
}


def scan_snmp(
    ip: str, timeout: float = 1.0, communities: list[str] | None = None
) -> dict[str, object]:
    """Try SNMP community strings and return basic system info.

    *communities* overrides the module-level default list when provided.
    Best-effort: restituisce ``{}`` su qualsiasi errore (SNMP assente/timeout).
    """
    comms = communities if communities is not None else SNMP_COMMUNITIES
    try:
        return asyncio.run(_scan(ip, timeout, comms))
    except Exception:
        return {}


async def _scan(ip: str, timeout: float, communities: list[str]) -> dict[str, object]:
    try:
        from pysnmp.hlapi.asyncio import (
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
            get_cmd,
        )
    except ImportError:
        return {}

    engine = SnmpEngine()
    for community in communities:
        result: dict[str, object] = {"community": community}
        success = False
        for key, oid in OIDS.items():
            target = await UdpTransportTarget.create(
                (ip, 161), timeout=timeout, retries=0
            )
            err_ind, err_stat, _, var_binds = await get_cmd(
                engine,
                CommunityData(community, mpModel=1),  # SNMPv2c
                target,
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
            )
            if err_ind or err_stat:
                continue
            for _, value in var_binds:
                result[key] = str(value)
                success = True
        if success:
            return result
    return {}
