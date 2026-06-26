#!/usr/bin/env python3
"""Dump leggibile dei dati di topologia fisica raccolti via SNMP (MS1).

Mostra, per uno switch, la forwarding table tradotta in **MAC → porta** (con
nomi porta), distinguendo porte di **accesso** (pochi MAC) da **uplink** (molti
MAC); e, per un router/L3, la tabella **ARP** (IP → MAC).

Uso:
    python scripts/snmp_topology_dump.py --host 192.168.101.11 -c public        # switch
    python scripts/snmp_topology_dump.py --host 192.168.101.1  -c public --arp  # router
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permette di lanciare lo script direttamente (aggiunge la root del progetto).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from network_inventory.scanner.snmp_topology import (  # noqa: E402
    collect_arp,
    collect_switch_topology,
)


def _dump_switch(
    host: str, communities: list[str], timeout: float, uplink: int
) -> None:
    topo = collect_switch_topology(host, communities, timeout)
    if topo is None:
        print(f"[NO] Nessuna risposta SNMP da {host} (community {communities})")
        return
    print(f"[OK] {topo.sys_name or host} — {topo.sys_descr or ''}")
    per_port = topo.macs_per_port()
    print(f"\nForwarding table: {len(topo.fdb)} voci su {len(per_port)} porte\n")
    access, uplinks = 0, 0
    for port in sorted(per_port):
        macs = per_port[port]
        kind = "UPLINK" if len(macs) >= uplink else "accesso"
        if kind == "UPLINK":
            uplinks += 1
        else:
            access += 1
        sample = ", ".join(sorted(set(macs))[:3])
        more = "" if len(set(macs)) <= 3 else f" (+{len(set(macs)) - 3})"
        print(f"  {port:<22} {len(macs):>4} MAC  [{kind:7}]  {sample}{more}")
    print(
        f"\nPorte di accesso (endpoint diretti): {access} · "
        f"uplink (>= {uplink} MAC): {uplinks}"
    )


def _dump_arp(host: str, communities: list[str], timeout: float) -> None:
    arp = collect_arp(host, communities, timeout)
    if not arp:
        print(f"[NO] Nessuna ARP da {host} (community {communities})")
        return
    print(f"[OK] Tabella ARP da {host}: {len(arp)} voci")
    for ip, mac in list(sorted(arp.items()))[:10]:
        print(f"  {ip:<16} → {mac}")
    if len(arp) > 10:
        print(f"  ... (+{len(arp) - 10})")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dump topologia fisica via SNMP (switch FDB / router ARP)."
    )
    parser.add_argument("--host", required=True, help="IP di management dell'apparato")
    parser.add_argument(
        "-c",
        "--community",
        action="append",
        help="Community (ripetibile). Default: public",
    )
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument(
        "--uplink",
        type=int,
        default=5,
        help="Soglia MAC oltre la quale una porta è considerata uplink (default 5)",
    )
    parser.add_argument(
        "--arp", action="store_true", help="Mostra la tabella ARP invece della FDB"
    )
    args = parser.parse_args()
    communities = args.community or ["public"]
    if args.arp:
        _dump_arp(args.host, communities, args.timeout)
    else:
        _dump_switch(args.host, communities, args.timeout, args.uplink)


if __name__ == "__main__":
    main()
