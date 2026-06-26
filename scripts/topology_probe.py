#!/usr/bin/env python3
"""Sonda di fattibilità per la topologia fisica (Sprint 8).

Interroga via SNMP (sola lettura) uno switch/router/AP e riporta quali dati
utili alla mappa fisica sono effettivamente disponibili:
  - IF-MIB         → elenco interfacce (nomi porta)
  - BRIDGE-MIB     → tabella MAC→porta (forwarding DB)
  - Q-BRIDGE-MIB   → tabella MAC→porta per VLAN
  - LLDP-MIB       → vicini (switch↔switch↔AP)

Non modifica nulla. Eseguila da una macchina sulla LAN che raggiunge l'apparato.

Uso:
    python scripts/topology_probe.py --host 192.168.1.1 --community public
    python scripts/topology_probe.py --host 192.168.1.1 -c public -c private
"""

from __future__ import annotations

import argparse
import asyncio

OIDS_SCALAR = {
    "sysDescr": "1.3.6.1.2.1.1.1.0",
    "sysName": "1.3.6.1.2.1.1.5.0",
}

# OID chiave per la mappa fisica endpoint → switch/porta.
OIDS_TABLE = {
    "IF-MIB ifDescr (interfacce)": "1.3.6.1.2.1.2.2.1.2",
    "IP-MIB ipNetToMediaPhysAddress (ARP MAC<->IP)": "1.3.6.1.2.1.4.22.1.2",
    "BRIDGE-MIB dot1dTpFdbPort (MAC->porta)": "1.3.6.1.2.1.17.4.3.1.2",
    "Q-BRIDGE dot1qTpFdbPort (MAC->porta/VLAN)": "1.3.6.1.2.1.17.7.1.2.2.1.2",
    "LLDP-MIB lldpRemSysName (vicini)": "1.0.8802.1.1.2.1.4.1.1.9",
}


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
    error_indication, error_status, _, var_binds = await get_cmd(
        engine,
        CommunityData(community, mpModel=1),  # mpModel=1 => SNMPv2c
        target,
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    if error_indication or error_status:
        return None
    for _, value in var_binds:
        return str(value)
    return None


async def _walk(engine, community, host, timeout, oid, limit=5):
    from pysnmp.hlapi.asyncio import (
        CommunityData,
        ContextData,
        ObjectIdentity,
        ObjectType,
        UdpTransportTarget,
        walk_cmd,
    )

    target = await UdpTransportTarget.create((host, 161), timeout=timeout, retries=0)
    count = 0
    samples: list[str] = []
    async for error_indication, error_status, _, var_binds in walk_cmd(
        engine,
        CommunityData(community, mpModel=1),
        target,
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
        lexicographicMode=False,
    ):
        if error_indication or error_status:
            break
        for name, value in var_binds:
            count += 1
            if len(samples) < limit:
                samples.append(f"{name.prettyPrint()} = {value.prettyPrint()}")
    return count, samples


async def probe(host: str, communities: list[str], timeout: float) -> None:
    from pysnmp.hlapi.asyncio import SnmpEngine

    engine = SnmpEngine()
    working = None
    for community in communities:
        descr = await _get(engine, community, host, timeout, OIDS_SCALAR["sysDescr"])
        if descr is not None:
            working = community
            name = await _get(engine, community, host, timeout, OIDS_SCALAR["sysName"])
            print(f"[OK] SNMP risponde con community '{community}'")
            print(f"     sysDescr: {descr}")
            print(f"     sysName : {name}")
            break

    if working is None:
        print(f"[NO] Nessuna risposta SNMP da {host} con community {communities}")
        print("     -> SNMP disabilitato, community diversa o host non raggiungibile.")
        print(
            "     -> Valutare l'abilitazione SNMP o le API VigorACS/Central Management."
        )
        return

    print("\nSorgenti dati per la topologia fisica:")
    available: dict[str, bool] = {}
    for label, oid in OIDS_TABLE.items():
        count, samples = await _walk(engine, working, host, timeout, oid)
        available[label] = count > 0
        status = "DISPONIBILE" if count else "assente/vuoto"
        print(f"  [{status:>12}] {label}: {count} righe")
        for sample in samples:
            print(f"        {sample}")

    print("\nVerdetto:")
    has_fdb = any("FdbPort" in k and v for k, v in available.items())
    has_lldp = any("lldp" in k.lower() and v for k, v in available.items())
    has_arp = any("ipNetToMedia" in k and v for k, v in available.items())
    print(
        "  - MAC->porta: "
        + ("OK → mappa cablato endpoint->switch fattibile" if has_fdb else "assente")
    )
    print(
        "  - ARP (MAC<->IP): "
        + ("OK → correlazione MAC↔IP da questo apparato" if has_arp else "assente")
    )
    print(
        "  - LLDP: "
        + ("OK → gerarchia switch<->switch<->AP fattibile" if has_lldp else "assente")
    )
    if not has_fdb and not has_lldp and not has_arp:
        print("  → Niente via SNMP standard: puntare su VigorACS / Central Management.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sonda di fattibilità topologia fisica (SNMP, sola lettura)."
    )
    parser.add_argument("--host", required=True, help="IP dell'apparato")
    parser.add_argument(
        "-c",
        "--community",
        action="append",
        help="Community SNMP (ripetibile). Default: public, private",
    )
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args()
    communities = args.community or ["public", "private"]
    asyncio.run(probe(args.host, communities, args.timeout))


if __name__ == "__main__":
    main()
