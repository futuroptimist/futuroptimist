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

    Accepts any object; non-string inputs fall back to ``"❓"``. Comparison is
    case-insensitive, normalizes internal whitespace and hyphens to underscores,
    and ignores surrounding whitespace so callers may pass values like
    ``"SUCCESS"``, ``" failure \n"``, or ``"TIMED\tOUT"`` and receive the same
    result.

    - ``"success"`` → ✅
    - ``"failure"``, ``"cancelled"``, ``"canceled"``, ``"timed_out"``,
      ``"startup_failure"``, ``"action_required"`` → ❌
    - anything else (including ``None`` or non-strings) → ❓
    """
    if not isinstance(conclusion, str) or not conclusion:
        normalized = ""
    else:
        normalized = re.sub(r"[\s-]+", "_", conclusion.strip().lower())
    if normalized == "success":
        return "✅"
    if normalized in {
        "failure",
        "cancelled",
        "canceled",
        "timed_out",
        "startup_failure",
        "action_required",
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

    # Determine the latest commit on the branch so we can filter workflow runs
    commit_resp = requests.get(
        f"https://api.github.com/repos/{repo}/commits/{branch}",
        headers=headers,
        timeout=10,
    )
    commit_resp.raise_for_status()
    sha = commit_resp.json().get("sha")

    url = (
        "https://api.github.com/repos/{repo}/actions/runs?per_page=100&status=completed&event=push"
    ).format(repo=repo)
    if branch:
        url += f"&branch={branch}"

    keywords = re.compile(r"(test|lint|build|ci)", re.I)
    failures = {
        "failure",
        "cancelled",
        "canceled",
        "timed_out",
        "startup_failure",
        "action_required",
    }

    def _fetch() -> str | None:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        runs = [
            r for r in resp.json().get("workflow_runs", []) if r.get("head_sha") == sha
        ]
        if not runs:
            return None
        # Prefer workflow runs whose names indicate CI relevance
        important = [r for r in runs if keywords.search(r.get("name", ""))]
        if important:
            runs = important
        conclusions = {r.get("conclusion") for r in runs}
        if any(c in failures for c in conclusions):
            return "failure"
        if conclusions == {"success"}:
            return "success"
        return None

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
    lines = readme_path.read_text(encoding="utf-8").splitlines()
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
                # Ensure UTF-8 output; lines later written with utf-8 encoding
                lines[i] = f"- {emoji} {lines[i][2:].lstrip()}"
    # Ensure output file encoded as UTF-8 so emoji render correctly on Windows
    readme_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    token = os.environ.get("GITHUB_TOKEN")
    update_readme(Path(__file__).resolve().parent.parent / "README.md", token)
