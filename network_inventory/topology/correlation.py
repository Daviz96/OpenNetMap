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
from network_inventory.scanner.snmp_topology import (
    SwitchTopology,
    collect_switch_topology,
)

_INFRA_KEYWORDS = ("switch", "router", "firewall", "gateway")


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


def select_snmp_targets(devices: list[Device], explicit_hosts: list[str]) -> list[str]:
    """Switch/router da interrogare: host espliciti + auto-detect (161 + tipo rete)."""
    targets: list[str] = list(explicit_hosts)
    for device in devices:
        device_type = (device.device_type or "").lower()
        if 161 in device.open_ports and any(k in device_type for k in _INFRA_KEYWORDS):
            targets.append(device.ip)
    seen: set[str] = set()
    ordered: list[str] = []
    for host in targets:
        if host and host not in seen:
            seen.add(host)
            ordered.append(host)
    return ordered


def collect_physical_links(
    devices: list[Device],
    communities: list[str],
    explicit_hosts: list[str] | None = None,
    timeout: float = 2.0,
) -> list[PhysicalLink]:
    """Interroga gli switch (auto+espliciti) e correla in attacchi fisici."""
    targets = select_snmp_targets(devices, explicit_hosts or [])
    switches: list[SwitchTopology] = []
    for host in targets:
        topo = collect_switch_topology(host, communities, timeout)
        if topo is not None and topo.fdb:
            switches.append(topo)
    return correlate_physical(switches, devices)


def link_to_dict(link: PhysicalLink) -> dict[str, object]:
    """Serializza un PhysicalLink (per stats/persistenza)."""
    return {
        "mac": link.mac,
        "switch_host": link.switch_host,
        "switch_name": link.switch_name,
        "port": link.port,
        "vlan": link.vlan,
        "companions": link.companions,
        "device_ip": link.device_ip,
    }
