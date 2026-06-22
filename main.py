"""Command-line entry point for the network inventory tool."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3 import disable_warnings
from rich.console import Console
from rich.table import Table

from network_inventory.database.store import InventoryStore
from network_inventory.events.engine import compare_snapshots
from network_inventory.fingerprint.classifier import classify_with_details
from network_inventory.inventory.device import Device
from network_inventory.inventory.inventory import InventoryRunner, enrich_device_identity
from network_inventory.reports.csv_report import write_csv
from network_inventory.reports.html_report import write_html
from network_inventory.reports.json_report import write_json
from network_inventory.security.assessment import assess_device
from network_inventory.topology.export import write_topology_exports
from network_inventory.utils.config import DEFAULT_PORTS, FULL_PORTS, TOP_PORTS, ScanConfig
from network_inventory.utils.logger import configure_logging
from network_inventory.utils.oui import OuiDatabase, update_oui_database

disable_warnings(InsecureRequestWarning)
CONSOLE = Console()


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""
    args = parse_args(argv)
    configure_logging(args.verbose)

    if args.dashboard:
        return run_dashboard(args.db or "inventory.db", args.host, args.port)

    config = ScanConfig(
        subnet=args.subnet,
        ports=_parse_ports(args.ports),
        threads=args.threads,
        timeout=args.timeout,
        snmp_enabled=args.snmp,
        verbose=args.verbose,
        report_formats=args.report,
        output_dir=args.output_dir,
    )

    try:
        if args.update_oui:
            path = update_oui_database()
            CONSOLE.print(f"[green]Database OUI aggiornato:[/green] {path}")
            if not args.from_json:
                return 0
        if args.monitor:
            return run_monitor(config, args)
        run_once(config, args)
    except Exception as exc:
        CONSOLE.print(f"[red]Errore:[/red] {exc}")
        return 1
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="LAN scanner and network inventory tool")
    parser.add_argument("--subnet", help="Subnet da scansionare, es. 192.168.1.0/24")
    parser.add_argument("--ports", default="default", help="default, top, full oppure lista: 22,80,443")
    parser.add_argument("--report", nargs="+", default=["json"], choices=["csv", "json", "html"], help="Formato report")
    parser.add_argument("--threads", type=int, default=100, help="Numero massimo di thread")
    parser.add_argument("--timeout", type=float, default=1.0, help="Timeout connessioni in secondi")
    parser.add_argument("--snmp", action="store_true", help="Forza scansione SNMP anche se la porta 161 non risulta aperta")
    parser.add_argument("--verbose", action="store_true", help="Logging dettagliato")
    parser.add_argument("--output-dir", default="reports_output", help="Cartella output report")
    parser.add_argument("--from-json", help="Rigenera report da un inventory.json esistente senza rifare la scansione")
    parser.add_argument("--update-oui", action="store_true", help="Scarica/aggiorna il database locale IEEE OUI oui.txt")
    parser.add_argument("--db", help="Salva la scansione in un database SQLite, es. inventory.db")
    parser.add_argument("--topology", action="store_true", help="Genera topology.json, topology.graphml e topology.html")
    parser.add_argument("--dashboard", action="store_true", help="Avvia API/dashboard FastAPI")
    parser.add_argument("--host", default="127.0.0.1", help="Host dashboard/API")
    parser.add_argument("--port", type=int, default=8000, help="Porta dashboard/API")
    parser.add_argument("--monitor", action="store_true", help="Esegue scansioni continue e genera eventi")
    parser.add_argument("--interval", type=int, default=300, help="Intervallo monitor in secondi")
    return parser.parse_args(argv)


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
        raise ValueError(f"Porte non valide: {invalid}")
    return ports


def print_table(devices: list[Device]) -> None:
    """Print inventory summary table."""
    table = Table(title="Network Inventory")
    table.add_column("IP", no_wrap=True)
    table.add_column("MAC", no_wrap=True)
    table.add_column("Hostname")
    table.add_column("Tipo dispositivo")
    table.add_column("Conf.")
    table.add_column("Security")
    table.add_column("Produttore")
    table.add_column("Modello")
    table.add_column("Porte aperte")

    for device in devices:
        table.add_row(
            device.ip,
            device.mac or "",
            device.hostname or "",
            device.device_type or "Sconosciuto",
            str(device.classification_confidence or ""),
            str(device.security_score),
            device.manufacturer or device.vendor or "",
            device.model or "",
            ", ".join(str(port) for port in device.open_ports),
        )
    CONSOLE.print(table)


def write_reports(
    devices: list[Device],
    stats: dict[str, object],
    formats: list[str],
    output_dir: str,
) -> list[Path]:
    """Write requested reports."""
    paths: list[Path] = []
    if "json" in formats:
        paths.append(write_json(devices, stats, output_dir))
    if "csv" in formats:
        paths.append(write_csv(devices, output_dir))
    if "html" in formats:
        paths.append(write_html(devices, stats, output_dir))
    return paths


def run_once(config: ScanConfig, args: argparse.Namespace) -> tuple[list[Device], dict[str, object]]:
    """Run one scan/import cycle and write selected outputs."""
    if args.from_json:
        devices, stats = load_inventory(args.from_json)
    else:
        runner = InventoryRunner(config)
        devices, stats = runner.run()
    print_table(devices)
    paths = write_reports(devices, stats, config.report_formats, config.output_dir)
    if args.topology:
        paths.extend(write_topology_exports(devices, stats, config.output_dir))
    if args.db:
        store = InventoryStore(args.db)
        previous = store.load_latest_devices()
        events = compare_snapshots(previous, devices)
        scan_id = store.save_scan(devices, stats, events)
        CONSOLE.print(f"[green]SQLite aggiornato:[/green] {args.db} scan_id={scan_id} eventi={len(events)}")
    for path in paths:
        CONSOLE.print(f"[green]Report creato:[/green] {path}")
    return devices, stats


def run_monitor(config: ScanConfig, args: argparse.Namespace) -> int:
    """Run continuous monitoring scans."""
    if args.from_json:
        CONSOLE.print("[red]Errore:[/red] --monitor non puo usare --from-json; serve una scansione reale.")
        return 1
    if not args.db:
        args.db = str(Path(config.output_dir) / "enterprise_inventory.db")
        CONSOLE.print(f"[yellow]DB non specificato, uso:[/yellow] {args.db}")
    CONSOLE.print(f"[green]Monitor attivo[/green] intervallo={args.interval}s db={args.db}")
    while True:
        started = time.strftime("%Y-%m-%d %H:%M:%S")
        CONSOLE.print(f"[cyan]Nuova scansione:[/cyan] {started}")
        run_once(config, args)
        CONSOLE.print(f"[cyan]In attesa:[/cyan] {args.interval}s")
        time.sleep(max(args.interval, 1))


def load_inventory(path: str) -> tuple[list[Device], dict[str, object]]:
    """Load inventory data from a previous JSON report."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    stats = dict(payload.get("stats") or {})
    oui = OuiDatabase()
    devices = [Device.from_dict(item) for item in payload.get("devices", [])]
    for device in devices:
        if not device.vendor:
            device.vendor = oui.lookup(device.mac)
        enrich_device_identity(device)
        classification = classify_with_details(device)
        device.device_type = device.device_type or classification.device_type
        device.os_guess = device.os_guess or classification.os_guess
        device.classification_confidence = device.classification_confidence or classification.confidence
        device.classification_reasons = device.classification_reasons or classification.reasons
        assessment = assess_device(device)
        device.security_score = assessment.score
        device.findings = assessment.findings
        device.recommendations = assessment.recommendations
    return devices, stats


def run_dashboard(db_path: str, host: str, port: int) -> int:
    """Run the FastAPI dashboard/API server."""
    try:
        import uvicorn

        from network_inventory.api.app import create_app
    except ImportError as exc:
        CONSOLE.print(f"[red]Dipendenza mancante:[/red] {exc}")
        CONSOLE.print("Installa le dipendenze aggiornate con: pip install -r requirements.txt")
        return 1

    app = create_app(db_path)
    CONSOLE.print(f"[green]Dashboard/API:[/green] http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
