from network_inventory.scanner.snmp_topology import (
    FdbEntry,
    SwitchTopology,
    _format_mac,
)


def test_format_mac():
    assert (
        _format_mac(bytes([0x00, 0x07, 0x4D, 0xB2, 0x92, 0xA9])) == "00:07:4d:b2:92:a9"
    )


def test_macs_per_port_groups_by_port_name():
    topo = SwitchTopology(
        host="10.0.0.1",
        fdb=[
            FdbEntry(mac="aa:aa:aa:aa:aa:01", vlan=1, bridge_port=2, if_name="Gi2"),
            FdbEntry(mac="aa:aa:aa:aa:aa:02", vlan=1, bridge_port=11, if_name="Gi11"),
            FdbEntry(mac="aa:aa:aa:aa:aa:03", vlan=1, bridge_port=11, if_name="Gi11"),
        ],
    )
    per_port = topo.macs_per_port()
    assert per_port["Gi2"] == ["aa:aa:aa:aa:aa:01"]
    assert len(per_port["Gi11"]) == 2  # porta con più MAC = uplink/downstream


def test_macs_per_port_falls_back_to_bridge_port():
    topo = SwitchTopology(
        host="10.0.0.1",
        fdb=[FdbEntry(mac="bb:bb:bb:bb:bb:01", vlan=1, bridge_port=5, if_name=None)],
    )
    assert "port-5" in topo.macs_per_port()
