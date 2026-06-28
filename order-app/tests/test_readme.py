from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"


def test_readme_has_required_sections():
    text = README.read_text(encoding="utf-8").lower()
    for marker in (
        "order service",
        "cdk bootstrap",
        "cdk deploy",
        "cdk destroy",
        "api_base",
        "http.server",
        "cors",
        "scan",
    ):
        assert marker in text, marker
