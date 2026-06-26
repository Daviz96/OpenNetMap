from network_inventory.inventory.device import Device
from network_inventory.scanner.snmp_topology import FdbEntry, SwitchTopology
from network_inventory.topology.correlation import access_links, correlate_physical

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
