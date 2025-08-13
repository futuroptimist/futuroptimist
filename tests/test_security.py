"""Security checks."""

from pathlib import Path

import pytest

from src.http import urlopen_http


def test_security_badges_present() -> None:
    readme = Path("README.md").read_text().lower()
    assert "dependabot" in readme
    assert "codeql" in readme
    assert "secret scanning" in readme


def test_urlopen_http_rejects_file_scheme(tmp_path: Path) -> None:
    file_url = f"file://{tmp_path}/x.txt"
    with pytest.raises(ValueError):
        urlopen_http(file_url)
