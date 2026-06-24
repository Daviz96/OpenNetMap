"""Tests for ARP/ping host discovery scanner (with mocks)."""

from unittest.mock import MagicMock, patch

from network_inventory.scanner.arp_scanner import (
    _arp_cache,
    _ping_host,
    reverse_dns,
    scan_subnet,
)

# --- reverse_dns ---


def test_reverse_dns_returns_hostname_on_success():
    with patch("socket.gethostbyaddr", return_value=("mydevice.local", [], [])):
        assert reverse_dns("10.0.0.1") == "mydevice.local"


def test_reverse_dns_returns_none_on_failure():
    with patch("socket.gethostbyaddr", side_effect=OSError):
        assert reverse_dns("10.0.0.1") is None


# --- _arp_cache ---


def test_arp_cache_parses_windows_output():
    sample = (
        "Interface: 192.168.1.100\n"
        "  10.0.0.1          aa-bb-cc-dd-ee-ff     dynamic\n"
        "  10.0.0.2          11-22-33-44-55-66     dynamic\n"
    )
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=sample)
        result = _arp_cache()
    assert result["10.0.0.1"] == "aa:bb:cc:dd:ee:ff"
    assert result["10.0.0.2"] == "11:22:33:44:55:66"


def test_arp_cache_returns_empty_on_subprocess_error():
    with patch("subprocess.run", side_effect=OSError):
        result = _arp_cache()
    assert result == {}


# --- _ping_host ---


def test_ping_host_returns_device_on_success():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = _ping_host("10.0.0.1", timeout=1.0)
    assert result is not None
    assert result.ip == "10.0.0.1"
    assert result.response_time_ms is not None


def test_ping_host_returns_none_on_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        result = _ping_host("10.0.0.1", timeout=1.0)
    assert result is None


def test_ping_host_returns_none_on_subprocess_error():
    with patch("subprocess.run", side_effect=OSError):
        result = _ping_host("10.0.0.1", timeout=1.0)
    assert result is None


# --- scan_subnet (scapy path mock) ---


def test_scan_subnet_uses_scapy_when_available():
    mock_received = MagicMock()
    mock_received.psrc = "10.0.0.1"
    mock_received.hwsrc = "aa:bb:cc:dd:ee:ff"

    with (
        patch(
            "network_inventory.scanner.arp_scanner._scan_with_scapy",
            return_value=[MagicMock(ip="10.0.0.1", mac="aa:bb:cc:dd:ee:ff")],
        ) as mock_scapy,
        patch(
            "network_inventory.scanner.arp_scanner._scan_with_ping",
            return_value=[],
        ) as mock_ping,
    ):
        devices = scan_subnet("10.0.0.0/30", threads=4, timeout=0.5)
        mock_scapy.assert_called_once()
        mock_ping.assert_not_called()
    assert len(devices) == 1


def test_scan_subnet_falls_back_to_ping_when_scapy_fails():
    with (
        patch(
            "network_inventory.scanner.arp_scanner._scan_with_scapy",
            return_value=[],
        ),
        patch(
            "network_inventory.scanner.arp_scanner._scan_with_ping",
            return_value=[MagicMock(ip="10.0.0.1")],
        ) as mock_ping,
    ):
        devices = scan_subnet("10.0.0.0/30", threads=4, timeout=0.5)
        mock_ping.assert_called_once()
    assert len(devices) == 1
