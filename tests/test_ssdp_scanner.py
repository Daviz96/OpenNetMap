"""Tests for the SSDP/UPnP scanner."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from network_inventory.scanner.ssdp_scanner import _parse_response, scan_ssdp

_SAMPLE_RESPONSE = (
    "HTTP/1.1 200 OK\r\n"
    "CACHE-CONTROL: max-age=1800\r\n"
    "ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n"
    "USN: uuid:abc123::urn:schemas-upnp-org:device:MediaRenderer:1\r\n"
    "LOCATION: http://192.168.1.5:49152/description.xml\r\n"
    "SERVER: Linux/5.4 UPnP/1.1 MiniUPnPd/2.1\r\n"
    "\r\n"
)


class TestParseResponse:
    def test_parses_server(self) -> None:
        parsed = _parse_response(_SAMPLE_RESPONSE)
        assert "linux" in parsed.get("server", "").lower()

    def test_parses_location(self) -> None:
        parsed = _parse_response(_SAMPLE_RESPONSE)
        assert "192.168.1.5" in parsed.get("location", "")

    def test_parses_st(self) -> None:
        parsed = _parse_response(_SAMPLE_RESPONSE)
        assert "MediaRenderer" in parsed.get("st", "")

    def test_empty_response(self) -> None:
        assert _parse_response("") == {}

    def test_ignores_lines_without_colon(self) -> None:
        raw = "HTTP/1.1 200 OK\r\nNO_COLON_HERE\r\nST: ssdp:all\r\n"
        parsed = _parse_response(raw)
        assert parsed.get("st") == "ssdp:all"


class TestScanSsdp:
    def test_returns_empty_on_socket_error(self) -> None:
        with patch("network_inventory.scanner.ssdp_scanner.socket.socket") as MockSock:
            MockSock.return_value.__enter__ = MagicMock()
            instance = MagicMock()
            instance.sendto.side_effect = OSError("no network")
            MockSock.return_value = instance
            result = scan_ssdp("192.168.1.5")
        assert result == {}

    def test_returns_empty_when_no_response_from_ip(self) -> None:
        other_ip = "192.168.1.99"
        target_ip = "192.168.1.5"
        response = _SAMPLE_RESPONSE.encode()

        with patch("network_inventory.scanner.ssdp_scanner.socket.socket") as MockSock:
            instance = MagicMock()
            MockSock.return_value = instance
            instance.recvfrom.side_effect = [
                (response, (other_ip, 1900)),
                TimeoutError(),
            ]
            result = scan_ssdp(target_ip, timeout=0.01)

        assert result == {}

    def test_returns_info_for_matching_ip(self) -> None:
        target_ip = "192.168.1.5"
        response = _SAMPLE_RESPONSE.encode()

        with patch("network_inventory.scanner.ssdp_scanner.socket.socket") as MockSock:
            instance = MagicMock()
            MockSock.return_value = instance
            instance.recvfrom.side_effect = [
                (response, (target_ip, 1900)),
                TimeoutError(),
            ]
            result = scan_ssdp(target_ip, timeout=0.01)

        assert "server" in result
        assert "linux" in str(result["server"]).lower()
        assert "location" in result

    def test_collects_multiple_service_types(self) -> None:
        target_ip = "192.168.1.5"
        resp1 = _SAMPLE_RESPONSE.encode()
        resp2 = (
            b"HTTP/1.1 200 OK\r\n"
            b"ST: upnp:rootdevice\r\n"
            b"SERVER: Linux/5.4 UPnP/1.1\r\n"
            b"LOCATION: http://192.168.1.5:49152/description.xml\r\n"
            b"\r\n"
        )

        with patch("network_inventory.scanner.ssdp_scanner.socket.socket") as MockSock:
            instance = MagicMock()
            MockSock.return_value = instance
            instance.recvfrom.side_effect = [
                (resp1, (target_ip, 1900)),
                (resp2, (target_ip, 1900)),
                TimeoutError(),
            ]
            result = scan_ssdp(target_ip, timeout=0.01)

        services = result.get("services", [])
        assert isinstance(services, list)
        assert len(services) == 2
