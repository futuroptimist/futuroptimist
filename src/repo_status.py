"""Update README with repo status emojis.

Fetches the latest GitHub Actions run for each repo listed in the README's
"Related Projects" section and prepends a green check, red cross, or question
mark depending on whether the most recent workflow run on the default branch
completed successfully, failed, or hasn't completed.
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import requests

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RepoStatus:
    """Summary of a repository's workflow status for README rendering."""

    emoji: str
    failure_links: tuple[str, ...] = ()


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
    """Fetch the latest workflow run conclusion for ``repo`` and return an emoji."""

    return fetch_repo_status_details(repo, token, branch, attempts).emoji


def fetch_repo_status_details(
    repo: str,
    token: str | None = None,
    branch: str | None = None,
    attempts: int = 2,
) -> RepoStatus:
    """Fetch the latest workflow run conclusion for ``repo`` and failure links.

    The GitHub API occasionally returns inconsistent data if a workflow is
    updating while we query it. To catch this non-determinism we fetch the
    status multiple times and ensure all results match. If they differ we raise
    ``RuntimeError`` so the calling workflow fails loudly.
    """

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if branch is None:
        try:
            repo_resp = requests.get(
                f"https://api.github.com/repos/{repo}", headers=headers, timeout=10
            )
            repo_resp.raise_for_status()
            repo_data = repo_resp.json()
        except (requests.exceptions.RequestException, ValueError) as exc:
            LOGGER.warning("Unable to fetch default branch for %s: %s", repo, exc)
            return RepoStatus(status_to_emoji(None))
        if not isinstance(repo_data, dict):
            LOGGER.warning(
                "Unexpected repository payload for %s: %r", repo, type(repo_data)
            )
            return RepoStatus(status_to_emoji(None))
        branch = repo_data.get("default_branch")

    url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=100&status=completed"
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

    def _failure_link(run: dict) -> str | None:
        for key in ("html_url", "logs_url", "artifacts_url", "url"):
            value = run.get(key)
            if isinstance(value, str) and value:
                return value
        return None

    def _evaluate_runs(runs: Iterable[dict]) -> tuple[str, tuple[str, ...]]:
        """Return the overall conclusion and failing workflow links."""

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

        latest = tuple(latest_runs.values())
        conclusions = {_normalize_conclusion(r.get("conclusion")) for r in latest}
        if any(c in failures for c in conclusions):
            links = tuple(
                dict.fromkeys(
                    link
                    for run in latest
                    if _normalize_conclusion(run.get("conclusion")) in failures
                    for link in [_failure_link(run)]
                    if link
                )
            )
            return "failure", links
        if "success" in conclusions:
            return "success", ()
        # Default to failure so lack of CI coverage surfaces as ❌
        return "failure", ()

    def _fetch() -> tuple[str | None, tuple[str, ...]]:
        try:
            commits_resp = requests.get(
                f"https://api.github.com/repos/{repo}/commits?sha={branch}&per_page=20",
                headers=headers,
                timeout=10,
            )
            commits_resp.raise_for_status()
            commits_data = commits_resp.json()
        except (requests.exceptions.RequestException, ValueError) as exc:
            LOGGER.warning("Unable to fetch commits for %s@%s: %s", repo, branch, exc)
            return None, ()
        if not isinstance(commits_data, list):
            LOGGER.warning(
                "Unexpected commits payload for %s@%s: %r",
                repo,
                branch,
                type(commits_data),
            )
            return None, ()
        commits = commits_data

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            runs_data = resp.json()
        except (requests.exceptions.RequestException, ValueError) as exc:
            LOGGER.warning(
                "Unable to fetch workflow runs for %s@%s: %s", repo, branch, exc
            )
            return None, ()
        if not isinstance(runs_data, dict):
            LOGGER.warning(
                "Unexpected workflow payload for %s@%s: %r",
                repo,
                branch,
                type(runs_data),
            )
            return None, ()

        runs = runs_data.get("workflow_runs", [])
        if not isinstance(runs, list):
            LOGGER.warning(
                "Unexpected workflow run list for %s@%s: %r",
                repo,
                branch,
                type(runs),
            )
            return None, ()

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
            return None, ()
        return None, ()

    results = [_fetch() for _ in range(attempts)]
    conclusions = [result[0] for result in results]
    if len(set(conclusions)) > 1:
        raise RuntimeError(
            f"Non-deterministic workflow conclusion for {repo}: {conclusions}"
        )
    failure_links: tuple[str, ...] = ()
    if conclusions[0] in {
        "failure",
        "cancelled",
        "canceled",
        "timed_out",
        "startup_failure",
        "action_required",
    }:
        failure_links = tuple(
            dict.fromkeys(link for _, links in results for link in links)
        )
    return RepoStatus(status_to_emoji(conclusions[0]), failure_links)


def _strip_status_markup(line: str) -> str:
    """Remove status emoji and stale failure links from a README project line."""

    line = re.sub(r"^(-\s*)(?:[✅❌❓]\s*)*", r"\1", line)
    return re.sub(r"\s+— failures: .*$", "", line)


def update_readme(
    readme_path: Path,
    token: str | None = None,
    now: datetime | None = None,
) -> None:
    """Update README with status emojis, failure links, and a timestamp."""

    lines = readme_path.read_text(encoding="utf-8").splitlines()
    output: list[str] = []
    in_section = False
    if now is None:
        now = datetime.now(UTC)
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")
    ts_line = f"_Last updated: {timestamp}; checks hourly_"

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == "## Related Projects":
            in_section = True
            output.append(line)
            output.append(ts_line)
            i += 1
            while i < len(lines) and lines[i].startswith("_Last updated:"):
                i += 1
            continue
        if in_section and line.startswith("## "):
            in_section = False
        if in_section and line.startswith("_Last updated:"):
            i += 1
            continue
        if in_section and line.startswith("- "):
            match = GITHUB_RE.search(line)
            if match:
                repo = f"{match.group(1)}/{match.group(2)}"
                branch = match.group(3)
                status = fetch_repo_status_details(repo, token, branch)
                base_line = _strip_status_markup(line)
                rendered = f"- {status.emoji} {base_line[2:].lstrip()}"
                if status.emoji == "❌" and status.failure_links:
                    rendered += f" — failures: {', '.join(status.failure_links)}"
                output.append(rendered)
                i += 1
                continue
        output.append(line)
        i += 1

    # Ensure output file encoded as UTF-8 so emoji render correctly on Windows.
    readme_path.write_text("\n".join(output) + "\n", encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    token = os.environ.get("GITHUB_TOKEN")
    update_readme(Path(__file__).resolve().parent.parent / "README.md", token)
