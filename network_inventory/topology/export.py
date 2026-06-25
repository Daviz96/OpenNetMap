"""Basic topology export helpers."""

from __future__ import annotations

import html
import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import networkx as nx

from network_inventory.inventory.device import Device
from network_inventory.topology.builder import build_graph


def write_topology_exports(
    devices: list[Device], stats: Mapping[str, object], output_dir: str | Path
) -> list[Path]:
    """Write topology JSON, GraphML, GEXF and HTML files."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    graph = build_graph(devices, dict(stats))
    topology: dict[str, object] = {
        "nodes": [dict(data) for _, data in graph.nodes(data=True)],
        "edges": [dict(data) for _, _, data in graph.edges(data=True)],
        "metadata": graph.graph["metadata"],
    }
    outputs = [
        _write_json(topology, path / "topology.json"),
        _write_graphml(topology, path / "topology.graphml"),
        _write_gexf(graph, path / "topology.gexf"),
        _write_html(topology, path / "topology.html"),
    ]
    return outputs


def _write_gexf(graph: nx.DiGraph, path: Path) -> Path:
    """Esporta in GEXF, ripulendo gli attributi non scalari (no nested dict)."""
    clean: nx.DiGraph = nx.DiGraph()
    for node_id, data in graph.nodes(data=True):
        clean.add_node(
            node_id,
            label=str(data.get("label") or node_id),
            type=str(data.get("type") or ""),
            ip=str(data.get("ip") or ""),
            level=int(data.get("level") or 0),
        )
    for source, target, data in graph.edges(data=True):
        clean.add_edge(
            source,
            target,
            relationship=str(data.get("relationship") or ""),
            confidence=int(data.get("confidence") or 0),
        )
    nx.write_gexf(clean, str(path))
    return path


def _write_json(topology: dict[str, object], path: Path) -> Path:
    path.write_text(
        json.dumps(topology, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return path


def _write_graphml(topology: dict[str, object], path: Path) -> Path:
    nodes = cast(list[dict[str, object]], topology["nodes"])
    edges = cast(list[dict[str, object]], topology["edges"])
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '  <graph edgedefault="undirected">',
    ]
    for node in nodes:
        node_id = html.escape(str(node["id"]))
        label = html.escape(str(node.get("label") or node_id))
        lines.extend(
            [
                f'    <node id="{node_id}">',
                f'      <data key="label">{label}</data>',
                "    </node>",
            ]
        )
    for index, edge in enumerate(edges):
        source = html.escape(str(edge["source"]))
        target = html.escape(str(edge["target"]))
        lines.append(f'    <edge id="e{index}" source="{source}" target="{target}" />')
    lines.extend(["  </graph>", "</graphml>"])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_html(topology: dict[str, object], path: Path) -> Path:
    nodes = cast(list[dict[str, object]], topology["nodes"])
    edges = cast(list[dict[str, object]], topology["edges"])
    items = "\n".join(
        f"<li><strong>{html.escape(str(node.get('label')))}</strong> "
        f"<span>{html.escape(str(node.get('type', '')))}</span> "
        f"<code>{html.escape(str(node.get('ip', '')))}</code></li>"
        for node in nodes
    )
    document = f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Network Topology</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #101418; color: #ecf2f8; }}
    header {{ padding: 24px 32px; background: #19212b; }}
    main {{ padding: 24px 32px; }}
    li {{ margin: 8px 0; padding: 10px; background: #18212b; border: 1px solid #2c3b4f; border-radius: 6px; }}
    span {{ color: #93c5fd; margin-left: 8px; }}
    code {{ float: right; color: #cbd5e1; }}
  </style>
</head>
<body>
  <header><h1>Network Topology</h1><p>{len(nodes)} nodi, {len(edges)} collegamenti</p></header>
  <main><ul>{items}</ul></main>
</body>
</html>"""
    path.write_text(document, encoding="utf-8")
    return path
