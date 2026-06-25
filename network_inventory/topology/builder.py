"""Build a logical network topology from inventory data.

Il modello è costruito su un grafo NetworkX (``nx.DiGraph``) per centralizzare
nodi, archi e gerarchie; ``build_topology`` lo serializza nel dizionario
``{"nodes": [...], "edges": [...], "metadata": {...}}`` consumato da dashboard,
export e persistenza.
"""

from __future__ import annotations

import ipaddress
from dataclasses import asdict, dataclass, field

import networkx as nx

from network_inventory.inventory.device import Device


@dataclass(slots=True)
class TopologyNode:
    id: str
    label: str
    type: str
    ip: str | None = None
    mac: str | None = None
    vendor: str | None = None
    model: str | None = None
    vlan: str | None = None
    level: int = 3
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class TopologyLink:
    source: str
    target: str
    relationship: str
    confidence: int = 100
    discovery_method: str = "inventory"
    metadata: dict[str, object] = field(default_factory=dict)


# Livello gerarchico per tipo nodo (0 = radice rete, valori più alti = più in basso).
_TYPE_LEVEL = {
    "network": 0,
    "firewall": 1,
    "router": 1,
    "vlan": 2,
    "switch": 2,
    "access_point": 3,
    "host": 3,
    "unknown": 4,
}


def _level_for(node_type: str) -> int:
    return _TYPE_LEVEL.get(node_type, 4)


def build_graph(
    devices: list[Device],
    stats: dict[str, object] | None = None,
    *,
    subnet: str | None = None,
    gateway: str | None = None,
) -> nx.DiGraph:
    """Costruisce il grafo NetworkX della topologia logica."""
    stats = dict(stats or {})
    if subnet:
        stats["subnet"] = subnet
    if gateway:
        stats["gateway"] = gateway
    subnet = str(stats.get("subnet") or "network")
    root_id = subnet

    devices = _correlate_devices(devices)
    gateway_ip = _normalize_ip(stats.get("gateway") or stats.get("default_gateway"))

    graph: nx.DiGraph = nx.DiGraph()
    graph.graph["metadata"] = {
        "device_count": len(devices),
        "subnet": subnet,
        "gateway": gateway_ip,
    }

    _add_node(graph, TopologyNode(id=root_id, label=root_id, type="network", level=0))

    gateway_device_id: str | None = None
    if gateway_ip:
        gateway_device = _find_device_by_ip(devices, gateway_ip)
        if gateway_device:
            gateway_node = _build_device_node(gateway_device)
            _add_node(graph, gateway_node)
            gateway_device_id = gateway_node.id
            _add_link(
                graph,
                TopologyLink(
                    source=root_id,
                    target=gateway_node.id,
                    relationship="DEFAULT_GATEWAY",
                    confidence=_edge_confidence(gateway_device),
                    discovery_method=_edge_discovery_method(gateway_device),
                ),
            )

    for device in devices:
        _add_node(graph, _build_device_node(device))

    for node_id, data in list(graph.nodes(data=True)):
        node_type = str(data.get("type"))
        if node_type in {"network", "vlan"}:
            continue
        if gateway_device_id and node_id == gateway_device_id:
            continue
        node_ip = data.get("ip")
        relationship = "CONNECTED_TO"
        if gateway_ip and node_ip and node_ip != gateway_ip:
            if node_type in {"switch", "router", "firewall"}:
                relationship = "UPLINK"
        metadata = data.get("metadata") or {}
        _add_link(
            graph,
            TopologyLink(
                source=root_id,
                target=node_id,
                relationship=relationship,
                confidence=50 if node_type == "unknown" else 90,
                discovery_method=str(metadata.get("discovery_method", "inventory")),
            ),
        )
        # Inferenza L3: gli apparati collegati al gateway sono vicini di livello 3.
        if relationship == "UPLINK" and gateway_device_id:
            _add_link(
                graph,
                TopologyLink(
                    source=gateway_device_id,
                    target=node_id,
                    relationship="LAYER3_NEIGHBOR",
                    confidence=60,
                    discovery_method="inventory",
                ),
            )

    _add_vlan_topology(graph, devices)
    return graph


def build_topology(
    devices: list[Device],
    stats: dict[str, object] | None = None,
    *,
    subnet: str | None = None,
    gateway: str | None = None,
) -> dict[str, object]:
    """Costruisce e serializza la topologia in dizionario."""
    graph = build_graph(devices, stats, subnet=subnet, gateway=gateway)
    nodes = [dict(data) for _, data in graph.nodes(data=True)]
    edges = [dict(data) for _, _, data in graph.edges(data=True)]
    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": graph.graph["metadata"],
    }


