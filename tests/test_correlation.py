from network_inventory.inventory.device import Device
from network_inventory.scanner.snmp_topology import FdbEntry, SwitchTopology
from network_inventory.topology.correlation import (
    access_links,
    correlate_physical,
    select_snmp_targets,
)

MAC = "00:07:4d:b2:92:a9"


def _switch(host: str, name: str, entries: list[FdbEntry]) -> SwitchTopology:
    return SwitchTopology(host=host, sys_name=name, fdb=entries)


def test_mac_attributed_to_fewest_companions_port():
    # Core: il MAC è su una porta con tanti altri (uplink).
    core = _switch(
        "10.0.0.1",
        "CORE",
        [
            FdbEntry(mac=MAC, vlan=1, bridge_port=1, if_name="Gi1"),
            FdbEntry(mac="aa:aa:aa:aa:aa:01", vlan=1, bridge_port=1, if_name="Gi1"),
            FdbEntry(mac="aa:aa:aa:aa:aa:02", vlan=1, bridge_port=1, if_name="Gi1"),
        ],
    )
    # Access: il MAC è da solo su una porta (endpoint diretto).
    access = _switch(
        "10.0.0.2",
        "ACCESS",
        [FdbEntry(mac=MAC, vlan=1, bridge_port=5, if_name="Gi5")],
    )
    devices = [Device(ip="192.168.1.50", mac=MAC, hostname="printer")]

    links = correlate_physical([core, access], devices)
    by_mac = {link.mac: link for link in links}

    link = by_mac[MAC.lower()]
    assert link.switch_host == "10.0.0.2"  # access, non core
    assert link.port == "Gi5"
    assert link.companions == 1
    assert link.device_label == "printer"
    assert link.device_ip == "192.168.1.50"


def test_access_links_filter():
    access = _switch(
        "10.0.0.2",
        "ACCESS",
        [
            FdbEntry(mac=MAC, vlan=1, bridge_port=5, if_name="Gi5"),
            FdbEntry(mac="bb:bb:bb:bb:bb:01", vlan=1, bridge_port=6, if_name="Gi6"),
            FdbEntry(mac="bb:bb:bb:bb:bb:02", vlan=1, bridge_port=6, if_name="Gi6"),
        ],
    )
    links = correlate_physical([access], [])
    direct = access_links(links, max_companions=1)
    ports = {link.port for link in direct}
    assert ports == {"Gi5"}  # solo la porta con 1 MAC


def test_select_snmp_targets_auto_and_explicit():
    switch = Device(
        ip="10.0.0.1", mac="aa:bb:cc:00:00:01", device_type="Switch", open_ports=[161]
    )
    pc = Device(
        ip="10.0.0.50", mac="aa:bb:cc:00:00:50", device_type="host", open_ports=[445]
    )
    printer = Device(
        ip="10.0.0.60",
        mac="aa:bb:cc:00:00:60",
        device_type="Stampante",
        open_ports=[161],
    )
    targets = select_snmp_targets([switch, pc, printer], ["10.0.0.99"])

    assert "10.0.0.99" in targets  # esplicito
    assert "10.0.0.1" in targets  # auto: switch con 161
    assert "10.0.0.50" not in targets  # host senza 161
    assert "10.0.0.60" not in targets  # stampante con 161 ma non apparato di rete
