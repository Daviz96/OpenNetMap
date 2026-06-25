from pathlib import Path

from fastapi.testclient import TestClient

from network_inventory.api.app import _filter_devices, _match_clause, create_app
from network_inventory.database.store import InventoryStore
from network_inventory.inventory.device import Device
from network_inventory.topology.builder import build_topology


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


def test_api_topology_route_served_from_db(tmp_path: Path):
    db_path = tmp_path / "inventory.db"
    store = InventoryStore(db_path)
    device = Device(ip="10.0.0.10", mac="aa:bb:cc:dd:ee:ff", hostname="switch")
    stats: dict[str, object] = {
        "started_at": "2026-06-25T00:00:00Z",
        "subnet": "10.0.0.0/24",
    }
    topology = build_topology([device], stats)
    store.save_scan([device], stats, topology=topology)

    app = create_app(str(db_path))
    client = TestClient(app)

    response = client.get("/topology")
    assert response.status_code == 200
    data = response.json()
    assert any(node["ip"] == "10.0.0.10" for node in data["nodes"])


def test_api_topology_route_empty_without_data(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    db_path = tmp_path / "inventory.db"
    InventoryStore(db_path)
    app = create_app(str(db_path))
    client = TestClient(app)

    response = client.get("/topology")
    assert response.status_code == 200
    assert response.json() == {"nodes": [], "edges": []}


def test_dashboard_pages_render_html(tmp_path: Path):
    db_path = tmp_path / "inventory.db"
    store = InventoryStore(db_path)
    device = Device(ip="10.0.0.10", mac="aa:bb:cc:dd:ee:ff", hostname="switch")
    stats: dict[str, object] = {
        "started_at": "2026-06-25T00:00:00Z",
        "subnet": "10.0.0.0/24",
    }
    store.save_scan([device], stats, topology=build_topology([device], stats))

    client = TestClient(create_app(str(db_path)))
    for path in ("/", "/dashboard/devices", "/dashboard/events", "/dashboard/topology"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "OpenNetMap" in response.text


def test_dashboard_topology_page_embeds_node(tmp_path: Path):
    db_path = tmp_path / "inventory.db"
    store = InventoryStore(db_path)
    device = Device(ip="10.0.0.42", mac="aa:bb:cc:dd:ee:01", hostname="nas")
    stats: dict[str, object] = {
        "started_at": "2026-06-25T00:00:00Z",
        "subnet": "10.0.0.0/24",
    }
    store.save_scan([device], stats, topology=build_topology([device], stats))

    client = TestClient(create_app(str(db_path)))
    response = client.get("/dashboard/topology")
    assert response.status_code == 200
    assert "vis-network.min.js" in response.text
    assert "10.0.0.42" in response.text


def test_static_assets_served(tmp_path: Path):
    client = TestClient(create_app(str(tmp_path / "inventory.db")))
    for asset in ("/static/chart.min.js", "/static/vis-network.min.js"):
        response = client.get(asset)
        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]


def test_static_assets_public_when_api_key_set(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OPENNETMAP_API_KEY", "secret123")
    client = TestClient(create_app(str(tmp_path / "inventory.db")))
    # Le pagine dashboard e gli asset statici restano pubblici.
    assert client.get("/static/chart.min.js").status_code == 200
    assert client.get("/").status_code == 200


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


def test_api_returns_401_when_api_key_set_and_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OPENNETMAP_API_KEY", "secret123")
    db_path = tmp_path / "inventory.db"
    app = create_app(str(db_path))
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/devices")
    assert response.status_code == 401


def test_api_returns_200_with_correct_api_key(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OPENNETMAP_API_KEY", "secret123")
    db_path = tmp_path / "inventory.db"
    app = create_app(str(db_path))
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/devices", headers={"x-api-key": "secret123"})
    assert response.status_code == 200


def test_api_dashboard_accessible_without_api_key(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OPENNETMAP_API_KEY", "secret123")
    db_path = tmp_path / "inventory.db"
    app = create_app(str(db_path))
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/")
    assert response.status_code == 200


def test_api_no_auth_required_when_env_not_set(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("OPENNETMAP_API_KEY", raising=False)
    db_path = tmp_path / "inventory.db"
    app = create_app(str(db_path))
    client = TestClient(app)
    response = client.get("/devices")
    assert response.status_code == 200
