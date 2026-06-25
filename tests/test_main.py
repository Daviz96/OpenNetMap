from pathlib import Path

import pytest

from main import _parse_ports, parse_args, write_reports
from network_inventory.inventory.device import Device


def test_parse_args_defaults(monkeypatch):
    for var in (
        "OPENNETMAP_SUBNET",
        "OPENNETMAP_DB",
        "OPENNETMAP_HOST",
        "OPENNETMAP_PORT",
    ):
        monkeypatch.delenv(var, raising=False)
    args = parse_args([])

    assert args.subnet is None
    assert args.ports == "default"
    assert args.report == ["json"]
    assert args.threads == 100
    assert args.timeout == 1.0
    assert args.snmp is False
    assert args.output_dir == "reports_output"
    assert args.dashboard is False
    assert args.db is None
    assert args.host == "127.0.0.1"
    assert args.port == 8000


def test_parse_args_reads_env_vars(monkeypatch):
    monkeypatch.setenv("OPENNETMAP_SUBNET", "10.0.0.0/24")
    monkeypatch.setenv("OPENNETMAP_DB", "/data/inventory.db")
    monkeypatch.setenv("OPENNETMAP_HOST", "0.0.0.0")
    monkeypatch.setenv("OPENNETMAP_PORT", "9000")

    args = parse_args([])
    assert args.subnet == "10.0.0.0/24"
    assert args.db == "/data/inventory.db"
    assert args.host == "0.0.0.0"
    assert args.port == 9000


def test_parse_args_cli_overrides_env(monkeypatch):
    monkeypatch.setenv("OPENNETMAP_HOST", "0.0.0.0")
    monkeypatch.setenv("OPENNETMAP_PORT", "9000")

    args = parse_args(["--host", "127.0.0.1", "--port", "8080"])
    assert args.host == "127.0.0.1"
    assert args.port == 8080


def test_parse_args_custom_values():
    args = parse_args(
        [
            "--subnet",
            "192.168.1.0/24",
            "--ports",
            "22,80",
            "--report",
            "json",
            "html",
            "--threads",
            "20",
            "--timeout",
            "2.5",
            "--snmp",
            "--verbose",
            "--output-dir",
            "outdir",
        ]
    )

    assert args.subnet == "192.168.1.0/24"
    assert args.ports == "22,80"
    assert args.report == ["json", "html"]
    assert args.threads == 20
    assert args.timeout == 2.5
    assert args.snmp is True
    assert args.verbose is True
    assert args.output_dir == "outdir"


def test_parse_ports_custom_list_and_invalid():
    assert _parse_ports("22,80") == [22, 80]

    with pytest.raises(ValueError, match="Porte non valide"):
        _parse_ports("0,70000")

    full_ports = _parse_ports("full")
    assert isinstance(full_ports, list)
    assert len(full_ports) > 0


def test_write_reports_generates_all_formats(tmp_path: Path):
    devices = [Device(ip="192.168.1.20", hostname="device")]
    stats = {"subnet": "192.168.1.0/24", "active_hosts": 1}

    paths = write_reports(devices, stats, ["json", "csv", "html"], str(tmp_path))

    assert any(path.name == "inventory.json" for path in paths)
    assert any(path.name == "inventory.csv" for path in paths)
    assert any(path.name == "inventory.html" for path in paths)
    assert (tmp_path / "inventory.json").exists()
    assert (tmp_path / "inventory.csv").exists()
    assert (tmp_path / "inventory.html").exists()
