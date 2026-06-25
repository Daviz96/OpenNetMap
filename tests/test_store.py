import sqlite3
from pathlib import Path

from network_inventory.database.store import InventoryStore
from network_inventory.events.engine import InventoryEvent
from network_inventory.inventory.device import Device
from network_inventory.topology.builder import build_topology


def test_inventory_store_save_and_load_latest_devices(tmp_path: Path):
    db_path = tmp_path / "inventory.db"
    store = InventoryStore(db_path)

    device = Device(ip="10.0.0.10", mac="00:11:22:33:44:55", hostname="switch")
    stats = {"started_at": "2026-06-22T00:00:00Z", "subnet": "10.0.0.0/24"}
    events = [
        InventoryEvent("NEW_DEVICE", "00:11:22:33:44:55|10.0.0.10", "Nuovo dispositivo")
    ]

    scan_id = store.save_scan([device], stats, events)
    assert isinstance(scan_id, int) and scan_id > 0

    loaded = store.load_latest_devices()
    assert len(loaded) == 1
    assert loaded[0].ip == "10.0.0.10"
    assert loaded[0].mac == "00:11:22:33:44:55"
    assert loaded[0].hostname == "switch"


def test_save_scan_persists_topology(tmp_path: Path):
    db_path = tmp_path / "inventory.db"
    store = InventoryStore(db_path)

    device = Device(ip="10.0.0.10", mac="00:11:22:33:44:55", hostname="switch")
    stats: dict[str, object] = {
        "started_at": "2026-06-25T00:00:00Z",
        "subnet": "10.0.0.0/24",
    }
    topology = build_topology([device], stats)

    store.save_scan([device], stats, topology=topology)

    loaded = store.load_latest_topology()
    assert loaded is not None
    nodes = loaded["nodes"]
    assert isinstance(nodes, list)
    assert any(node["ip"] == "10.0.0.10" for node in nodes)

    with sqlite3.connect(db_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM topology").fetchone()[0]
    assert count == 1


def test_load_latest_topology_returns_none_when_absent(tmp_path: Path):
    store = InventoryStore(tmp_path / "inventory.db")
    assert store.load_latest_topology() is None


def test_save_scan_emits_topology_change_events(tmp_path: Path):
    db_path = tmp_path / "inventory.db"
    store = InventoryStore(db_path)
    stats: dict[str, object] = {
        "started_at": "2026-06-25T00:00:00Z",
        "subnet": "10.0.0.0/24",
    }
    d1 = Device(ip="10.0.0.10", mac="aa:bb:cc:dd:ee:10")
    d2 = Device(ip="10.0.0.11", mac="aa:bb:cc:dd:ee:11")

    # Primo scan: nessuna topologia precedente -> nessun evento di cambiamento.
    store.save_scan([d1], stats, topology=build_topology([d1], stats))
    # Secondo scan con un nuovo device -> nodo e collegamento aggiunti.
    store.save_scan([d1, d2], stats, topology=build_topology([d1, d2], stats))

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT event_type FROM events WHERE event_type LIKE 'TOPOLOGY_%'"
        ).fetchall()
    types = {row[0] for row in rows}
    assert "TOPOLOGY_NODE_ADDED" in types
    assert "TOPOLOGY_LINK_ADDED" in types


def test_save_scan_ensures_default_vlan_without_duplicates(tmp_path: Path):
    db_path = tmp_path / "inventory.db"
    store = InventoryStore(db_path)
    device = Device(ip="10.0.0.10", mac="00:11:22:33:44:55")
    stats: dict[str, object] = {
        "started_at": "2026-06-25T00:00:00Z",
        "subnet": "10.0.0.0/24",
    }

    store.save_scan([device], stats)
    store.save_scan([device], stats)

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT vlan_id, vlan_name, subnet, source FROM vlans"
        ).fetchall()
    assert rows == [("0", "Default VLAN", "10.0.0.0/24", "default")]
