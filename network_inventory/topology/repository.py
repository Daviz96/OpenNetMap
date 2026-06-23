"""SQLite persistence for topology snapshots and change history."""

from __future__ import annotations

import datetime
import json
import sqlite3
from pathlib import Path

from .diff import diff_topology

TOPOLOGY_SCHEMA = """
CREATE TABLE IF NOT EXISTS topology (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    topology_json TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vlans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vlan_id TEXT,
    vlan_name TEXT,
    subnet TEXT,
    source TEXT
);

CREATE TABLE IF NOT EXISTS topology_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    change_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    details TEXT,
    recorded_at TEXT NOT NULL
);
"""


class TopologyRepository:
    """Persist topology snapshots and change history into SQLite."""

    def __init__(self, path: str | Path = "inventory.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save_topology(self, scan_id: int, topology: dict[str, object]) -> int:
        """Save a topology snapshot and related change events."""
        previous = self.load_latest_topology()
        changes = diff_topology(previous, topology) if previous else None
        recorded_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with sqlite3.connect(self.path) as connection:
            connection.executescript(TOPOLOGY_SCHEMA)
            cursor = connection.execute(
                "INSERT INTO topology(scan_id, topology_json, recorded_at) VALUES(?, ?, ?)",
                (scan_id, json.dumps(topology, ensure_ascii=False), recorded_at),
            )
            topology_id = int(cursor.lastrowid or 0)
            if changes:
                self._save_changes(connection, scan_id, changes, recorded_at)
        return topology_id

    def load_latest_topology(self) -> dict[str, object] | None:
        """Load the most recent topology snapshot."""
        with sqlite3.connect(self.path) as connection:
            connection.executescript(TOPOLOGY_SCHEMA)
            row = connection.execute(
                "SELECT topology_json FROM topology ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        return data if isinstance(data, dict) else None

    def _save_changes(
        self,
        connection: sqlite3.Connection,
        scan_id: int,
        changes: dict[str, list[dict[str, object]]],
        recorded_at: str,
    ) -> None:
        for change_type, items in changes.items():
            entity_type = "node" if change_type.startswith("nodes_") else "edge"
            for item in items:
                connection.execute(
                    "INSERT INTO topology_changes(scan_id, change_type, entity_type, entity_id, details, recorded_at) VALUES(?, ?, ?, ?, ?, ?)",
                    (
                        scan_id,
                        change_type,
                        entity_type,
                        str(
                            item.get("id")
                            or item.get("source")
                            or item.get("target")
                            or ""
                        ),
                        json.dumps(item, ensure_ascii=False),
                        recorded_at,
                    ),
                )

    def _init_schema(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.executescript(TOPOLOGY_SCHEMA)
