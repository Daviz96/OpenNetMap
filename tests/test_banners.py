"""Tests for banner collection and signature matching."""

from __future__ import annotations

from network_inventory.fingerprint.banners import match_banner


class TestMatchBanner:
    def test_matches_openssh(self) -> None:
        result = match_banner("SSH-2.0-OpenSSH_9.3")
        assert result is not None
        assert result["vendor"] == "OpenBSD"
        assert result["product"] == "OpenSSH"
        assert result.get("version") == "9.3"

    def test_matches_dropbear(self) -> None:
        result = match_banner("SSH-2.0-Dropbear_2022.83")
        assert result is not None
        assert result["device_type"] == "router"

    def test_matches_mikrotik_ssh(self) -> None:
        result = match_banner("SSH-2.0-RouterOS_7.10")
        assert result is not None
        assert result["vendor"] == "MikroTik"

    def test_matches_apache(self) -> None:
        result = match_banner("Apache/2.4.57 (Ubuntu)")
        assert result is not None
        assert result["vendor"] == "Apache"
        assert result.get("version") == "2.4"

    def test_matches_nginx(self) -> None:
        result = match_banner("nginx/1.24.0")
        assert result is not None
        assert result["product"] == "nginx"

    def test_matches_vsftpd(self) -> None:
        result = match_banner("220 (vsFTPd 3.0.5)")
        assert result is not None
        assert result["product"] == "vsftpd"
        assert result.get("version") == "3.0"

    def test_matches_postfix(self) -> None:
        result = match_banner("220 mail.example.com ESMTP Postfix")
        assert result is not None
        assert result["vendor"] == "Postfix"

    def test_matches_tp_link(self) -> None:
        result = match_banner("TP-LINK TL-WR841N")
        assert result is not None
        assert result["device_type"] == "router"

    def test_no_match_for_unknown_banner(self) -> None:
        result = match_banner("220 Unknown Server v1.0")
        assert result is None

    def test_empty_banner_returns_none(self) -> None:
        assert match_banner("") is None

    def test_case_insensitive_match(self) -> None:
        result = match_banner("server: mikrotik routeros")
        assert result is not None
        assert result["vendor"] == "MikroTik"

    def test_matches_synology(self) -> None:
        result = match_banner("DSM Synology DiskStation")
        assert result is not None
        assert result["device_type"] == "nas"
