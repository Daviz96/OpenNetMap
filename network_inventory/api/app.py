"""FastAPI application and dashboard pages for inventory data."""

from __future__ import annotations

import fnmatch
import html
import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from network_inventory.database.store import InventoryStore
from network_inventory.events.engine import compare_snapshots
from network_inventory.fingerprint.classifier import classify_with_details
from network_inventory.inventory.device import Device
from network_inventory.inventory.inventory import (
    InventoryRunner,
    enrich_device_identity,
)
from network_inventory.reports.csv_report import write_csv
from network_inventory.reports.html_report import write_html
from network_inventory.reports.json_report import write_json
from network_inventory.security.assessment import assess_device
from network_inventory.topology.export import write_topology_exports
from network_inventory.utils.config import (
    DEFAULT_PORTS,
    FULL_PORTS,
    TOP_PORTS,
    ScanConfig,
)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass(slots=True)
class ScanJob:
    """In-memory API scan job state."""

    id: str
    status: str = "queued"
    created_at: str = field(default_factory=_utc_now)
    started_at: str | None = None
    finished_at: str | None = None
    scan_id: int | None = None
    device_count: int = 0
    event_count: int = 0
    output_paths: list[str] = field(default_factory=list)
    error: str | None = None


class ScanRequest(BaseModel):
    """Request body for POST /scan."""

    subnet: str | None = None
    ports: str = Field(
        default="default", description="default, top, full, or comma-separated ports"
    )
    report: list[str] = Field(default_factory=lambda: ["json", "html"])
    threads: int = Field(default=100, ge=1, le=1000)
    timeout: float = Field(default=1.0, ge=0.1, le=30.0)
    snmp: bool = False
    output_dir: str = "reports_output"
    db: str | None = None
    topology: bool = True
    dry_run_from_json: str | None = Field(
        default=None, description="Load an existing inventory JSON instead of scanning"
    )


_JOBS: dict[str, ScanJob] = {}
_JOBS_LOCK = threading.Lock()


def create_app(db_path: str = "inventory.db") -> FastAPI:
    """Create the REST API and dashboard application."""
    InventoryStore(db_path)
    app = FastAPI(title="Network Inventory API", version="0.2.0")

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        stats_payload = _latest_stats(db_path)
        recent_events = _query_events(db_path, 10)
        risky_devices = _query_risky_devices(db_path, 10)
        counts = _summary_counts(db_path)
        with _JOBS_LOCK:
            jobs = [_job_to_dict(job) for job in _JOBS.values()]
        jobs.sort(key=lambda item: item["created_at"], reverse=True)
        return _render_dashboard(
            stats_payload, recent_events, risky_devices, counts, jobs[:5]
        )

    @app.get("/dashboard/devices", response_class=HTMLResponse)
    def devices_page(q: str | None = None, sort: str = "ip") -> str:
        rows = _query_devices(db_path, 10000, 0, q, sort)
        return _render_devices_page(rows, q or "", sort)

    @app.get("/dashboard/events", response_class=HTMLResponse)
    def events_page(
        q: str | None = None, limit: int = Query(250, ge=1, le=2000)
    ) -> str:
        rows = _query_events(db_path, limit, q)
        return _render_events_page(rows, q or "")

    @app.get("/devices")
    def devices(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        q: str | None = None,
        sort: str = "ip",
    ) -> dict[str, Any]:
        rows = _query_devices(db_path, limit, offset, q, sort)
        return {
            "items": rows,
            "limit": limit,
            "offset": offset,
            "query": q,
            "sort": sort,
        }

    @app.get("/devices/{device_key}")
    def device(device_key: str) -> dict[str, Any]:
        row = _query_device(db_path, device_key)
        return row or {"error": "not_found"}

    @app.get("/stats")
    def stats() -> dict[str, Any]:
        return _latest_stats(db_path)

    @app.get("/events")
    def events(
        limit: int = Query(100, ge=1, le=1000), q: str | None = None
    ) -> dict[str, Any]:
        return {"items": _query_events(db_path, limit, q), "query": q}

    @app.get("/topology")
    def topology() -> dict[str, Any]:
        path = Path("reports_output") / "topology.json"
        if not path.exists():
            return {"nodes": [], "edges": []}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
        return {"nodes": [], "edges": []}

    @app.get("/vlans")
    def vlans() -> dict[str, Any]:
        return {"items": _query_vlans(db_path)}

    @app.get("/scans")
    def scans(limit: int = Query(50, ge=1, le=500)) -> dict[str, Any]:
        return {"items": _query_scans(db_path, limit)}

    @app.post("/scan")
    def scan(request: ScanRequest) -> dict[str, Any]:
        job = ScanJob(id=str(uuid.uuid4()))
        with _JOBS_LOCK:
            _JOBS[job.id] = job
        thread = threading.Thread(
            target=_run_scan_job, args=(job.id, request, db_path), daemon=True
        )
        thread.start()
        return _job_to_dict(job)

    @app.get("/scan/jobs")
    def scan_jobs() -> dict[str, Any]:
        with _JOBS_LOCK:
            jobs = [_job_to_dict(job) for job in _JOBS.values()]
        jobs.sort(key=lambda item: item["created_at"], reverse=True)
        return {"items": jobs}

    @app.get("/scan/jobs/{job_id}")
    def scan_job(job_id: str) -> dict[str, Any]:
        with _JOBS_LOCK:
            job = _JOBS.get(job_id)
        return _job_to_dict(job) if job else {"error": "not_found"}

    return app


