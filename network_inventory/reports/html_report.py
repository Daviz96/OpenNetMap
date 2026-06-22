"""HTML report writer."""

from __future__ import annotations

import html
import json
from pathlib import Path

from network_inventory.inventory.device import Device


def write_html(
    devices: list[Device], stats: dict[str, object], output_dir: str | Path
) -> Path:
    """Write a searchable HTML report."""
    path = Path(output_dir) / "inventory.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(_row(device) for device in devices)
    stats_json = html.escape(json.dumps(stats, ensure_ascii=False))
    document = f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Network Inventory</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f6f8fb; color: #18212f; }}
    header {{ padding: 24px 32px; background: #18212f; color: white; }}
    main {{ padding: 24px 32px; }}
    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }}
    .stat {{ background: white; border: 1px solid #dce3ee; border-radius: 8px; padding: 14px; }}
    .stat b {{ display: block; font-size: 22px; margin-top: 4px; }}
    input {{ width: 100%; box-sizing: border-box; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 6px; margin-bottom: 12px; }}
    .table-wrap {{ overflow-x: auto; border: 1px solid #dce3ee; background: white; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid #dce3ee; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #e7edf5; text-align: left; vertical-align: top; }}
    th {{ cursor: pointer; background: #edf2f7; }}
    .badge {{ display: inline-block; padding: 3px 8px; border-radius: 999px; background: #e0f2fe; color: #075985; font-size: 12px; }}
    .mono, .ports {{ font-family: Consolas, monospace; }}
  </style>
</head>
<body>
  <header><h1>Network Inventory</h1><div>{html.escape(str(stats.get("subnet", "")))}</div></header>
  <main>
    <section class="stats" data-stats="{stats_json}">
      <div class="stat">Host totali<b>{stats.get("total_hosts", 0)}</b></div>
      <div class="stat">Host attivi<b>{stats.get("active_hosts", 0)}</b></div>
      <div class="stat">Host liberi<b>{stats.get("free_hosts", 0)}</b></div>
      <div class="stat">Utilizzo<b>{stats.get("utilization_percent", 0)}%</b></div>
    </section>
    <input id="search" placeholder="Cerca dispositivi">
    <div class="table-wrap">
      <table id="inventory">
        <thead><tr><th>IP</th><th>MAC</th><th>Hostname</th><th>Tipo</th><th>Conf.</th><th>Security</th><th>Produttore</th><th>Modello</th><th>Porte</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </main>
  <script>
    const search = document.querySelector("#search");
    search.addEventListener("input", () => {{
      const q = search.value.toLowerCase();
      document.querySelectorAll("#inventory tbody tr").forEach(row => {{
        row.style.display = row.innerText.toLowerCase().includes(q) ? "" : "none";
      }});
    }});
    document.querySelectorAll("th").forEach((th, index) => {{
      th.addEventListener("click", () => {{
        const tbody = document.querySelector("#inventory tbody");
        [...tbody.rows].sort((a, b) => a.cells[index].innerText.localeCompare(b.cells[index].innerText, undefined, {{numeric: true}}))
          .forEach(row => tbody.appendChild(row));
      }});
    }});
  </script>
</body>
</html>"""
    path.write_text(document, encoding="utf-8")
    return path


def _row(device: Device) -> str:
    ports = ", ".join(str(port) for port in device.open_ports)
    return (
        "<tr>"
        f'<td class="mono">{html.escape(device.ip)}</td>'
        f"<td class=\"mono\">{html.escape(device.mac or '')}</td>"
        f"<td>{html.escape(device.hostname or '')}</td>"
        f"<td><span class=\"badge\">{html.escape(device.device_type or 'Sconosciuto')}</span></td>"
        f"<td>{html.escape(str(device.classification_confidence or ''))}</td>"
        f"<td>{html.escape(str(device.security_score))}</td>"
        f"<td>{html.escape(device.manufacturer or device.vendor or '')}</td>"
        f"<td>{html.escape(device.model or '')}</td>"
        f'<td class="ports">{html.escape(ports)}</td>'
        "</tr>"
    )
