"""Tests for port-based security assessment."""

from network_inventory.inventory.device import Device
from network_inventory.security.assessment import assess_device


def _dev(ports: list[int] | None = None, snmp_community: str | None = None) -> Device:
    device = Device(ip="10.0.0.1", open_ports=ports or [])
    if snmp_community:
        device.snmp_info = {"community": snmp_community}
    return device


# --- Score massimo ---


def test_clean_device_scores_100():
    result = assess_device(_dev(ports=[22, 443]))
    assert result.score == 100
    assert result.findings == []
    assert result.recommendations == []


# --- Singoli finding ---


def test_telnet_open_deducts_20():
    result = assess_device(_dev(ports=[23]))
    assert result.score == 80
    assert any("Telnet" in f for f in result.findings)


def test_ftp_open_deducts_12():
    result = assess_device(_dev(ports=[21]))
    assert result.score == 88
    assert any("FTP" in f for f in result.findings)


def test_snmp_exposed_deducts_10():
    result = assess_device(_dev(ports=[161]))
    assert result.score == 90
    assert any("SNMP" in f for f in result.findings)


def test_http_without_https_deducts_8():
    result = assess_device(_dev(ports=[80]))
    assert result.score == 92
    assert any("HTTP" in f for f in result.findings)


def test_https_present_no_http_penalty():
    result = assess_device(_dev(ports=[80, 443]))
    assert result.score == 100


def test_rdp_exposed_deducts_15():
    result = assess_device(_dev(ports=[3389]))
    assert result.score == 85
    assert any("RDP" in f for f in result.findings)


def test_smb_exposed_deducts_8():
    result = assess_device(_dev(ports=[445]))
    assert result.score == 92
    assert any("SMB" in f for f in result.findings)


def test_snmp_default_community_public_deducts_20():
    result = assess_device(_dev(snmp_community="public"))
    assert result.score == 80
    assert any("Community" in f for f in result.findings)


def test_snmp_default_community_private_deducts_20():
    result = assess_device(_dev(snmp_community="private"))
    assert result.score == 80


# --- Score non scende sotto 0 ---


def test_score_is_nonnegative_with_all_findings():
    # max penalità: 20+12+10+8+15+8+20 = 93 → score minimo 7
    result = assess_device(
        _dev(ports=[21, 23, 80, 161, 445, 3389], snmp_community="public")
    )
    assert result.score >= 0
    assert result.score == 7


# --- Recommendations presenti per ogni finding ---


def test_recommendations_match_findings():
    result = assess_device(_dev(ports=[21, 23, 3389]))
    assert len(result.recommendations) == len(result.findings)


# --- Più finding insieme ---


def test_multiple_findings_accumulate():
    result = assess_device(_dev(ports=[23, 21]))
    assert result.score == 100 - 20 - 12
    assert len(result.findings) == 2