def _run_scan_job(job_id: str, request: ScanRequest, default_db_path: str) -> None:
    _update_job(job_id, status="running", started_at=_utc_now())
    try:
        devices, stats = _load_or_scan(request)
        output_paths = _write_scan_outputs(devices, stats, request)
        db_target = request.db or default_db_path
        store = InventoryStore(db_target)
        previous = store.load_latest_devices()
        events = compare_snapshots(previous, devices)
        scan_id = store.save_scan(devices, stats, events)
        _update_job(
            job_id,
            status="completed",
            finished_at=_utc_now(),
            scan_id=scan_id,
            device_count=len(devices),
            event_count=len(events),
            output_paths=output_paths,
        )
    except Exception as exc:
        _update_job(job_id, status="failed", finished_at=_utc_now(), error=str(exc))


def _load_or_scan(request: ScanRequest) -> tuple[list[Device], dict[str, object]]:
    if request.dry_run_from_json:
        return _load_inventory_json(request.dry_run_from_json)
    config = ScanConfig(
        subnet=request.subnet,
        ports=_parse_ports(request.ports),
        threads=request.threads,
        timeout=request.timeout,
        snmp_enabled=request.snmp,
        report_formats=request.report,
        output_dir=request.output_dir,
    )
    return InventoryRunner(config).run()


def _write_scan_outputs(
    devices: list[Device], stats: dict[str, object], request: ScanRequest
) -> list[str]:
    paths: list[Path] = []
    formats = set(request.report)
    if "json" in formats:
        paths.append(write_json(devices, stats, request.output_dir))
    if "csv" in formats:
        paths.append(write_csv(devices, request.output_dir))
    if "html" in formats:
        paths.append(write_html(devices, stats, request.output_dir))
    if request.topology:
        paths.extend(write_topology_exports(devices, stats, request.output_dir))
    return [str(path) for path in paths]


