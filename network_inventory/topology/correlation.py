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
    collect_switch_topologies,
)

# Tipi/vendor indicativi di apparati di rete (switch/router/AP) da interrogare.
_INFRA_KEYWORDS = ("switch", "router", "firewall", "gateway", "access point")
_INFRA_VENDORS = (
    "draytek",
    "cisco",
    "aruba",
    "hpe",
    "netgear",
    "mikrotik",
    "ubiquiti",
    "tp-link",
    "tplink",
    "zyxel",
    "juniper",
)
# Tipi chiaramente "endpoint": esclusi dall'auto-detect anche se il vendor combacia.
_ENDPOINT_KEYWORDS = (
    "stampante",
    "printer",
    "telecamera",
    "camera",
    "pc ",
    "windows",
    "linux",
    "mac",
    "nas",
    "iot",
    "smartphone",
    "tablet",
    "tv",
)


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
    """Switch/router/AP da interrogare: host espliciti + auto-detect.

    Auto-detect: apparati con tipo di rete (switch/router/...) e porta 161 aperta,
    **oppure** con vendor di apparati di rete (DrayTek, Cisco, ...), esclusi i tipi
    chiaramente endpoint (stampanti, telecamere, PC...).
    """
    targets: list[str] = list(explicit_hosts)
    for device in devices:
        device_type = (device.device_type or "").lower()
        vendor = (device.vendor or device.manufacturer or "").lower()
        is_endpoint = any(k in device_type for k in _ENDPOINT_KEYWORDS)
        if is_endpoint:
            continue
        by_type = 161 in device.open_ports and any(
            k in device_type for k in _INFRA_KEYWORDS
        )
        by_vendor = any(v in vendor for v in _INFRA_VENDORS)
        if by_type or by_vendor:
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
    topologies = collect_switch_topologies(targets, communities, timeout)
    _reclassify_from_snmp(devices, topologies)
    switches = [topo for topo in topologies if topo.fdb]
    return correlate_physical(switches, devices)


def _reclassify_from_snmp(
    devices: list[Device], topologies: list[SwitchTopology]
) -> None:
    """Corregge device_type degli apparati interrogati usando la sysDescr SNMP."""
    by_ip = {topo.host: topo for topo in topologies if topo.sys_descr}
    for device in devices:
        topo = by_ip.get(device.ip)
        if topo is None or not topo.sys_descr:
            continue
        descr = topo.sys_descr.lower()
        if "switch" in descr:
            device.device_type = "Switch"
        elif "access point" in descr or "vigorap" in descr:
            device.device_type = "Access Point"
        elif "router" in descr or "vigor2" in descr or "vigor3" in descr:
            device.device_type = "Router"


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
