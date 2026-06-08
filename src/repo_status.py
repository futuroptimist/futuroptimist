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

GITHUB_RE = re.compile(r"https://github.com/([\w-]+)/([\w.-]+)(?:/tree/([\w./-]+))?")
FAILURE_LINK_RE = re.compile(
    r"^\[[^\]]+\]\(https://github\.com/[^)]+/(?:actions(?:/runs/[^)]*)?|commit/[^)]*)\)"
    r"(?:,\s*)?"
)
SKIP_COMMIT_RE = re.compile(
    r"(?i)(?:\[(?:ci|actions)[-_/\s]*skip\]|\[skip[-_/\s]*(?:ci|actions)\]|skip[-_/\s]*(?:ci|actions))"
)


@dataclass(frozen=True)
class RepoStatus:
    """Rendered repository status plus optional failure detail links."""

    emoji: str
    failure_links: tuple[str, ...] = ()


def _markdown_label(text: object, fallback: str) -> str:
    """Return a compact Markdown link label with brackets removed."""
    if not isinstance(text, str) or not text.strip():
        return fallback
    return re.sub(r"[\[\]]", "", text.strip())


def _failure_link_for_run(repo: str, run: dict) -> str | None:
    """Return the best direct GitHub URL for a failed workflow run."""
    html_url = run.get("html_url")
    if isinstance(html_url, str) and html_url:
        return html_url
    run_id = run.get("id")
    if isinstance(run_id, int | str) and str(run_id):
        return f"https://github.com/{repo}/actions/runs/{run_id}"
    head_sha = run.get("head_sha")
    if isinstance(head_sha, str) and head_sha:
        return f"https://github.com/{repo}/commit/{head_sha}"
    return None


def _format_failure_links(links: Iterable[tuple[str, str]]) -> tuple[str, ...]:
    """Format unique failure URLs as comma-separated Markdown-ready links."""
    formatted: list[str] = []
    seen: set[str] = set()
    for label, url in links:
        if url in seen:
            continue
        seen.add(url)
        formatted.append(f"[{_markdown_label(label, 'failure details')}]({url})")
    return tuple(formatted)


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


def fetch_repo_status_details(
    repo: str,
    token: str | None = None,
    branch: str | None = None,
    attempts: int = 2,
) -> RepoStatus:
    """Fetch the latest workflow run conclusion and failure detail links.

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

    def _evaluate_runs(runs: Iterable[dict]) -> tuple[str, tuple[str, ...]]:
        """Return the conclusion and failure links for latest workflow attempts."""

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
        failed_runs = [
            r
            for r in latest_runs.values()
            if _normalize_conclusion(r.get("conclusion")) in failures
        ]
        if failed_runs:
            links = _format_failure_links(
                (
                    _markdown_label(r.get("name"), "failed run"),
                    url,
                )
                for r in failed_runs
                for url in [_failure_link_for_run(repo, r)]
                if url is not None
            )
            return "failure", links
        if "success" in conclusions:
            return "success", ()
        # Default to failure so lack of CI coverage surfaces as ❌. Link to any
        # available run/commit assets so readers still have a direct starting point.
        fallback_links = _format_failure_links(
            (
                _markdown_label(r.get("name"), "failure details"),
                url,
            )
            for r in latest_runs.values()
            for url in [_failure_link_for_run(repo, r)]
            if url is not None
        )
        return "failure", fallback_links

    def _fetch() -> tuple[str, tuple[str, ...]] | None:
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
            return None
        if not isinstance(commits_data, list):
            LOGGER.warning(
                "Unexpected commits payload for %s@%s: %r",
                repo,
                branch,
                type(commits_data),
            )
            return None
        commits = commits_data

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            runs_data = resp.json()
        except (requests.exceptions.RequestException, ValueError) as exc:
            LOGGER.warning(
                "Unable to fetch workflow runs for %s@%s: %s", repo, branch, exc
            )
            return None
        if not isinstance(runs_data, dict):
            LOGGER.warning(
                "Unexpected workflow payload for %s@%s: %r",
                repo,
                branch,
                type(runs_data),
            )
            return None

        runs = runs_data.get("workflow_runs", [])
        if not isinstance(runs, list):
            LOGGER.warning(
                "Unexpected workflow run list for %s@%s: %r",
                repo,
                branch,
                type(runs),
            )
            return None

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
    conclusion = conclusions[0]
    if conclusion is None:
        return RepoStatus(status_to_emoji(None))
    status, failure_links = conclusion
    emoji = status_to_emoji(status)
    return RepoStatus(emoji, failure_links if emoji == "❌" else ())


def fetch_repo_status(
    repo: str,
    token: str | None = None,
    branch: str | None = None,
    attempts: int = 2,
) -> str:
    """Fetch the latest workflow run conclusion for ``repo`` and return an emoji.

    Kept as the public emoji-only wrapper for callers that do not need failure
    details. Use :func:`fetch_repo_status_details` to render README links.
    """
    return fetch_repo_status_details(repo, token, branch, attempts).emoji


def _strip_status_prefix(line: str) -> str:
    """Remove existing status emojis and generated failure links from a bullet."""
    content = line[2:].lstrip()
    content = re.sub(r"^(?:[✅❌❓]\s*)+", "", content)
    while True:
        match = FAILURE_LINK_RE.match(content)
        if match is None:
            break
        content = content[match.end() :].lstrip()
    content = re.sub(r"^—\s*", "", content)
    return content


def _status_prefix(status: RepoStatus) -> str:
    """Return the README bullet prefix for a repository status."""
    if status.emoji == "❌" and status.failure_links:
        return f"{status.emoji} {', '.join(status.failure_links)} —"
    return status.emoji


def update_readme(
    readme_path: Path,
    token: str | None = None,
    now: datetime | None = None,
) -> None:
    """Update README with status emojis, failure links, and one timestamp."""
    lines = readme_path.read_text(encoding="utf-8").splitlines()
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
            if i + 1 < len(lines) and lines[i + 1].startswith("_Last updated:"):
                lines[i + 1] = ts_line
                i += 2
            else:
                lines.insert(i + 1, ts_line)
                i += 2
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.startswith("_Last updated:"):
            del lines[i]
            continue
        if in_section and line.startswith("- "):
            match = GITHUB_RE.search(line)
            if match:
                repo = f"{match.group(1)}/{match.group(2)}"
                branch = match.group(3)
                status = fetch_repo_status_details(repo, token, branch)
                content = _strip_status_prefix(line)
                # Ensure UTF-8 output; lines later written with utf-8 encoding.
                lines[i] = f"- {_status_prefix(status)} {content}"
        i += 1

    # Ensure output file encoded as UTF-8 so emoji render correctly on Windows.
    readme_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    token = os.environ.get("GITHUB_TOKEN")
    update_readme(Path(__file__).resolve().parent.parent / "README.md", token)
