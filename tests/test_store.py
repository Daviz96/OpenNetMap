from pathlib import Path

from network_inventory.database.store import InventoryStore
from network_inventory.events.engine import InventoryEvent
from network_inventory.inventory.device import Device


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
