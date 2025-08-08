from __future__ import annotations

from pathlib import Path
import re
import requests


def _related_projects_section() -> str:
    readme = Path("README.md").read_text(encoding="utf-8")
    match = re.search(r"## Related Projects\n(?P<section>.*?)(\n## |\Z)", readme, re.S)
    assert match, "Related Projects section missing"
    return match.group("section")


def test_related_project_links_match_status() -> None:
    section = _related_projects_section()
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        status = "✅" if "✅" in line else "❌" if "❌" in line else None
        github_links = re.findall(r"https://github.com/[^)\s]+", line)
        if not github_links:
            continue
        url = github_links[0]
        try:
            resp = requests.head(url, timeout=5)
            exists = resp.status_code < 400
        except requests.RequestException:
            exists = False
        assert status is not None, f"Missing status for {url}"
        assert (status == "✅") == exists, f"{url} status {status} mismatch"