def _load_inventory_json(path: str) -> tuple[list[Device], dict[str, object]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        stats_payload = payload.get("stats")
        if isinstance(stats_payload, dict):
            stats = {str(key): value for key, value in stats_payload.items()}
        else:
            stats = {}
        devices_payload = payload.get("devices")
        devices_items = devices_payload if isinstance(devices_payload, list) else []
    else:
        stats = {}
        devices_items = []
    devices = [Device.from_dict(item) for item in devices_items]
    for device in devices:
        enrich_device_identity(device)
        classification = classify_with_details(device)
        device.device_type = device.device_type or classification.device_type
        device.os_guess = device.os_guess or classification.os_guess
        device.classification_confidence = (
            device.classification_confidence or classification.confidence
        )
        device.classification_reasons = (
            device.classification_reasons or classification.reasons
        )
        assessment = assess_device(device)
        device.security_score = assessment.score
        device.findings = assessment.findings
        device.recommendations = assessment.recommendations
    return devices, stats


def _parse_ports(value: str) -> list[int]:
    normalized = value.lower().strip()
    if normalized == "default":
        return DEFAULT_PORTS.copy()
    if normalized == "top":
        return TOP_PORTS.copy()
    if normalized == "full":
        return FULL_PORTS.copy()
    ports = sorted({int(port.strip()) for port in value.split(",") if port.strip()})
    invalid = [port for port in ports if port < 1 or port > 65535]
    if invalid:
        raise ValueError(f"Invalid ports: {invalid}")
    return ports


def _update_job(job_id: str, **changes: object) -> None:
    with _JOBS_LOCK:
        job = _JOBS[job_id]
        for key, value in changes.items():
            setattr(job, key, value)


def _job_to_dict(job: ScanJob) -> dict[str, Any]:
    return {
        "id": job.id,
        "status": job.status,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "scan_id": job.scan_id,
        "device_count": job.device_count,
        "event_count": job.event_count,
        "output_paths": job.output_paths,
        "error": job.error,
    }


def _connect(db_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _query_devices(
    db_path: str, limit: int, offset: int, q: str | None, sort: str = "ip"
) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT device_key, ip, mac, hostname, vendor, device_type, manufacturer, model, last_json FROM devices"
        ).fetchall()
    devices = [_device_row(row) for row in rows]
    devices = _filter_devices(devices, q)
    devices.sort(key=lambda item: _sort_value(item, sort))
    return devices[offset : offset + limit]


def _query_device(db_path: str, device_key: str) -> dict[str, Any] | None:
    with _connect(db_path) as connection:
        row = connection.execute(
            "SELECT last_json FROM devices WHERE device_key = ?", (device_key,)
        ).fetchone()
    if not row:
        return None
    data = json.loads(row["last_json"])
    return data if isinstance(data, dict) else None


def _latest_stats(db_path: str) -> dict[str, Any]:
    with _connect(db_path) as connection:
        row = connection.execute(
            "SELECT stats_json FROM scans ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if not row:
        return {}
    data = json.loads(row["stats_json"])
    return data if isinstance(data, dict) else {}


def _query_events(
    db_path: str, limit: int, q: str | None = None
) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT event_type, device_key, message, timestamp FROM events ORDER BY id DESC LIMIT ?",
            (max(limit * 5, limit),),
        ).fetchall()
    events = [dict(row) for row in rows]
    if q:
        query = q.lower()
        events = [
            event
            for event in events
            if query in " ".join(str(value).lower() for value in event.values())
        ]
    return events[:limit]


def _query_vlans(db_path: str) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT vlan_id, vlan_name, subnet, source FROM vlans ORDER BY vlan_id"
        ).fetchall()
    return [dict(row) for row in rows]


def _query_scans(db_path: str, limit: int) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT id, started_at, stats_json FROM scans ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "started_at": row["started_at"],
            "stats": _ensure_dict(json.loads(row["stats_json"])),
        }
        for row in rows
    ]


def _query_risky_devices(db_path: str, limit: int) -> list[dict[str, Any]]:
    devices = _query_devices(db_path, 1000, 0, None)
    devices.sort(key=lambda item: int(item.get("security_score") or 100))
    return devices[:limit]


def _summary_counts(db_path: str) -> dict[str, int]:
    with _connect(db_path) as connection:
        devices_count = connection.execute(
            "SELECT COUNT(*) AS count FROM devices"
        ).fetchone()["count"]
        events_count = connection.execute(
            "SELECT COUNT(*) AS count FROM events"
        ).fetchone()["count"]
        scans_count = connection.execute(
            "SELECT COUNT(*) AS count FROM scans"
        ).fetchone()["count"]
    return {"devices": devices_count, "events": events_count, "scans": scans_count}


def _device_row(row: sqlite3.Row) -> dict[str, Any]:
    data = json.loads(row["last_json"])
    if not isinstance(data, dict):
        data = {}
    data["device_key"] = row["device_key"]
    return data


def _filter_devices(
    devices: list[dict[str, Any]], query: str | None
) -> list[dict[str, Any]]:
    if not query:
        return devices
    clauses = [clause.strip() for clause in query.split(" and ") if clause.strip()]
    return [
        device
        for device in devices
        if all(_match_clause(device, clause) for clause in clauses)
    ]


def _match_clause(device: dict[str, Any], clause: str) -> bool:
    if ":" not in clause:
        return clause.lower() in _device_search_text(device)
    field, raw_value = clause.split(":", 1)
    field = field.strip().lower()
    value = raw_value.strip().lower()
    if field == "vendor":
        return (
            value
            in str(device.get("vendor") or device.get("manufacturer") or "").lower()
        )
    if field in {"type", "device_type"}:
        return value in str(device.get("device_type") or "").lower()
    if field == "port":
        return _safe_int(value) in {int(port) for port in device.get("open_ports", [])}
    if field == "os":
        return value in str(device.get("os_guess") or "").lower()
    if field == "ip":
        return fnmatch.fnmatch(str(device.get("ip") or ""), value.replace("%", "*"))
    if field == "hostname":
        return value in str(device.get("hostname") or "").lower()
    if field == "mac":
        return value in str(device.get("mac") or "").lower()
    if field == "vlan":
        return value in str(device.get("vlan") or "").lower()
    if field in {"risk", "security"}:
        score = int(device.get("security_score") or 100)
        expected = _safe_int(value)
        return expected is not None and score <= expected
    return value in str(device.get(field) or "").lower()


