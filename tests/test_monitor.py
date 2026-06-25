import argparse
import signal
import threading
from pathlib import Path

import main
from network_inventory.utils.config import ScanConfig


def test_install_stop_handlers_sets_event_on_signal():
    original = signal.getsignal(signal.SIGINT)
    try:
        event = threading.Event()
        main._install_stop_handlers(event)
        handler = signal.getsignal(signal.SIGINT)
        assert callable(handler)
        handler(signal.SIGINT, None)
        assert event.is_set()
    finally:
        signal.signal(signal.SIGINT, original)


def test_run_monitor_stops_after_signal(tmp_path: Path, monkeypatch):
    captured: dict[str, threading.Event] = {}

    def fake_install(event: threading.Event) -> None:
        captured["event"] = event

    calls = {"count": 0}

    def fake_run_once(config: ScanConfig, args: argparse.Namespace):
        calls["count"] += 1
        # Simulate a stop signal arriving during the first scan.
        captured["event"].set()
        return [], {}

    monkeypatch.setattr(main, "_install_stop_handlers", fake_install)
    monkeypatch.setattr(main, "run_once", fake_run_once)

    args = argparse.Namespace(
        from_json=None, db=str(tmp_path / "monitor.db"), interval=1
    )
    result = main.run_monitor(ScanConfig(), args)

    assert result == 0
    assert calls["count"] == 1


def test_run_monitor_rejects_from_json():
    args = argparse.Namespace(from_json="x.json", db=None, interval=1)
    assert main.run_monitor(ScanConfig(), args) == 1
