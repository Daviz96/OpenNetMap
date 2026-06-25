"""SQLite persistence layer."""

from __future__ import annotations

import datetime
import json
import sqlite3
from collections.abc import Mapping
from pathlib import Path

from network_inventory.events.engine import InventoryEvent
from network_inventory.inventory.device import Device
from network_inventory.topology.diff import diff_topology

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

    def save_scan(
        self,
        devices: list[Device],
        stats: Mapping[str, object],
        events: list[InventoryEvent] | None = None,
        topology: Mapping[str, object] | None = None,
    ) -> int:
        """Persist a scan snapshot and return scan id.

        When ``topology`` (the model produced by ``build_topology``) is given it
        is stored in the ``topology`` table and any VLAN nodes it contains are
        registered in the ``vlans`` lookup. A default VLAN 0 row is always
        ensured so the table is never empty.
        """
        with sqlite3.connect(self.path) as connection:
            connection.executescript(SCHEMA)
            cursor = connection.execute(
                "INSERT INTO scans(started_at, stats_json) VALUES(?, ?)",
                (
                    str(stats.get("started_at") or ""),
                    json.dumps(stats, ensure_ascii=False),
                ),
            )
            scan_id = cursor.lastrowid
            assert scan_id is not None
            scan_id = int(scan_id)
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
                    connection.execute(
                        "INSERT INTO ports(scan_id, device_key, port) VALUES(?, ?, ?)",
                        (scan_id, key, port),
                    )
                if device.services:
                    connection.execute(
                        "INSERT INTO services(scan_id, device_key, service_json) VALUES(?, ?, ?)",
                        (scan_id, key, json.dumps(device.services, ensure_ascii=False)),
                    )
            for event in events or []:
                connection.execute(
                    "INSERT INTO events(event_type, device_key, message, timestamp) VALUES(?, ?, ?, ?)",
                    (
                        event.event_type,
                        event.device_key,
                        event.message,
                        event.timestamp,
                    ),
                )
            if topology is not None:
                previous_topology = _load_latest_topology(connection)
                connection.execute(
                    "INSERT INTO topology(scan_id, topology_json) VALUES(?, ?)",
                    (scan_id, json.dumps(topology, ensure_ascii=False)),
                )
                if previous_topology is not None:
                    for change in _topology_change_events(
                        previous_topology, dict(topology)
                    ):
                        connection.execute(
                            "INSERT INTO events(event_type, device_key, message, timestamp) VALUES(?, ?, ?, ?)",
                            change,
                        )
            _persist_vlans(connection, topology, stats)
            return scan_id

    def load_latest_devices(self) -> list[Device]:
        """Load latest known devices."""
        with sqlite3.connect(self.path) as connection:
            connection.executescript(SCHEMA)
            rows = connection.execute("SELECT last_json FROM devices").fetchall()
        return [Device.from_dict(json.loads(row[0])) for row in rows]

    def load_latest_topology(self) -> dict[str, object] | None:
        """Return the topology model of the most recent scan, if any."""
        with sqlite3.connect(self.path) as connection:
            connection.executescript(SCHEMA)
            row = connection.execute(
                "SELECT topology_json FROM topology ORDER BY scan_id DESC, id DESC LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(row[0])
        return payload if isinstance(payload, dict) else None

    def _init_schema(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.executescript(SCHEMA)


def _device_key(device: Device) -> str:
    return f"{device.mac or 'no-mac'}|{device.ip}"


def _load_latest_topology(
    connection: sqlite3.Connection,
) -> dict[str, object] | None:
    """Carica l'ultima topologia salvata usando la connessione corrente."""
    row = connection.execute(
        "SELECT topology_json FROM topology ORDER BY scan_id DESC, id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return None
    payload = json.loads(row[0])
    return payload if isinstance(payload, dict) else None


def _topology_change_events(
    previous: dict[str, object], current: dict[str, object]
) -> list[tuple[str, str, str, str]]:
    """Trasforma il diff di topologia in righe-evento (event_type, key, msg, ts)."""
    changes = diff_topology(previous, current)
    timestamp = datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat()
    events: list[tuple[str, str, str, str]] = []
    for node in changes.get("nodes_added", []):
        label = node.get("label") or node.get("id")
        events.append(
            (
                "TOPOLOGY_NODE_ADDED",
                str(node.get("id") or ""),
                f"Nuovo nodo topologia: {label}",
                timestamp,
            )
        )
    for node in changes.get("nodes_removed", []):
        label = node.get("label") or node.get("id")
        events.append(
            (
                "TOPOLOGY_NODE_REMOVED",
                str(node.get("id") or ""),
                f"Nodo topologia rimosso: {label}",
                timestamp,
            )
        )
    for edge in changes.get("edges_added", []):
        key = f"{edge.get('source')}->{edge.get('target')}"
        events.append(
            (
                "TOPOLOGY_LINK_ADDED",
                key,
                f"Nuovo collegamento {edge.get('relationship')}: {key}",
                timestamp,
            )
        )
    for edge in changes.get("edges_removed", []):
        key = f"{edge.get('source')}->{edge.get('target')}"
        events.append(
            (
                "TOPOLOGY_LINK_REMOVED",
                key,
                f"Collegamento rimosso {edge.get('relationship')}: {key}",
                timestamp,
            )
        )
    return events


def _persist_vlans(
    connection: sqlite3.Connection,
    topology: Mapping[str, object] | None,
    stats: Mapping[str, object],
) -> None:
    """Register VLAN rows from a topology model, ensuring a default VLAN 0.

    The ``vlans`` table is a global lookup without a ``scan_id``; rows are
    inserted only when a matching ``vlan_id`` is not already present, so
    repeated scans never create duplicates.
    """
    subnet = str(stats.get("subnet") or "") or None
    _upsert_vlan(connection, "0", "Default VLAN", subnet, "default")

    if not topology:
        return
    nodes = topology.get("nodes")
    if not isinstance(nodes, list):
        return
    for node in nodes:
        if not isinstance(node, dict) or node.get("type") != "vlan":
            continue
        metadata = node.get("metadata")
        vlan_value = (
            metadata.get("vlan_id") if isinstance(metadata, dict) else None
        ) or node.get("id")
        if vlan_value is None:
            continue
        label = node.get("label")
        _upsert_vlan(
            connection,
            str(vlan_value),
            str(label) if label is not None else None,
            subnet,
            "snmp",
        )


def _upsert_vlan(
    connection: sqlite3.Connection,
    vlan_id: str,
    vlan_name: str | None,
    subnet: str | None,
    source: str,
) -> None:
    connection.execute(
        """
        INSERT INTO vlans(vlan_id, vlan_name, subnet, source)
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS(SELECT 1 FROM vlans WHERE vlan_id IS ?)
        """,
        (vlan_id, vlan_name, subnet, source, vlan_id),
    )
