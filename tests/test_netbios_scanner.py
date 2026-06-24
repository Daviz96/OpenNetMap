"""Tests for the cross-platform NetBIOS scanner."""

from __future__ import annotations

from unittest.mock import patch

from network_inventory.scanner.netbios_scanner import (
    _parse_nbtstat,
    _parse_nmblookup,
    scan_netbios,
)

NBTSTAT_OUTPUT = """\
               NetBIOS Remote Machine Name Table

       Name               Type         Status
    ---------------------------------------------
    MYPC           <00>  UNIQUE      Registered
    WORKGROUP      <00>  GROUP       Registered
    MYPC           <20>  UNIQUE      Registered
"""

NMBLOOKUP_OUTPUT = """\
Looking up status of 192.168.1.10
\tMYPC            <00> -         <ACTIVE>
\tWORKGROUP       <00> - <GROUP> <ACTIVE>
"""


class TestParseNbtstat:
    def test_extracts_unique_name(self) -> None:
        result = _parse_nbtstat(NBTSTAT_OUTPUT)
        assert "MYPC" in result["names"]  # type: ignore[operator]

    def test_extracts_workgroup(self) -> None:
        result = _parse_nbtstat(NBTSTAT_OUTPUT)
        assert result["workgroup"] == "WORKGROUP"

    def test_empty_output(self) -> None:
        result = _parse_nbtstat("")
        assert result["names"] == []
        assert result["workgroup"] is None


class TestParseNmblookup:
    def test_extracts_unique_name(self) -> None:
        result = _parse_nmblookup(NMBLOOKUP_OUTPUT)
        assert "MYPC" in result["names"]  # type: ignore[operator]

    def test_extracts_workgroup(self) -> None:
        result = _parse_nmblookup(NMBLOOKUP_OUTPUT)
        assert result["workgroup"] == "WORKGROUP"

    def test_empty_output(self) -> None:
        result = _parse_nmblookup("")
        assert result["names"] == []
        assert result["workgroup"] is None


class TestScanNetbios:
    def test_uses_nbtstat_when_available(self) -> None:
        with patch("network_inventory.scanner.netbios_scanner._run") as mock_run:
            mock_run.side_effect = [NBTSTAT_OUTPUT, None]
            result = scan_netbios("192.168.1.10")
        assert "MYPC" in result["names"]  # type: ignore[operator]
        assert mock_run.call_count == 1

    def test_falls_back_to_nmblookup(self) -> None:
        with patch("network_inventory.scanner.netbios_scanner._run") as mock_run:
            mock_run.side_effect = [None, NMBLOOKUP_OUTPUT]
            result = scan_netbios("192.168.1.10")
        assert "MYPC" in result["names"]  # type: ignore[operator]
        assert mock_run.call_count == 2

    def test_returns_empty_when_both_unavailable(self) -> None:
        with patch("network_inventory.scanner.netbios_scanner._run") as mock_run:
            mock_run.return_value = None
            result = scan_netbios("192.168.1.10")
        assert result == {}

    def test_nbtstat_nonzero_triggers_fallback(self) -> None:
        with patch("network_inventory.scanner.netbios_scanner._run") as mock_run:
            mock_run.side_effect = [None, NMBLOOKUP_OUTPUT]
            result = scan_netbios("192.168.1.10")
        assert result.get("workgroup") == "WORKGROUP"
