"""Compare topology snapshots and identify changes."""

from __future__ import annotations


def diff_topology(
    previous: dict[str, object], current: dict[str, object]
) -> dict[str, list[dict[str, object]]]:
    """Compute added and removed topology nodes and edges."""
    previous_nodes = {node["id"]: node for node in _normalize_nodes(previous)}
    current_nodes = {node["id"]: node for node in _normalize_nodes(current)}

    previous_edges = { _edge_key(edge): edge for edge in _normalize_edges(previous) }
    current_edges = { _edge_key(edge): edge for edge in _normalize_edges(current) }

    removed_nodes = [node for node_id, node in previous_nodes.items() if node_id not in current_nodes]
    added_nodes = [node for node_id, node in current_nodes.items() if node_id not in previous_nodes]
    removed_edges = [edge for key, edge in previous_edges.items() if key not in current_edges]
    added_edges = [edge for key, edge in current_edges.items() if key not in previous_edges]

    return {
        "nodes_added": added_nodes,
        "nodes_removed": removed_nodes,
        "edges_added": added_edges,
        "edges_removed": removed_edges,
    }


def _normalize_nodes(payload: dict[str, object]) -> list[dict[str, object]]:
    items = payload.get("nodes")
    if isinstance(items, list):
        return [cast_node(node) for node in items if isinstance(node, dict)]
    return []


def _normalize_edges(payload: dict[str, object]) -> list[dict[str, object]]:
    items = payload.get("edges")
    if isinstance(items, list):
        return [cast_edge(edge) for edge in items if isinstance(edge, dict)]
    return []


def cast_node(data: object) -> dict[str, object]:
    if isinstance(data, dict):
        return data
    return {}


def cast_edge(data: object) -> dict[str, object]:
    if isinstance(data, dict):
        return data
    return {}


def _edge_key(edge: dict[str, object]) -> tuple[str, str, str]:
    return (
        str(edge.get("source") or ""),
        str(edge.get("target") or ""),
        str(edge.get("relationship") or ""),
    )
