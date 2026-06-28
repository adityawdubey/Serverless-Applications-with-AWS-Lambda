from pathlib import Path

SNIPPETS = Path(__file__).resolve().parents[1] / "scripts" / "api.http"


def test_api_http_has_both_calls():
    text = SNIPPETS.read_text(encoding="utf-8")
    assert "POST" in text and "/orders" in text
    assert "GET" in text
    assert "curl" in text
