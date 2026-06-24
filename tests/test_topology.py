import json
from pathlib import Path

from network_inventory.inventory.device import Device
from network_inventory.topology.builder import build_topology
from network_inventory.topology.diff import diff_topology
from network_inventory.topology.export import write_topology_exports


def test_build_topology_contains_network_root_and_device_node():
    device = Device(ip="192.168.0.10", mac="aa:bb:cc:dd:ee:ff", hostname="printer")
    topology = build_topology([device], subnet="192.168.0.0/24")

    assert "nodes" in topology and "edges" in topology
    assert isinstance(topology["nodes"], list)
    assert isinstance(topology["edges"], list)
    assert topology["nodes"][0]["id"] == "192.168.0.0/24"
    assert topology["nodes"][1]["id"] == "aa:bb:cc:dd:ee:ff|192.168.0.10"
    assert topology["edges"][0]["source"] == "192.168.0.0/24"
    assert topology["edges"][0]["target"] == "aa:bb:cc:dd:ee:ff|192.168.0.10"


def test_write_topology_exports_writes_files(tmp_path: Path):
    device = Device(ip="192.168.0.11", mac=None, hostname="router")
    stats = {"subnet": "192.168.0.0/24"}

    outputs = write_topology_exports([device], stats, str(tmp_path))

    expected_files = {
        tmp_path / "topology.json",
        tmp_path / "topology.graphml",
        tmp_path / "topology.html",
    }
    assert set(outputs) == expected_files
    assert (tmp_path / "topology.json").exists()

    data = json.loads((tmp_path / "topology.json").read_text(encoding="utf-8"))
    assert data["nodes"][1]["label"] == "router"


def test_build_topology_includes_gateway_and_vlan():
    devices = [
        Device(
            ip="192.168.0.1",
            mac="aa:bb:cc:dd:ee:01",
            hostname="gateway",
            device_type="router",
            discovery_methods=["snmp"],
        ),
        Device(
            ip="192.168.0.10",
            mac="aa:bb:cc:dd:ee:10",
            hostname="switch1",
            device_type="switch",
            discovery_methods=["lldp"],
            snmp_info={"vlan": 100},
        ),
        Device(
            ip="192.168.0.20",
            mac="aa:bb:cc:dd:ee:20",
            hostname="host1",
            device_type="host",
            discovery_methods=["arp"],
        ),
    ]
    topology = build_topology(
        devices, {"subnet": "192.168.0.0/24", "gateway": "192.168.0.1"}
    )

    assert isinstance(topology, dict)
    nodes = topology["nodes"]
    edges = topology["edges"]
    assert isinstance(nodes, list)
    assert isinstance(edges, list)
    assert any(node["type"] == "network" for node in nodes)
    assert any(node["id"] == "aa:bb:cc:dd:ee:01|192.168.0.1" for node in nodes)
    assert any(edge["relationship"] == "DEFAULT_GATEWAY" for edge in edges)
    assert any(edge["relationship"] == "MEMBER_OF_VLAN" for edge in edges)


def test_diff_topology_detects_added_and_removed():
    previous: dict[str, object] = {
        "nodes": [{"id": "network", "label": "network", "type": "network"}],
        "edges": [],
    }
    current: dict[str, object] = {
        "nodes": [
            {"id": "network", "label": "network", "type": "network"},
            {"id": "device1", "label": "device1", "type": "host"},
        ],
        "edges": [
            {"source": "network", "target": "device1", "relationship": "CONNECTED_TO"}
        ],
    }

    changes = diff_topology(previous, current)
    assert len(changes["nodes_added"]) == 1
    assert len(changes["edges_added"]) == 1
    assert changes["nodes_removed"] == []
    assert changes["edges_removed"] == []
