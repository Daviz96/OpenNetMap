import json
from pathlib import Path

from network_inventory.inventory.device import Device
from network_inventory.topology.export import build_topology, write_topology_exports


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
