"""Tests for the snapshot comparison event engine."""

from network_inventory.events.engine import compare_snapshots
from network_inventory.inventory.device import Device


def _dev(ip: str, mac: str = "aa:bb:cc:dd:ee:ff", **kwargs) -> Device:
    return Device(ip=ip, mac=mac, **kwargs)


def _event_types(events: list) -> list[str]:
    return [e.event_type for e in events]


# --- NEW_DEVICE ---


def test_new_device_event_when_host_appears():
    prev: list[Device] = []
    curr = [_dev("10.0.0.1")]
    events = compare_snapshots(prev, curr)
    assert "NEW_DEVICE" in _event_types(events)
    assert events[0].device_key == "aa:bb:cc:dd:ee:ff|10.0.0.1"


# --- DEVICE_OFFLINE ---


def test_device_offline_event_when_host_disappears():
    prev = [_dev("10.0.0.1")]
    curr: list[Device] = []
    events = compare_snapshots(prev, curr)
    assert "DEVICE_OFFLINE" in _event_types(events)


# --- PORT_OPENED ---


def test_port_opened_event():
    prev = [_dev("10.0.0.1", open_ports=[22])]
    curr = [_dev("10.0.0.1", open_ports=[22, 80])]
    events = compare_snapshots(prev, curr)
    assert "PORT_OPENED" in _event_types(events)
    port_event = next(e for e in events if e.event_type == "PORT_OPENED")
    assert "80" in port_event.message


# --- PORT_CLOSED ---


def test_port_closed_event():
    prev = [_dev("10.0.0.1", open_ports=[22, 23])]
    curr = [_dev("10.0.0.1", open_ports=[22])]
    events = compare_snapshots(prev, curr)
    assert "PORT_CLOSED" in _event_types(events)
    port_event = next(e for e in events if e.event_type == "PORT_CLOSED")
    assert "23" in port_event.message


# --- HOSTNAME_CHANGED ---


def test_hostname_changed_event():
    prev = [_dev("10.0.0.1", hostname="old-host")]
    curr = [_dev("10.0.0.1", hostname="new-host")]
    events = compare_snapshots(prev, curr)
    assert "HOSTNAME_CHANGED" in _event_types(events)


def test_no_hostname_event_when_unchanged():
    prev = [_dev("10.0.0.1", hostname="same")]
    curr = [_dev("10.0.0.1", hostname="same")]
    events = compare_snapshots(prev, curr)
    assert "HOSTNAME_CHANGED" not in _event_types(events)


# --- VENDOR_CHANGED ---


def test_vendor_changed_event():
    prev = [_dev("10.0.0.1", vendor="Cisco")]
    curr = [_dev("10.0.0.1", vendor="Ubiquiti")]
    events = compare_snapshots(prev, curr)
    assert "VENDOR_CHANGED" in _event_types(events)


# --- CLASSIFICATION_CHANGED ---


def test_classification_changed_event():
    prev = [_dev("10.0.0.1", device_type="Router")]
    curr = [_dev("10.0.0.1", device_type="Switch")]
    events = compare_snapshots(prev, curr)
    assert "CLASSIFICATION_CHANGED" in _event_types(events)


# --- SECURITY_SCORE_CHANGED ---


def test_security_score_changed_event():
    prev = [_dev("10.0.0.1", security_score=100)]
    curr = [_dev("10.0.0.1", security_score=60)]
    events = compare_snapshots(prev, curr)
    assert "SECURITY_SCORE_CHANGED" in _event_types(events)


def test_no_security_event_when_score_unchanged():
    prev = [_dev("10.0.0.1", security_score=80)]
    curr = [_dev("10.0.0.1", security_score=80)]
    events = compare_snapshots(prev, curr)
    assert "SECURITY_SCORE_CHANGED" not in _event_types(events)


# --- IP_CHANGED (stesso MAC, IP diverso) ---


def test_ip_changed_event_when_mac_reappears_with_new_ip():
    mac = "aa:bb:cc:dd:ee:01"
    prev = [_dev("10.0.0.1", mac=mac)]
    curr = [_dev("10.0.0.99", mac=mac)]
    events = compare_snapshots(prev, curr)
    types = _event_types(events)
    assert "NEW_DEVICE" in types
    assert "IP_CHANGED" in types


# --- Snapshot senza modifiche ---


def test_no_events_when_snapshots_identical():
    devices = [_dev("10.0.0.1", open_ports=[22], hostname="host", security_score=100)]
    events = compare_snapshots(devices, devices)
    assert events == []


# --- Evento con timestamp ---


def test_event_has_timestamp():
    events = compare_snapshots([], [_dev("10.0.0.1")])
    assert events[0].timestamp != ""
