"""Tests for the mDNS scanner."""

from __future__ import annotations

import socket
import threading
from typing import Any
from unittest.mock import MagicMock, patch

from network_inventory.scanner.mdns_scanner import scan_mdns, scan_mdns_network


class _FakeListener:
    """Minimal base class to stand in for zeroconf.ServiceListener."""


def _make_zeroconf_module(
    zc_instance: MagicMock,
    browser_factory: Any = None,
) -> MagicMock:
    """Build a mock 'zeroconf' module for sys.modules injection."""
    mod = MagicMock()
    mod.Zeroconf.return_value = zc_instance
    mod.ServiceListener = _FakeListener
    if browser_factory is not None:
        mod.ServiceBrowser.side_effect = browser_factory
    else:
        mod.ServiceBrowser.return_value = MagicMock()
    return mod


def _make_info(ip: str, port: int, server: str) -> MagicMock:
    info = MagicMock()
    info.addresses = [socket.inet_aton(ip)]
    info.port = port
    info.server = server
    return info


class TestScanMdns:
    def test_returns_empty_when_zeroconf_missing(self) -> None:
        with patch.dict("sys.modules", {"zeroconf": None}):
            result = scan_mdns("192.168.1.1")
        assert result == {}

    def test_returns_empty_when_no_matching_ip(self) -> None:
        mock_zc = MagicMock()
        mod = _make_zeroconf_module(mock_zc)
        with patch.dict("sys.modules", {"zeroconf": mod}):
            result = scan_mdns("10.0.0.1", timeout=0.01)
        assert result == {}

    def _run_with_events(
        self,
        ip: str,
        info: MagicMock | None,
        stype: str = "_http._tcp.local.",
        name: str = "Device._http._tcp.local.",
    ) -> dict[str, object]:
        """Helper: run scan_mdns with a single simulated add_service event."""
        mock_zc = MagicMock()
        mock_zc.get_service_info.return_value = info

        captured: list[Any] = []

        def fake_browser(zc: Any, stype_: str, listener: Any) -> MagicMock:
            captured.append(listener)
            return MagicMock()

        mod = _make_zeroconf_module(mock_zc, browser_factory=fake_browser)

        def fire_and_return(
            self: threading.Event, timeout: float | None = None
        ) -> bool:
            for lst in captured:
                lst.add_service(mock_zc, stype, name)
            return False

        with patch.dict("sys.modules", {"zeroconf": mod}):
            with patch.object(threading.Event, "wait", fire_and_return):
                return scan_mdns(ip, timeout=0.01)

    def test_service_found_for_matching_ip(self) -> None:
        target_ip = "192.168.1.10"
        info = _make_info(target_ip, 80, "mydevice.local.")
        result = self._run_with_events(target_ip, info)

        assert "services" in result
        services = result["services"]
        assert isinstance(services, list)
        assert len(services) >= 1
        svc = services[0]
        assert isinstance(svc, dict)
        assert svc["port"] == 80

    def test_service_skipped_for_different_ip(self) -> None:
        target_ip = "192.168.1.10"
        other_ip = "192.168.1.99"
        info = _make_info(other_ip, 80, "other.local.")
        result = self._run_with_events(target_ip, info)
        assert result == {}

    def test_hostname_extracted_from_server_field(self) -> None:
        target_ip = "192.168.1.10"
        info = _make_info(target_ip, 22, "printer.local.")
        result = self._run_with_events(
            target_ip, info, "_ssh._tcp.local.", "Printer._ssh._tcp.local."
        )
        assert result.get("hostname") == "printer.local"

    def test_none_service_info_ignored(self) -> None:
        target_ip = "192.168.1.10"
        result = self._run_with_events(target_ip, None)
        assert result == {}


class TestScanMdnsNetwork:
    def test_close_timeout_does_not_raise(self) -> None:
        """Un TimeoutError da zc.close() non deve propagare (best-effort)."""
        mock_zc = MagicMock()
        mock_zc.close.side_effect = TimeoutError("shutdown")
        mod = _make_zeroconf_module(mock_zc)
        with patch.dict("sys.modules", {"zeroconf": mod}):
            result = scan_mdns_network(timeout=0.01)
        assert result == {}
        mock_zc.close.assert_called_once()

    def test_results_keyed_by_ip(self) -> None:
        target_ip = "192.168.1.50"
        info = _make_info(target_ip, 631, "nas.local.")
        mock_zc = MagicMock()
        mock_zc.get_service_info.return_value = info
        captured: list[Any] = []

        def fake_browser(zc: Any, stype_: str, listener: Any) -> MagicMock:
            captured.append(listener)
            return MagicMock()

        mod = _make_zeroconf_module(mock_zc, browser_factory=fake_browser)

        def fire(self: threading.Event, timeout: float | None = None) -> bool:
            for lst in captured:
                lst.add_service(mock_zc, "_ipp._tcp.local.", "NAS._ipp._tcp.local.")
            return False

        with patch.dict("sys.modules", {"zeroconf": mod}):
            with patch.object(threading.Event, "wait", fire):
                result = scan_mdns_network(timeout=0.01)

        assert target_ip in result
        assert result[target_ip]["hostname"] == "nas.local"