def _add_node(graph: nx.DiGraph, node: TopologyNode) -> None:
    graph.add_node(node.id, **asdict(node))


def _add_link(graph: nx.DiGraph, link: TopologyLink) -> None:
    graph.add_edge(link.source, link.target, **asdict(link))


def _correlate_devices(devices: list[Device]) -> list[Device]:
    """Correla/deduplica i dispositivi visti da più metodi (stesso mac|ip).

    Collassa voci con la stessa chiave preservando l'ordine; mantiene la prima
    occorrenza (la pipeline di inventory di norma fornisce già voci uniche).
    """
    seen: dict[str, Device] = {}
    for device in devices:
        key = _build_device_id(device)
        if key not in seen:
            seen[key] = device
    return list(seen.values())


def _add_vlan_topology(graph: nx.DiGraph, devices: list[Device]) -> None:
    for vlan_id, vlan_node in _build_vlan_nodes(devices).items():
        if vlan_id not in graph:
            _add_node(graph, vlan_node)
        for device in devices:
            device_vlan = _extract_vlan(device)
            if device_vlan is not None and f"vlan-{device_vlan}" == vlan_id:
                _add_link(
                    graph,
                    TopologyLink(
                        source=_build_device_id(device),
                        target=vlan_id,
                        relationship="MEMBER_OF_VLAN",
                        confidence=_edge_confidence(device),
                        discovery_method=_edge_discovery_method(device),
                    ),
                )


def _build_device_node(device: Device) -> TopologyNode:
    node_type = _normalize_device_type(device.device_type)
    return TopologyNode(
        id=_build_device_id(device),
        label=device.hostname or device.ip,
        type=node_type,
        ip=device.ip,
        mac=device.mac,
        vendor=device.vendor or device.manufacturer,
        model=device.model,
        vlan=str(_extract_vlan(device)) if _extract_vlan(device) is not None else None,
        level=_level_for(node_type),
        metadata={
            "discovery_methods": device.discovery_methods,
            "discovery_confidence": device.discovery_confidence,
            "classification_confidence": device.classification_confidence,
            "sources": device.sources,
            "snmp_info": device.snmp_info,
        },
    )


def _build_device_id(device: Device) -> str:
    return f"{device.mac or 'no-mac'}|{device.ip}"


def _extract_vlan(device: Device) -> int | None:
    vlan = device.snmp_info.get("vlan") if isinstance(device.snmp_info, dict) else None
    if isinstance(vlan, (int, str)) and str(vlan).isdigit():
        return int(vlan)
    vlans = (
        device.snmp_info.get("vlans") if isinstance(device.snmp_info, dict) else None
    )
    if isinstance(vlans, list) and vlans:
        first = vlans[0]
        if isinstance(first, (int, str)) and str(first).isdigit():
            return int(first)
    return None


def _build_vlan_nodes(devices: list[Device]) -> dict[str, TopologyNode]:
    nodes: dict[str, TopologyNode] = {}
    for device in devices:
        vlan_id = _extract_vlan(device)
        if vlan_id is None:
            continue
        node_id = f"vlan-{vlan_id}"
        if node_id not in nodes:
            nodes[node_id] = TopologyNode(
                id=node_id,
                label=f"VLAN {vlan_id}",
                type="vlan",
                level=_level_for("vlan"),
                metadata={"vlan_id": vlan_id},
            )
    return nodes


def _find_device_by_ip(devices: list[Device], ip: str | None) -> Device | None:
    if not ip:
        return None
    for device in devices:
        if device.ip == ip:
            return device
    return None


def _normalize_ip(value: object | None) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return str(ipaddress.ip_address(text))
    except ValueError:
        return text


def _normalize_device_type(value: str | None) -> str:
    if not value:
        return "unknown"
    low = value.lower()
    if "switch" in low:
        return "switch"
    if "router" in low:
        return "router"
    if "firewall" in low:
        return "firewall"
    if "access point" in low or "access-point" in low or "ap" in low:
        return "access_point"
    if "server" in low or "workstation" in low or "pc" in low:
        return "host"
    return value


def _edge_confidence(device: Device) -> int:
    if any(method.lower() == "lldp" for method in device.discovery_methods):
        return 100
    if any(method.lower() == "snmp" for method in device.discovery_methods):
        return 95
    if any(method.lower() == "arp" for method in device.discovery_methods):
        return 50
    return min(max(int(device.discovery_confidence or 50), 1), 100)


def _edge_discovery_method(device: Device) -> str:
    methods = [m.lower() for m in device.discovery_methods if isinstance(m, str)]
    if "lldp" in methods:
        return "lldp"
    if "cdp" in methods:
        return "cdp"
    if "snmp" in methods:
        return "snmp"
    if "arp" in methods:
        return "arp"
    return "inventory"
