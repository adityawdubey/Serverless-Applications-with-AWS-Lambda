from pathlib import Path

HTML = Path(__file__).resolve().parents[2] / "web" / "index.html"


def test_frontend_contains_required_markers():
    text = HTML.read_text(encoding="utf-8")
    # Single configurable API base.
    assert "const API_BASE" in text
    # Both routes are called.
    assert "/orders" in text
    assert "fetch(" in text
    # Branding and sample items from the spec/mockup.
    assert "Order service" in text
    assert "Serverless" in text
    for sample in ("Margherita pizza", "Cold coffee", "Paneer wrap"):
        assert sample in text
    # Panels labelled by route.
    assert "POST /orders" in text
    assert "GET /orders" in text
