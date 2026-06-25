from network_inventory.templating import render, security_class


def test_security_class_thresholds():
    assert security_class(100) == "sec-good"
    assert security_class(80) == "sec-good"
    assert security_class(79) == "sec-warn"
    assert security_class(50) == "sec-warn"
    assert security_class(49) == "sec-bad"
    assert security_class(0) == "sec-bad"


def test_security_class_non_numeric():
    assert security_class(None) == "sec-unknown"
    assert security_class("n/a") == "sec-unknown"


def test_render_dashboard_template_minimal():
    html = render(
        "dashboard.html",
        subtitle="Subnet 10.0.0.0/24",
        stats={"utilization_percent": 12},
        events=[],
        risky_devices=[],
        counts={"devices": 0, "scans": 0, "events": 0},
        jobs=[],
        history=[],
    )
    assert "<!doctype html>" in html.lower()
    assert "OpenNetMap" in html
    # Senza history non deve includere lo script del grafico.
    assert "chart.min.js" not in html


def test_render_dashboard_includes_chart_with_history():
    html = render(
        "dashboard.html",
        subtitle="",
        stats={},
        events=[],
        risky_devices=[],
        counts={"devices": 1, "scans": 1, "events": 0},
        jobs=[],
        history=[{"scan_id": 1, "label": "2026-06-25", "count": 3}],
    )
    assert "/static/chart.min.js" in html
    assert "historyChart" in html
