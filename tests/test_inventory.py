import pytest

from network_inventory.inventory.device import Device
from network_inventory.inventory.inventory import (
    _mark_discovery,
    _validate_subnet_size,
    enrich_device_identity,
)


def test_device_to_dict_from_dict_roundtrip():
    device = Device(
        ip="10.0.0.1",
        mac="00:11:22:33:44:55",
        hostname="test-host",
        open_ports=[22, 80],
        services={"http": {"server": "Custom Device"}},
        sources={"ip": ["arp"]},
    )

    data = device.to_dict()
    loaded = Device.from_dict(data)

    assert loaded.ip == device.ip
    assert loaded.mac == device.mac
    assert loaded.hostname == device.hostname
    assert loaded.open_ports == [22, 80]
    assert loaded.services == device.services
    assert loaded.sources == device.sources


def test_device_from_dict_coerces_values_and_defaults():
    data = {
        "ip": "192.168.1.10",
        "open_ports": ["22", "443"],
        "confidence": {"classification": "0.82"},
        "sources": {"mac": ["arp_cache_or_arp_scan"]},
    }

    device = Device.from_dict(data)

    assert device.ip == "192.168.1.10"
    assert device.open_ports == [22, 443]
    assert device.confidence["classification"] == 0.82
    assert device.sources == {"mac": ["arp_cache_or_arp_scan"]}


def test_mark_discovery_defaults_to_unknown_when_no_device_info():
    device = Device(ip="10.1.1.1")

    _mark_discovery(device)

    assert device.discovery_methods == ["unknown"]
    assert device.discovery_confidence == 0.35
    assert device.sources["ip"] == ["unknown"]
    assert "mac" not in device.sources


def test_mark_discovery_builds_expected_sources_and_confidence():
    device = Device(
        ip="10.1.1.2",
        mac="aa:bb:cc:dd:ee:ff",
        hostname="device.local",
        response_time_ms=12.5,
    )

    _mark_discovery(device)

    assert set(device.discovery_methods) == {"arp", "icmp", "reverse_dns"}
    assert device.discovery_confidence == 0.95
    assert device.sources["ip"] == ["arp", "icmp", "reverse_dns"]
    assert device.sources["mac"] == ["arp_cache_or_arp_scan"]
    assert device.sources["hostname"] == ["reverse_dns"]


def test_validate_subnet_size_accepts_ipv4_small():
    _validate_subnet_size("192.168.0.0/24")


def test_validate_subnet_size_rejects_too_large_subnet():
    with pytest.raises(ValueError, match="Subnet too large"):
        _validate_subnet_size("10.0.0.0/19")


def test_validate_subnet_size_rejects_ipv6():
    with pytest.raises(ValueError, match="Only IPv4 subnets"):
        _validate_subnet_size("2001:db8::/64")


def test_enrich_device_identity_infers_model_from_http_service():
    device = Device(
        ip="10.0.0.2",
        vendor="Ubiquiti",
        services={"http": {"site": {"server": "UniFi Controller"}}},
    )

    enrich_device_identity(device)

    assert device.manufacturer == "UniFi"
    assert device.model == "UniFi Controller"
