"""Correlation engine: endpoint → switch/porta dalla forwarding table.

Incrocia le forwarding table di più switch (raccolte via SNMP) con l'inventario
per determinare, per ogni dispositivo, a **quale switch e porta** è attaccato.

Euristica "fewest companions": un MAC è attaccato direttamente allo switch/porta
dove compare insieme al **minor numero di altri MAC** (idealmente da solo = porta
di accesso edge). Le porte con molti MAC sono uplink verso altri switch/AP.
"""

from __future__ import annotations

from dataclasses import dataclass

from network_inventory.inventory.device import Device
from network_inventory.scanner.snmp_topology import SwitchTopology


@dataclass(slots=True)
class PhysicalLink:
    """Attacco fisico di un dispositivo a una porta di switch."""

    mac: str
    switch_host: str
    switch_name: str | None
    port: str
    vlan: int
    companions: int  # n. di MAC sulla stessa porta (1 = endpoint diretto)
    device_ip: str | None = None
    device_label: str | None = None


def _norm_mac(mac: str | None) -> str:
    return (mac or "").replace("-", ":").strip().lower()


def correlate_physical(
    switches: list[SwitchTopology], devices: list[Device]
) -> list[PhysicalLink]:
    """Restituisce gli attacchi fisici (uno per MAC, la porta più "edge")."""
    by_mac: dict[str, Device] = {
        _norm_mac(d.mac): d for d in devices if _norm_mac(d.mac)
    }

    # Per ogni switch: (porta) -> set di MAC, per contare i "compagni".
    port_macs: dict[tuple[str, str], set[str]] = {}
    for switch in switches:
        for entry in switch.fdb:
            port = entry.if_name or f"port-{entry.bridge_port}"
            port_macs.setdefault((switch.host, port), set()).add(_norm_mac(entry.mac))

    # Per ogni MAC, scegli l'occorrenza (switch, porta) con meno compagni.
    best: dict[str, PhysicalLink] = {}
    for switch in switches:
        for entry in switch.fdb:
            mac = _norm_mac(entry.mac)
            port = entry.if_name or f"port-{entry.bridge_port}"
            companions = len(port_macs.get((switch.host, port), set()))
            current = best.get(mac)
            if current is not None and current.companions <= companions:
                continue
            device = by_mac.get(mac)
            best[mac] = PhysicalLink(
                mac=mac,
                switch_host=switch.host,
                switch_name=switch.sys_name,
                port=port,
                vlan=entry.vlan,
                companions=companions,
                device_ip=device.ip if device else None,
                device_label=(device.hostname or device.ip) if device else None,
            )

    return list(best.values())


def access_links(
    links: list[PhysicalLink], max_companions: int = 1
) -> list[PhysicalLink]:
    """Filtra i soli attacchi diretti (porta di accesso, <= max_companions MAC)."""
    return [link for link in links if link.companions <= max_companions]
