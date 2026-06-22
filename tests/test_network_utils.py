from network_inventory.utils.network import subnet_stats


def test_subnet_stats_computes_utilization_for_ipv4():
    stats = subnet_stats("192.168.1.0/29", active_hosts=3)

    assert stats["subnet"] == "192.168.1.0/29"
    assert stats["total_hosts"] == 6
    assert stats["active_hosts"] == 3
    assert stats["free_hosts"] == 3
    assert stats["utilization_percent"] == 50.0


def test_subnet_stats_handles_zero_active_hosts():
    stats = subnet_stats("10.0.0.0/30", active_hosts=0)

    assert stats["total_hosts"] == 2
    assert stats["free_hosts"] == 2
    assert stats["utilization_percent"] == 0.0
