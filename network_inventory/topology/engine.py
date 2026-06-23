"""Topology engine orchestration and high-level topology services."""

from __future__ import annotations

from network_inventory.inventory.device import Device

from .builder import build_topology
from .repository import TopologyRepository


class TopologyEngine:
    """Orchestrate topology build, export and persistence."""

    def __init__(self, repository: TopologyRepository | None = None) -> None:
        self.repository = repository

    def build(self, devices: list[Device], stats: dict[str, object]) -> dict[str, object]:
        """Build topology from discovered devices and scan metadata."""
        return build_topology(devices, stats)

    def save_topology(self, db_path: str, scan_id: int, topology: dict[str, object]) -> None:
        """Persist topology snapshot in SQLite."""
        repo = self.repository or TopologyRepository(db_path)
        repo.save_topology(scan_id, topology)
