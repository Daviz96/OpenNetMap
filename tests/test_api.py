from pathlib import Path

from fastapi.testclient import TestClient
from network_inventory.api.app import create_app, _match_clause, _filter_devices
from network_inventory.database.store import InventoryStore
from network_inventory.inventory.device import Device


def test_api_devices_route_returns_empty_list_for_empty_db(tmp_path: Path):
    db_path = tmp_path / "inventory.db"
    InventoryStore(db_path)
    app = create_app(str(db_path))
    client = TestClient(app)

    response = client.get("/devices")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["limit"] == 100
    assert data["offset"] == 0


def test_api_scans_route_returns_scans(tmp_path: Path):
    db_path = tmp_path / "inventory.db"
    store = InventoryStore(db_path)
    device = Device(ip="10.0.0.1", mac="aa:bb:cc:dd:ee:ff")
    stats = {"started_at": "2026-06-22T00:00:00Z", "subnet": "10.0.0.0/24"}
    scan_id = store.save_scan([device], stats, events=[])

    app = create_app(str(db_path))
    client = TestClient(app)

    response = client.get("/scans")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == scan_id
    assert data["items"][0]["stats"]["subnet"] == "10.0.0.0/24"


def test_match_clause_filters_devices_by_field():
    device = {"vendor": "Cisco", "ip": "10.0.0.5", "hostname": "office"}
    assert _match_clause(device, "vendor:Cisco")
    assert _match_clause(device, "hostname:office")
    assert _match_clause(device, "ip:10.0.0.5")
    assert not _match_clause(device, "vendor:Juniper")


def test_filter_devices_composes_and_clauses():
    devices = [
        {"ip": "10.0.0.5", "vendor": "Cisco", "hostname": "office"},
        {"ip": "10.0.0.6", "vendor": "Ubiquiti", "hostname": "lab"},
    ]
    filtered = _filter_devices(devices, "vendor:Cisco and hostname:office")
    assert len(filtered) == 1
    assert filtered[0]["ip"] == "10.0.0.5"
