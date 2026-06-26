"""SNMP collectors for physical (L2/L3) topology — pysnmp 7.x (asyncio).

Raccoglie i dati necessari alla mappa fisica cablata:
  - Q-BRIDGE ``dot1qTpFdbPort``      → MAC → (VLAN, bridge-port)
  - BRIDGE   ``dot1dBasePortIfIndex``→ bridge-port → ifIndex
  - IF-MIB   ``ifName``/``ifDescr``  → ifIndex → nome porta
  - IP-MIB   ``ipNetToMediaPhysAddress`` → IP → MAC (tabella ARP, dal router)

Tutte le funzioni di rete sono best-effort: in caso di errore/timeout
restituiscono strutture vuote senza sollevare eccezioni.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

# OID base (senza indice)
_OID_DOT1Q_FDB_PORT = "1.3.6.1.2.1.17.7.1.2.2.1.2"
_OID_DOT1D_BASEPORT_IFINDEX = "1.3.6.1.2.1.17.1.4.1.2"
_OID_IFNAME = "1.3.6.1.2.1.31.1.1.1.1"
_OID_IFDESCR = "1.3.6.1.2.1.2.2.1.2"
_OID_ARP_PHYS = "1.3.6.1.2.1.4.22.1.2"
_OID_SYSDESCR = "1.3.6.1.2.1.1.1.0"
_OID_SYSNAME = "1.3.6.1.2.1.1.5.0"


@dataclass(slots=True)
class FdbEntry:
    """Una voce della forwarding table: MAC visto su una porta in una VLAN."""

    mac: str
    vlan: int
    bridge_port: int
    if_name: str | None = None


@dataclass(slots=True)
class SwitchTopology:
    """Dati di topologia raccolti da uno switch via SNMP."""

    host: str
    community: str | None = None
    sys_name: str | None = None
    sys_descr: str | None = None
    fdb: list[FdbEntry] = field(default_factory=list)

    def macs_per_port(self) -> dict[str, list[str]]:
        """Mappa nome-porta → MAC visti su quella porta."""
        result: dict[str, list[str]] = {}
        for entry in self.fdb:
            port = entry.if_name or f"port-{entry.bridge_port}"
            result.setdefault(port, []).append(entry.mac)
        return result


def _format_mac(octets: bytes) -> str:
    return ":".join(f"{b:02x}" for b in octets)


def collect_switch_topology(
    host: str, communities: list[str], timeout: float = 2.0
) -> SwitchTopology | None:
    """Raccoglie la FDB (MAC→porta con nomi) da uno switch. ``None`` se muto."""
    try:
        return asyncio.run(_collect_switch(host, communities, timeout))
    except Exception:
        return None


def collect_arp(
    host: str, communities: list[str], timeout: float = 2.0
) -> dict[str, str]:
    """Raccoglie la tabella ARP (IP→MAC) da un router/L3. {} se muto."""
    try:
        return asyncio.run(_collect_arp(host, communities, timeout))
    except Exception:
        return {}


async def _get(engine, community, host, timeout, oid):
    from pysnmp.hlapi.asyncio import (
        CommunityData,
        ContextData,
        ObjectIdentity,
        ObjectType,
        UdpTransportTarget,
        get_cmd,
    )

    target = await UdpTransportTarget.create((host, 161), timeout=timeout, retries=0)
    err_ind, err_stat, _, var_binds = await get_cmd(
        engine,
        CommunityData(community, mpModel=1),
        target,
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    if err_ind or err_stat:
        return None
    for _, value in var_binds:
        return value
    return None


async def _walk(engine, community, host, timeout, base_oid):
    """Walk di un sottoalbero; restituisce [(suffix_tuple, value), ...]."""
    from pysnmp.hlapi.asyncio import (
        CommunityData,
        ContextData,
        ObjectIdentity,
        ObjectType,
        UdpTransportTarget,
        walk_cmd,
    )

    base = tuple(int(p) for p in base_oid.split("."))
    target = await UdpTransportTarget.create((host, 161), timeout=timeout, retries=0)
    rows: list[tuple[tuple[int, ...], object]] = []
    async for err_ind, err_stat, _, var_binds in walk_cmd(
        engine,
        CommunityData(community, mpModel=1),
        target,
        ContextData(),
        ObjectType(ObjectIdentity(base_oid)),
        lexicographicMode=False,
    ):
        if err_ind or err_stat:
            break
        for name, value in var_binds:
            full = tuple(name.asTuple())
            if full[: len(base)] != base:
                continue
            rows.append((full[len(base) :], value))
    return rows


async def _resolve_community(engine, host, communities, timeout):
    for community in communities:
        if await _get(engine, community, host, timeout, _OID_SYSDESCR) is not None:
            return community
    return None


async def _collect_switch(
    host: str, communities: list[str], timeout: float
) -> SwitchTopology | None:
    from pysnmp.hlapi.asyncio import SnmpEngine

    engine = SnmpEngine()
    community = await _resolve_community(engine, host, communities, timeout)
    if community is None:
        return None

    sys_descr = await _get(engine, community, host, timeout, _OID_SYSDESCR)
    sys_name = await _get(engine, community, host, timeout, _OID_SYSNAME)

    # bridge-port → ifIndex
    base_to_ifindex: dict[int, int] = {}
    for suffix, value in await _walk(
        engine, community, host, timeout, _OID_DOT1D_BASEPORT_IFINDEX
    ):
        if suffix:
            base_to_ifindex[suffix[0]] = int(value)

    # ifIndex → nome (ifName, fallback ifDescr)
    if_names: dict[int, str] = {}
    for suffix, value in await _walk(engine, community, host, timeout, _OID_IFNAME):
        if suffix:
            if_names[suffix[0]] = str(value)
    if not if_names:
        for suffix, value in await _walk(
            engine, community, host, timeout, _OID_IFDESCR
        ):
            if suffix:
                if_names[suffix[0]] = str(value)

    fdb: list[FdbEntry] = []
    for suffix, value in await _walk(
        engine, community, host, timeout, _OID_DOT1Q_FDB_PORT
    ):
        # suffix = (vlan/fdbId, mac0..mac5)
        if len(suffix) < 7:
            continue
        vlan = suffix[0]
        mac = _format_mac(bytes(suffix[1:7]))
        bridge_port = int(value)
        if_name = if_names.get(base_to_ifindex.get(bridge_port, -1))
        fdb.append(
            FdbEntry(mac=mac, vlan=vlan, bridge_port=bridge_port, if_name=if_name)
        )

    return SwitchTopology(
        host=host,
        community=community,
        sys_name=str(sys_name) if sys_name is not None else None,
        sys_descr=str(sys_descr) if sys_descr is not None else None,
        fdb=fdb,
    )


async def _collect_arp(
    host: str, communities: list[str], timeout: float
) -> dict[str, str]:
    from pysnmp.hlapi.asyncio import SnmpEngine

    engine = SnmpEngine()
    community = await _resolve_community(engine, host, communities, timeout)
    if community is None:
        return {}

    arp: dict[str, str] = {}
    for suffix, value in await _walk(engine, community, host, timeout, _OID_ARP_PHYS):
        # suffix = (ifIndex, ip0, ip1, ip2, ip3)
        if len(suffix) < 5:
            continue
        ip = ".".join(str(o) for o in suffix[-4:])
        try:
            octets = value.asOctets()
        except AttributeError:
            continue
        if len(octets) == 6:
            arp[ip] = _format_mac(octets)
    return arp
