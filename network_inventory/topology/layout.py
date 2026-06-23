"""Topology layout helpers using NetworkX and lightweight graph layouts."""

from __future__ import annotations

import networkx as nx
from typing import cast


def hierarchical_layout(graph: nx.Graph) -> dict[str, tuple[float, float]]:
    """Compute an approximate hierarchical layout."""
    try:
        return cast(dict[str, tuple[float, float]], nx.multipartite_layout(graph))
    except nx.NetworkXError:
        return cast(dict[str, tuple[float, float]], nx.spring_layout(graph, seed=42))


def force_directed_layout(graph: nx.Graph) -> dict[str, tuple[float, float]]:
    """Compute a force-directed layout."""
    return cast(dict[str, tuple[float, float]], nx.spring_layout(graph, seed=42))


def radial_layout(
    graph: nx.Graph, center: str | None = None
) -> dict[str, tuple[float, float]]:
    """Compute a radial layout around an optional center node."""
    try:
        if center and center in graph:
            return nx.shell_layout(
                graph, nlist=[[center], [n for n in graph if n != center]]
            )
        return nx.shell_layout(graph)
    except nx.NetworkXError:
        return nx.spring_layout(graph, seed=42)