def _device_search_text(device: dict[str, Any]) -> str:
    return " ".join(
        str(value).lower()
        for value in [
            device.get("ip"),
            device.get("mac"),
            device.get("hostname"),
            device.get("vendor"),
            device.get("manufacturer"),
            device.get("model"),
            device.get("device_type"),
            device.get("os_guess"),
            device.get("open_ports"),
        ]
        if value is not None
    )


def _sort_value(device: dict[str, Any], sort: str) -> str | int:
    key = sort.strip().lower()
    if key == "security":
        return int(device.get("security_score") or 100)
    if key == "ports":
        return len(device.get("open_ports", []))
    return str(device.get(key) or "").lower()


def _safe_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def _render_dashboard(
    stats: dict[str, Any],
    events: list[dict[str, Any]],
    risky_devices: list[dict[str, Any]],
    counts: dict[str, int],
    jobs: list[dict[str, Any]],
) -> str:
    event_rows = "".join(
        f"<tr><td>{_esc(event['timestamp'])}</td><td>{_esc(event['event_type'])}</td><td>{_esc(event['message'])}</td></tr>"
        for event in events
    )
    risky_rows = "".join(
        "<tr>"
        f"<td>{_esc(device.get('ip'))}</td>"
        f"<td>{_esc(device.get('hostname'))}</td>"
        f"<td>{_esc(device.get('device_type'))}</td>"
        f"<td>{_esc(device.get('manufacturer') or device.get('vendor'))}</td>"
        f"<td>{_esc(device.get('security_score'))}</td>"
        "</tr>"
        for device in risky_devices
    )
    job_rows = "".join(
        "<tr>"
        f"<td><code>{_esc(job.get('id'))}</code></td>"
        f"<td>{_esc(job.get('status'))}</td>"
        f"<td>{_esc(job.get('device_count'))}</td>"
        f"<td>{_esc(job.get('event_count'))}</td>"
        f"<td>{_esc(job.get('error'))}</td>"
        "</tr>"
        for job in jobs
    )
    content = f"""
    <div class="stats">
      <div class="stat">Dispositivi inventariati<b>{counts["devices"]}</b></div>
      <div class="stat">Scansioni salvate<b>{counts["scans"]}</b></div>
      <div class="stat">Eventi totali<b>{counts["events"]}</b></div>
      <div class="stat">Utilizzo subnet<b>{_esc(stats.get("utilization_percent", 0))}%</b></div>
    </div>
    <section>
      <h2>Dispositivi piu rischiosi</h2>
      <table><thead><tr><th>IP</th><th>Hostname</th><th>Tipo</th><th>Produttore</th><th>Score</th></tr></thead><tbody>{risky_rows}</tbody></table>
    </section>
    <section>
      <h2>Scan job recenti</h2>
      <p class="hint">Avvio API: <code>POST /scan</code>. Stato: <code>GET /scan/jobs</code>.</p>
      <table><thead><tr><th>Job</th><th>Stato</th><th>Dispositivi</th><th>Eventi</th><th>Errore</th></tr></thead><tbody>{job_rows}</tbody></table>
    </section>
    <section>
      <h2>Ultimi eventi</h2>
      <table><thead><tr><th>Timestamp</th><th>Tipo</th><th>Messaggio</th></tr></thead><tbody>{event_rows}</tbody></table>
    </section>
"""
    return _page_shell(
        "Network Inventory Dashboard",
        content,
        subtitle=f"Subnet {_esc(stats.get('subnet', ''))}",
    )


