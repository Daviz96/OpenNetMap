import csv
import json
from pathlib import Path

from network_inventory.inventory.device import Device
from network_inventory.reports.csv_report import write_csv
from network_inventory.reports.html_report import write_html
from network_inventory.reports.json_report import write_json


def test_write_json_creates_payload(tmp_path: Path):
    devices = [Device(ip="10.0.0.5", hostname="device5")]
    stats = {"subnet": "10.0.0.0/24", "active_hosts": 1}

    output = write_json(devices, stats, tmp_path)
    assert output.name == "inventory.json"
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["stats"] == stats
    assert data["devices"][0]["ip"] == "10.0.0.5"


def test_write_html_creates_searchable_report(tmp_path: Path):
    devices = [Device(ip="10.0.0.6", hostname="device6", device_type="router")]
    stats = {"subnet": "10.0.0.0/24", "active_hosts": 1, "total_hosts": 2}

    output = write_html(devices, stats, tmp_path)
    assert output.name == "inventory.html"
    html_text = output.read_text(encoding="utf-8")
    assert "OpenNetMap" in html_text
    assert "device6" in html_text
    assert "router" in html_text
    assert str(stats["active_hosts"]) in html_text
    # Il punteggio di sicurezza è reso con una classe CSS colorata.
    assert "sec-good" in html_text  # device6 ha score di default 100


def test_write_csv_writes_header_and_rows(tmp_path: Path):
    devices = [Device(ip="10.0.0.7", hostname="device7", mac="00:11:22:33:44:55")]
    output = write_csv(devices, tmp_path)

    assert output.name == "inventory.csv"
    with output.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert rows[0]["ip"] == "10.0.0.7"
    assert rows[0]["hostname"] == "device7"
    assert rows[0]["mac"] == "00:11:22:33:44:55"
