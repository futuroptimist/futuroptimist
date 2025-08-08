"""Update README with repo status emojis.

Fetches the latest GitHub Actions run for each repo listed in the README's
"Related Projects" section and prepends a green check or red cross depending on
whether the most recent workflow run on the default branch succeeded.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import requests

GITHUB_RE = re.compile(r"https://github.com/([\w-]+)/([\w.-]+)")


def status_to_emoji(conclusion: str | None) -> str:
    """Return an emoji representing the run conclusion.

    Parameters
    ----------
    conclusion:
        The `conclusion` field from a workflow run, e.g. ``"success"`` or
        ``"failure"``. ``None`` indicates no runs or an in-progress run.
    """

    return "✅" if conclusion == "success" else "❌"


def fetch_repo_status(repo: str, token: str | None = None) -> str:
    """Fetch the latest workflow run conclusion for ``repo`` and return an emoji."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=1"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    runs = resp.json().get("workflow_runs", [])
    conclusion = runs[0].get("conclusion") if runs else None
    return status_to_emoji(conclusion)


def update_readme(readme_path: Path, token: str | None = None) -> None:
    """Update README with status emojis for related project repos."""
    lines = readme_path.read_text().splitlines()
    in_section = False
    for i, line in enumerate(lines):
        if line.strip() == "## Related Projects":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.startswith("- "):
            match = GITHUB_RE.search(line)
            if match:
                repo = f"{match.group(1)}/{match.group(2)}"
                emoji = fetch_repo_status(repo, token)
                # remove existing emoji
                lines[i] = re.sub(r"^(-\s*)(?:✅|❌)?\s*", r"\1", line)
                lines[i] = f"- {emoji} {lines[i][2:].lstrip()}"
    readme_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    token = os.environ.get("GITHUB_TOKEN")
    update_readme(Path(__file__).resolve().parent.parent / "README.md", token)
