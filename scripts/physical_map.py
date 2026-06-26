#!/usr/bin/env python3
"""Mappa fisica endpoint → switch/porta (MS2) da dati SNMP + inventario.

Interroga uno o più switch via SNMP (forwarding table) e, incrociando con un
inventario JSON di OpenNetMap, stampa a quale **switch e porta** è attaccato
ogni dispositivo (porte di accesso = endpoint diretti).

Uso:
    python scripts/physical_map.py --switch 192.168.101.11 -c public \\
        --inventory reports_output/inventory.json
    # più switch:
    python scripts/physical_map.py -s 192.168.101.11 -s 192.168.101.12 \\
        -c public --inventory reports_output/inventory.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from network_inventory.inventory.device import Device  # noqa: E402
from network_inventory.scanner.snmp_topology import (  # noqa: E402
    collect_switch_topology,
)
from network_inventory.topology.correlation import (  # noqa: E402
    access_links,
    correlate_physical,
)


def _load_devices(path: str | None) -> list[Device]:
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data.get("devices", []) if isinstance(data, dict) else []
    return [Device.from_dict(item) for item in items]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mappa fisica endpoint → switch/porta."
    )
    parser.add_argument(
        "-s", "--switch", action="append", required=True, help="IP switch (ripetibile)"
    )
    parser.add_argument(
        "-c", "--community", action="append", help="Community SNMP. Default: public"
    )
    parser.add_argument("--inventory", help="Path a un inventory.json di OpenNetMap")
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument(
        "--max-companions",
        type=int,
        default=1,
        help="Max MAC per porta perché sia 'accesso diretto' (default 1)",
    )
    args = parser.parse_args()
    communities = args.community or ["public"]

    devices = _load_devices(args.inventory)
    print(f"Inventario: {len(devices)} dispositivi")

    switches = []
    for host in args.switch:
        topo = collect_switch_topology(host, communities, args.timeout)
        if topo is None:
            print(f"  [NO] {host}: nessuna risposta SNMP")
            continue
        print(f"  [OK] {host}: {topo.sys_name or ''} — {len(topo.fdb)} voci FDB")
        switches.append(topo)

    if not switches:
        print("Nessuno switch interrogabile. Abilita SNMP e riprova.")
        return

    links = correlate_physical(switches, devices)
    direct = access_links(links, max_companions=args.max_companions)
    direct.sort(key=lambda link: (link.switch_host, link.port))

    print(
        f"\nAttacchi diretti (porte con <= {args.max_companions} MAC): {len(direct)}\n"
    )
    mapped = 0
    for link in direct:
        who = link.device_label or "(sconosciuto)"
        ip = f" {link.device_ip}" if link.device_ip else ""
        if link.device_label:
            mapped += 1
        print(
            f"  {link.switch_name or link.switch_host} / {link.port:<20} "
            f"VLAN {link.vlan:<4} → {who}{ip}  [{link.mac}]"
        )
    print(
        f"\n{mapped}/{len(direct)} attacchi diretti corrispondono a un dispositivo "
        "dell'inventario."
    )


if __name__ == "__main__":
    main()
