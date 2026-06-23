"""Basic topology export helpers."""

from __future__ import annotations

import html
import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from network_inventory.inventory.device import Device


def build_topology(
    devices: list[Device], subnet: str | None = None
) -> dict[str, object]:
    """Build a simple star topology from the scan result."""
    root_id = subnet or "network"
    nodes: list[dict[str, object]] = [
        {"id": root_id, "label": root_id, "type": "network"}
    ]
    edges: list[dict[str, object]] = []
    for device in devices:
        node_id = f"{device.mac or 'no-mac'}|{device.ip}"
        nodes.append(
            {
                "id": node_id,
                "label": device.hostname or device.ip,
                "ip": device.ip,
                "mac": device.mac,
                "type": device.device_type or "unknown",
                "security_score": device.security_score,
            }
        )
        edges.append({"source": root_id, "target": node_id, "relation": "discovered"})
    return {"nodes": nodes, "edges": edges}


def write_topology_exports(
    devices: list[Device], stats: Mapping[str, object], output_dir: str | Path
) -> list[Path]:
    """Write topology JSON, GraphML and HTML files."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    topology = build_topology(devices, str(stats.get("subnet") or "network"))
    outputs = [
        _write_json(topology, path / "topology.json"),
        _write_graphml(topology, path / "topology.graphml"),
        _write_html(topology, path / "topology.html"),
    ]
    return outputs


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
