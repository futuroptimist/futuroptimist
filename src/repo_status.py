"""Update README with repo status emojis.

Fetches the latest GitHub Actions run for each repo listed in the README's
"Related Projects" section and prepends a green check, red cross, or question
mark depending on whether the most recent workflow run on the default branch
completed successfully, failed, or hasn't completed.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from datetime import datetime, timezone

import requests

GITHUB_RE = re.compile(r"https://github.com/([\w-]+)/([\w.-]+)(?:/tree/([\w./-]+))?")


def status_to_emoji(conclusion: str | None) -> str:
    """Return an emoji representing the run conclusion.

    Comparison is case-insensitive and ignores surrounding whitespace so
    callers may pass values like ``"SUCCESS"`` or ``" failure \n"`` and
    receive the same result.

    - ``"success"`` → ✅
    - ``"failure"``, ``"cancelled"``, ``"canceled"``, ``"timed_out"``,
      ``"startup_failure"`` → ❌
    - anything else (including ``None``) → ❓
    """
    if conclusion:
        normalized = conclusion.strip().lower().replace("-", "_").replace(" ", "_")
    else:
        normalized = ""
    if normalized == "success":
        return "✅"
    if normalized in {
        "failure",
        "cancelled",
        "canceled",
        "timed_out",
        "startup_failure",
    }:
        return "❌"
    return "❓"


def fetch_repo_status(
    repo: str,
    token: str | None = None,
    branch: str | None = None,
    attempts: int = 2,
) -> str:
    """Fetch the latest workflow run conclusion for ``repo`` and return an emoji.

    The GitHub API occasionally returns inconsistent data if a workflow is
    updating while we query it. To catch this non-determinism we fetch the
    status multiple times and ensure all results match. If they differ we raise
    ``RuntimeError`` so the calling workflow fails loudly.
    """
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if branch is None:
        repo_resp = requests.get(
            f"https://api.github.com/repos/{repo}", headers=headers, timeout=10
        )
        repo_resp.raise_for_status()
        branch = repo_resp.json().get("default_branch")

    url = (
        "https://api.github.com/repos/{repo}/actions/runs?per_page=1&status=completed&event=push"
    ).format(repo=repo)
    if branch:
        url += f"&branch={branch}"

    def _fetch() -> str | None:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])
        return runs[0].get("conclusion") if runs else None

    conclusions = [_fetch() for _ in range(attempts)]
    if len(set(conclusions)) > 1:
        raise RuntimeError(
            f"Non-deterministic workflow conclusion for {repo}: {conclusions}"
        )
    return status_to_emoji(conclusions[0])


def update_readme(
    readme_path: Path,
    token: str | None = None,
    now: datetime | None = None,
) -> None:
    """Update README with status emojis and a timestamp."""
    lines = readme_path.read_text().splitlines()
    in_section = False
    if now is None:
        now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")
    for i, line in enumerate(lines):
        if line.strip() == "## Related Projects":
            in_section = True
            ts_line = f"_Last updated: {timestamp}; checks hourly_"
            if i + 1 < len(lines) and lines[i + 1].startswith("_Last updated:"):
                lines[i + 1] = ts_line
            else:
                lines.insert(i + 1, ts_line)
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.startswith("- "):
            match = GITHUB_RE.search(line)
            if match:
                repo = f"{match.group(1)}/{match.group(2)}"
                branch = match.group(3)
                emoji = fetch_repo_status(repo, token, branch)
                # remove existing emoji
                lines[i] = re.sub(r"^(-\s*)(?:[✅❌❓]\s*)*", r"\1", line)
                lines[i] = f"- {emoji} {lines[i][2:].lstrip()}"
    readme_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":  # pragma: no cover
    token = os.environ.get("GITHUB_TOKEN")
    update_readme(Path(__file__).resolve().parent.parent / "README.md", token)
