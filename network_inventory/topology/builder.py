"""Build a logical network topology from inventory data."""

from __future__ import annotations

import ipaddress
from dataclasses import asdict, dataclass, field

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
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class TopologyLink:
    source: str
    target: str
    relationship: str
    confidence: int = 100
    discovery_method: str = "inventory"
    metadata: dict[str, object] = field(default_factory=dict)


def build_topology(
    devices: list[Device],
    stats: dict[str, object] | None = None,
    *,
    subnet: str | None = None,
    gateway: str | None = None,
) -> dict[str, object]:
    """Build a topology model from a device inventory and scan stats."""
    stats = stats or {}
    if subnet:
        stats["subnet"] = subnet
    if gateway:
        stats["gateway"] = gateway
    subnet = str(stats.get("subnet") or "network")
    root_id = subnet
    nodes: dict[str, TopologyNode] = {}
    links: list[TopologyLink] = []

    nodes[root_id] = TopologyNode(id=root_id, label=root_id, type="network")

    gateway_ip = _normalize_ip(stats.get("gateway") or stats.get("default_gateway"))
    gateway_device_id: str | None = None
    if gateway_ip:
        gateway_device = _find_device_by_ip(devices, gateway_ip)
        if gateway_device:
            gateway_node = _build_device_node(gateway_device)
            nodes[gateway_node.id] = gateway_node
            gateway_device_id = gateway_node.id
            links.append(
                TopologyLink(
                    source=root_id,
                    target=gateway_node.id,
                    relationship="DEFAULT_GATEWAY",
                    confidence=_edge_confidence(gateway_device),
                    discovery_method=_edge_discovery_method(gateway_device),
                )
            )

    for device in devices:
        node = _build_device_node(device)
        nodes[node.id] = node

    for node in nodes.values():
        if node.type == "network":
            continue
        if gateway_device_id and node.id == gateway_device_id:
            continue
        relationship = "CONNECTED_TO"
        if gateway_ip and node.ip and node.ip != gateway_ip:
            if node.type in {"switch", "router", "firewall"}:
                relationship = "UPLINK"
        links.append(
            TopologyLink(
                source=root_id,
                target=node.id,
                relationship=relationship,
                confidence=50 if node.type == "unknown" else 90,
                discovery_method=str(
                    node.metadata.get("discovery_method", "inventory")
                ),
            )
        )

    vlan_nodes = _build_vlan_nodes(devices)
    for vlan_id, vlan_node in vlan_nodes.items():
        if vlan_id not in nodes:
            nodes[vlan_id] = vlan_node
        for device in devices:
            device_vlan = _extract_vlan(device)
            if device_vlan:
                device_vlan_id = f"vlan-{device_vlan}"
                if device_vlan_id == vlan_id:
                    device_id = _build_device_id(device)
                    links.append(
                        TopologyLink(
                            source=device_id,
                            target=vlan_id,
                            relationship="MEMBER_OF_VLAN",
                            confidence=_edge_confidence(device),
                            discovery_method=_edge_discovery_method(device),
                        )
                    )

    return {
        "nodes": [asdict(node) for node in nodes.values()],
        "edges": [asdict(link) for link in links],
        "metadata": {
            "device_count": len(devices),
            "subnet": subnet,
            "gateway": gateway_ip,
        },
    }


def _build_device_node(device: Device) -> TopologyNode:
    return TopologyNode(
        id=_build_device_id(device),
        label=device.hostname or device.ip,
        type=_normalize_device_type(device.device_type),
        ip=device.ip,
        mac=device.mac,
        vendor=device.vendor or device.manufacturer,
        model=device.model,
        vlan=str(_extract_vlan(device)) if _extract_vlan(device) is not None else None,
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


def _device_id_from_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    return f"no-mac|{ip}"


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
