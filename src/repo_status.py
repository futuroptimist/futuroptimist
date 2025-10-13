"""Update README with repo status emojis.

Fetches the latest GitHub Actions run for each repo listed in the README's
"Related Projects" section and prepends a green check, red cross, or question
mark depending on whether the most recent workflow run on the default branch
completed successfully, failed, or hasn't completed.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests

GITHUB_RE = re.compile(r"https://github.com/([\w-]+)/([\w.-]+)(?:/tree/([\w./-]+))?")
SKIP_COMMIT_RE = re.compile(
    r"(?i)(?:\[(?:ci|actions)[-_/\s]*skip\]|\[skip[-_/\s]*(?:ci|actions)\]|skip[-_/\s]*(?:ci|actions))"
)


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

    url = "https://api.github.com/repos/{repo}/actions/runs?per_page=100&status=completed".format(
        repo=repo
    )
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

    def _normalize_conclusion(value: str | None) -> str:
        if not isinstance(value, str):
            return ""
        return re.sub(r"[\s-]+", "_", value.strip().lower())

    def _should_skip_commit(commit: dict) -> bool:
        message = commit.get("commit", {}).get("message", "")
        if SKIP_COMMIT_RE.search(message):
            return True
        for key in ("author", "committer"):
            login = (commit.get(key) or {}).get("login")
            name = commit.get("commit", {}).get(key, {}).get("name")
            if isinstance(login, str) and login.endswith("[bot]"):
                return True
            if isinstance(name, str) and name.endswith("[bot]"):
                return True
        return False

    def _evaluate_runs(runs: Iterable[dict]) -> str:
        """Return the overall conclusion for the most recent attempt of each workflow."""

        latest_runs: dict[tuple[object, object, object], dict] = {}

        def _attempt_key(run: dict) -> tuple[int, str]:
            raw_attempt = run.get("run_attempt")
            try:
                attempt = int(raw_attempt)
            except (TypeError, ValueError):
                attempt = 0
            updated = run.get("updated_at")
            return (attempt, str(updated) if updated is not None else "")

        for run in runs:
            key = (
                run.get("workflow_id"),
                run.get("run_number"),
                run.get("name"),
            )
            current = latest_runs.get(key)
            if current is None or _attempt_key(run) > _attempt_key(current):
                latest_runs[key] = run

        conclusions = {
            _normalize_conclusion(r.get("conclusion")) for r in latest_runs.values()
        }
        if any(c in failures for c in conclusions):
            return "failure"
        if "success" in conclusions:
            return "success"
        # Default to failure so lack of CI coverage surfaces as ❌
        return "failure"

    def _fetch() -> str | None:
        commits_resp = requests.get(
            f"https://api.github.com/repos/{repo}/commits?sha={branch}&per_page=20",
            headers=headers,
            timeout=10,
        )
        commits_resp.raise_for_status()
        commits = commits_resp.json()

        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        runs = resp.json().get("workflow_runs", [])

        runs_by_sha: dict[str, list[dict]] = {}
        for run in runs:
            sha = run.get("head_sha")
            if not isinstance(sha, str):
                continue
            runs_by_sha.setdefault(sha, []).append(run)

        for commit in commits:
            sha = commit.get("sha")
            if not isinstance(sha, str):
                continue
            commit_runs = runs_by_sha.get(sha, [])
            if commit_runs:
                important = [
                    r for r in commit_runs if keywords.search(r.get("name", ""))
                ]
                if important:
                    commit_runs = important
                return _evaluate_runs(commit_runs)
            if _should_skip_commit(commit):
                continue
            return None
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