def _render_devices_page(devices: list[dict[str, Any]], query: str, sort: str) -> str:
    rows = "".join(
        "<tr>"
        f"<td><code>{_esc(device.get('ip'))}</code></td>"
        f"<td><code>{_esc(device.get('mac'))}</code></td>"
        f"<td>{_esc(device.get('hostname'))}</td>"
        f"<td>{_esc(device.get('device_type'))}</td>"
        f"<td>{_esc(device.get('manufacturer') or device.get('vendor'))}</td>"
        f"<td>{_esc(device.get('model'))}</td>"
        f"<td>{_esc(device.get('security_score'))}</td>"
        f"<td>{_esc(', '.join(str(port) for port in device.get('open_ports', [])))}</td>"
        "</tr>"
        for device in devices
    )
    content = f"""
    <form class="toolbar" method="get">
      <input name="q" value="{_esc(query)}" placeholder="vendor:Brother and port:9100">
      <select name="sort">
        {_option("ip", sort, "IP")}
        {_option("security", sort, "Security")}
        {_option("device_type", sort, "Tipo")}
        {_option("manufacturer", sort, "Produttore")}
        {_option("ports", sort, "Numero porte")}
      </select>
      <button type="submit">Filtra</button>
    </form>
    <p class="hint">Esempi: <code>vendor:Brother</code> <code>type:Stampante and port:9100</code> <code>ip:192.168.100.*</code> <code>security:80</code></p>
    <table><thead><tr><th>IP</th><th>MAC</th><th>Hostname</th><th>Tipo</th><th>Produttore</th><th>Modello</th><th>Security</th><th>Porte</th></tr></thead><tbody>{rows}</tbody></table>
"""
    return _page_shell("Dispositivi", content, subtitle=f"{len(devices)} risultati")


def _render_events_page(events: list[dict[str, Any]], query: str) -> str:
    rows = "".join(
        "<tr>"
        f"<td><code>{_esc(event.get('timestamp'))}</code></td>"
        f"<td>{_esc(event.get('event_type'))}</td>"
        f"<td><code>{_esc(event.get('device_key'))}</code></td>"
        f"<td>{_esc(event.get('message'))}</td>"
        "</tr>"
        for event in events
    )
    content = f"""
    <form class="toolbar" method="get">
      <input name="q" value="{_esc(query)}" placeholder="PORT_OPENED, 192.168.100, Brother">
      <button type="submit">Filtra</button>
    </form>
    <table><thead><tr><th>Timestamp</th><th>Tipo</th><th>Dispositivo</th><th>Messaggio</th></tr></thead><tbody>{rows}</tbody></table>
"""
    return _page_shell("Eventi", content, subtitle=f"{len(events)} eventi")


def _page_shell(title: str, content: str, subtitle: str = "") -> str:
    return f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)}</title>
  <style>
    body {{ margin: 0; font-family: Segoe UI, Arial, sans-serif; background: #0f141b; color: #e5edf6; }}
    header {{ padding: 22px 30px; background: #17202c; border-bottom: 1px solid #2b3a4f; }}
    main {{ padding: 24px 30px; }}
    nav {{ margin-top: 12px; display: flex; gap: 14px; flex-wrap: wrap; }}
    .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 22px; }}
    .stat {{ background: #17202c; border: 1px solid #2b3a4f; border-radius: 8px; padding: 14px; }}
    .stat b {{ display: block; font-size: 24px; margin-top: 4px; color: #93c5fd; }}
    section {{ margin-top: 24px; }}
    table {{ width: 100%; border-collapse: collapse; background: #111923; border: 1px solid #2b3a4f; }}
    th, td {{ padding: 9px 11px; border-bottom: 1px solid #233044; text-align: left; vertical-align: top; }}
    th {{ color: #bfdbfe; background: #17202c; }}
    code {{ color: #cbd5e1; }}
    a {{ color: #93c5fd; }}
    .toolbar {{ display: grid; grid-template-columns: minmax(240px, 1fr) 180px auto; gap: 10px; margin-bottom: 12px; }}
    input, select, button {{ background: #111923; color: #e5edf6; border: 1px solid #2b3a4f; border-radius: 6px; padding: 9px 10px; }}
    button {{ cursor: pointer; color: #bfdbfe; }}
    .hint {{ color: #a8b3c2; }}
  </style>
</head>
<body>
  <header>
    <h1>{_esc(title)}</h1>
    <div>{subtitle}</div>
    <nav>
      <a href="/">Dashboard</a>
      <a href="/dashboard/devices">Dispositivi</a>
      <a href="/dashboard/events">Eventi</a>
      <a href="/devices">API dispositivi</a>
      <a href="/events">API eventi</a>
      <a href="/topology">API topologia</a>
      <a href="/scan/jobs">API scan jobs</a>
    </nav>
  </header>
  <main>{content}</main>
</body>
</html>"""


def _option(value: str, current: str, label: str) -> str:
    selected = " selected" if value == current else ""
    return f'<option value="{_esc(value)}"{selected}>{_esc(label)}</option>'


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value))
