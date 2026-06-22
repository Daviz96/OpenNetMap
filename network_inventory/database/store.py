"""SQLite persistence layer."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from network_inventory.events.engine import InventoryEvent
from network_inventory.inventory.device import Device


SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    stats_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS devices (
    device_key TEXT PRIMARY KEY,
    ip TEXT NOT NULL,
    mac TEXT,
    hostname TEXT,
    vendor TEXT,
    device_type TEXT,
    manufacturer TEXT,
    model TEXT,
    first_seen TEXT,
    last_seen TEXT,
    last_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scan_devices (
    scan_id INTEGER NOT NULL,
    device_key TEXT NOT NULL,
    device_json TEXT NOT NULL,
    PRIMARY KEY (scan_id, device_key)
);

CREATE TABLE IF NOT EXISTS ports (
    scan_id INTEGER NOT NULL,
    device_key TEXT NOT NULL,
    port INTEGER NOT NULL,
    PRIMARY KEY (scan_id, device_key, port)
);

CREATE TABLE IF NOT EXISTS services (
    scan_id INTEGER NOT NULL,
    device_key TEXT NOT NULL,
    service_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    device_key TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topology (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    topology_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vlans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vlan_id TEXT,
    vlan_name TEXT,
    subnet TEXT,
    source TEXT
);
"""


class InventoryStore:
    """Simple SQLite store for inventory snapshots."""

    def __init__(self, path: str | Path = "inventory.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save_scan(self, devices: list[Device], stats: dict[str, object], events: list[InventoryEvent] | None = None) -> int:
        """Persist a scan snapshot and return scan id."""
        with sqlite3.connect(self.path) as connection:
            connection.executescript(SCHEMA)
            cursor = connection.execute(
                "INSERT INTO scans(started_at, stats_json) VALUES(?, ?)",
                (str(stats.get("started_at") or ""), json.dumps(stats, ensure_ascii=False)),
            )
            scan_id = int(cursor.lastrowid)
            for device in devices:
                key = _device_key(device)
                payload = json.dumps(device.to_dict(), ensure_ascii=False)
                connection.execute(
                    """
                    INSERT INTO devices(device_key, ip, mac, hostname, vendor, device_type, manufacturer, model, first_seen, last_seen, last_json)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(device_key) DO UPDATE SET
                        ip=excluded.ip,
                        hostname=excluded.hostname,
                        vendor=excluded.vendor,
                        device_type=excluded.device_type,
                        manufacturer=excluded.manufacturer,
                        model=excluded.model,
                        last_seen=excluded.last_seen,
                        last_json=excluded.last_json
                    """,
                    (
                        key,
                        device.ip,
                        device.mac,
                        device.hostname,
                        device.vendor,
                        device.device_type,
                        device.manufacturer,
                        device.model,
                        device.first_seen,
                        device.last_seen,
                        payload,
                    ),
                )
                connection.execute(
                    "INSERT INTO scan_devices(scan_id, device_key, device_json) VALUES(?, ?, ?)",
                    (scan_id, key, payload),
                )
                for port in device.open_ports:
                    connection.execute("INSERT INTO ports(scan_id, device_key, port) VALUES(?, ?, ?)", (scan_id, key, port))
                if device.services:
                    connection.execute(
                        "INSERT INTO services(scan_id, device_key, service_json) VALUES(?, ?, ?)",
                        (scan_id, key, json.dumps(device.services, ensure_ascii=False)),
                    )
            for event in events or []:
                connection.execute(
                    "INSERT INTO events(event_type, device_key, message, timestamp) VALUES(?, ?, ?, ?)",
                    (event.event_type, event.device_key, event.message, event.timestamp),
                )
            return scan_id

    def load_latest_devices(self) -> list[Device]:
        """Load latest known devices."""
        with sqlite3.connect(self.path) as connection:
            connection.executescript(SCHEMA)
            rows = connection.execute("SELECT last_json FROM devices").fetchall()
        return [Device.from_dict(json.loads(row[0])) for row in rows]

    def _init_schema(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.executescript(SCHEMA)


def _device_key(device: Device) -> str:
    return f"{device.mac or 'no-mac'}|{device.ip}"
