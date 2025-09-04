from pathlib import Path


def test_checks_script_has_trailing_newline():
    data = Path("scripts/checks.sh").read_bytes()
    assert data.endswith(b"\n"), "checks.sh should end with a newline"


def test_checks_script_handles_missing_npm():
    text = Path("scripts/checks.sh").read_text()
    assert "command -v npm >/dev/null 2>&1" in text
    assert "package.json not found or npm missing" in text

