"""Event generation by comparing inventory snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from network_inventory.inventory.device import Device


@dataclass(slots=True)
class InventoryEvent:
    """Represents a detected inventory change."""

    event_type: str
    device_key: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat())


def compare_snapshots(previous: list[Device], current: list[Device]) -> list[InventoryEvent]:
    """Generate events by comparing two device snapshots."""
    previous_by_key = {_device_key(device): device for device in previous}
    current_by_key = {_device_key(device): device for device in current}
    previous_by_mac = {device.mac: device for device in previous if device.mac}
    events: list[InventoryEvent] = []

    for key, device in current_by_key.items():
        old = previous_by_key.get(key)
        if old is None:
            events.append(InventoryEvent("NEW_DEVICE", key, f"Nuovo dispositivo rilevato: {device.ip}"))
            old_by_mac = previous_by_mac.get(device.mac) if device.mac else None
            if old_by_mac and old_by_mac.ip != device.ip:
                events.append(InventoryEvent("IP_CHANGED", key, f"IP cambiato per {device.mac}: {old_by_mac.ip} -> {device.ip}"))
            continue
        events.extend(_compare_device(old, device, key))

    for key, device in previous_by_key.items():
        if key not in current_by_key:
            events.append(InventoryEvent("DEVICE_OFFLINE", key, f"Dispositivo non piu rilevato: {device.ip}"))

    return events


def _compare_device(old: Device, new: Device, key: str) -> list[InventoryEvent]:
    events: list[InventoryEvent] = []
    old_ports = set(old.open_ports)
    new_ports = set(new.open_ports)
    for port in sorted(new_ports - old_ports):
        events.append(InventoryEvent("PORT_OPENED", key, f"Porta aperta su {new.ip}: {port}"))
    for port in sorted(old_ports - new_ports):
        events.append(InventoryEvent("PORT_CLOSED", key, f"Porta chiusa su {new.ip}: {port}"))
    if old.hostname != new.hostname:
        events.append(InventoryEvent("HOSTNAME_CHANGED", key, f"Hostname cambiato: {old.hostname} -> {new.hostname}"))
    if old.vendor != new.vendor:
        events.append(InventoryEvent("VENDOR_CHANGED", key, f"Vendor cambiato: {old.vendor} -> {new.vendor}"))
    if old.device_type != new.device_type:
        events.append(
            InventoryEvent("CLASSIFICATION_CHANGED", key, f"Classificazione cambiata: {old.device_type} -> {new.device_type}")
        )
    if old.security_score != new.security_score:
        events.append(
            InventoryEvent("SECURITY_SCORE_CHANGED", key, f"Security score cambiato: {old.security_score} -> {new.security_score}")
        )
    if old.ip != new.ip:
        events.append(InventoryEvent("IP_CHANGED", key, f"IP cambiato: {old.ip} -> {new.ip}"))
    return events


def _device_key(device: Device) -> str:
    return f"{device.mac or 'no-mac'}|{device.ip}"
