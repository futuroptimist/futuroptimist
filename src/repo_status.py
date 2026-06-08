"""Update README with repo status emojis.

Fetches the latest GitHub Actions runs for each repo listed in the README's
"Related Projects" section and prepends a green check, red cross, or question
mark depending on whether the most recent relevant workflow runs on the default
branch completed successfully, failed, or haven't completed. Failed statuses can
also include direct links to the failing workflow runs.
"""

from __future__ import annotations

import logging
import os
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import requests

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class StatusLink:
    """A rendered README status link."""

    label: str
    url: str


@dataclass(frozen=True)
class RepoStatus:
    """Structured repository status for README rendering and future metadata."""

    emoji: str
    failure_links: tuple[StatusLink, ...] = field(default_factory=tuple)


# Backward-compatible name used by earlier tests/callers.
RepoStatusReport = RepoStatus

GITHUB_RE = re.compile(r"https://github.com/([\w-]+)/([\w.-]+)(?:/tree/([\w./-]+))?")
SKIP_COMMIT_RE = re.compile(
    r"(?i)(?:\[(?:ci|actions)[-_/\s]*skip\]|\[skip[-_/\s]*(?:ci|actions)\]|skip[-_/\s]*(?:ci|actions))"
)
FAILURE_CONCLUSIONS = {
    "failure",
    "cancelled",
    "canceled",
    "timed_out",
    "startup_failure",
    "action_required",
}
CI_NAME_RE = re.compile(r"(test|lint|build|ci)", re.I)
TIMESTAMP_RE = re.compile(r"^_Last updated: .*; checks hourly_$")
OLD_FAILURE_SUFFIX_RE = re.compile(r"\s+\(failing runs: [^)]*\)$")


def _normalize_conclusion(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[\s-]+", "_", value.strip().lower())


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
    normalized = _normalize_conclusion(conclusion)
    if normalized == "success":
        return "✅"
    if normalized in FAILURE_CONCLUSIONS:
        return "❌"
    return "❓"


def _should_skip_commit(commit: dict) -> bool:
    message = commit.get("commit", {}).get("message", "")
    if isinstance(message, str) and SKIP_COMMIT_RE.search(message):
        return True
    for key in ("author", "committer"):
        login = (commit.get(key) or {}).get("login")
        name = commit.get("commit", {}).get(key, {}).get("name")
        if isinstance(login, str) and login.endswith("[bot]"):
            return True
        if isinstance(name, str) and name.endswith("[bot]"):
            return True
    return False


def _attempt_key(run: dict) -> tuple[int, str]:
    raw_attempt = run.get("run_attempt")
    try:
        attempt = int(raw_attempt)
    except (TypeError, ValueError):
        attempt = 0
    updated = run.get("updated_at")
    return (attempt, str(updated) if updated is not None else "")


def _run_url(repo: str, run: dict) -> str | None:
    html_url = run.get("html_url")
    if isinstance(html_url, str) and html_url:
        return html_url
    run_id = run.get("id")
    if run_id is not None:
        return f"https://github.com/{repo}/actions/runs/{run_id}"
    return None


def _base_run_label(run: dict) -> str:
    name = run.get("name") or run.get("display_title") or run.get("workflow_id")
    return str(name) if name is not None else "workflow run"


def _failure_links(repo: str, failed_runs: Iterable[dict]) -> tuple[StatusLink, ...]:
    runs = list(failed_runs)
    label_counts = Counter(_base_run_label(run) for run in runs)
    links: list[StatusLink] = []
    for run in runs:
        url = _run_url(repo, run)
        if not url:
            continue
        label = _base_run_label(run)
        if label_counts[label] > 1:
            run_number = run.get("run_number")
            run_attempt = run.get("run_attempt")
            if run_number is not None:
                label = f"{label} #{run_number}"
            if run_attempt not in (None, 1, "1"):
                label = f"{label} attempt {run_attempt}"
        links.append(StatusLink(label, url))
    return tuple(sorted(links, key=lambda link: (link.label.lower(), link.url)))


def _evaluate_runs(
    repo: str, runs: Iterable[dict]
) -> tuple[str, tuple[StatusLink, ...]]:
    """Return conclusion and failure links for each workflow latest attempt."""

    latest_runs: dict[tuple[object, object, object], dict] = {}
    for run in runs:
        key = (run.get("workflow_id"), run.get("run_number"), run.get("name"))
        current = latest_runs.get(key)
        if current is None or _attempt_key(run) > _attempt_key(current):
            latest_runs[key] = run

    failed_runs = [
        run
        for run in latest_runs.values()
        if _normalize_conclusion(run.get("conclusion")) in FAILURE_CONCLUSIONS
    ]
    if failed_runs:
        return "failure", _failure_links(repo, failed_runs)

    conclusions = {
        _normalize_conclusion(r.get("conclusion")) for r in latest_runs.values()
    }
    if "success" in conclusions:
        return "success", ()
    # Preserve existing semantics: a commit with only non-success relevant runs
    # surfaces as failed rather than silently passing.
    return "failure", ()


def fetch_repo_status_details(
    repo: str,
    token: str | None = None,
    branch: str | None = None,
    attempts: int = 2,
) -> RepoStatus:
    """Fetch the latest workflow run status and actionable failure links.

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

    def _fetch() -> tuple[str | None, tuple[StatusLink, ...]]:
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
            if isinstance(sha, str):
                runs_by_sha.setdefault(sha, []).append(run)

        for commit in commits_data:
            sha = commit.get("sha")
            if not isinstance(sha, str):
                continue
            commit_runs = runs_by_sha.get(sha, [])
            if commit_runs:
                important = [
                    run
                    for run in commit_runs
                    if CI_NAME_RE.search(str(run.get("name", "")))
                ]
                if important:
                    commit_runs = important
                return _evaluate_runs(repo, commit_runs)
            if _should_skip_commit(commit):
                continue
            return None, ()
        return None, ()

    reports = [_fetch() for _ in range(attempts)]
    conclusions = [report[0] for report in reports]
    if len(set(conclusions)) > 1:
        raise RuntimeError(
            f"Non-deterministic workflow conclusion for {repo}: {conclusions}"
        )

    failure_links: list[StatusLink] = []
    for _, links in reports:
        for link in links:
            if link not in failure_links:
                failure_links.append(link)
    return RepoStatus(status_to_emoji(conclusions[0]), tuple(failure_links))


def fetch_repo_status_report(
    repo: str,
    token: str | None = None,
    branch: str | None = None,
    attempts: int = 2,
) -> RepoStatus:
    """Backward-compatible alias for structured repo status details."""

    return fetch_repo_status_details(repo, token, branch, attempts)


def fetch_repo_status(
    repo: str,
    token: str | None = None,
    branch: str | None = None,
    attempts: int = 2,
) -> str:
    """Fetch the latest workflow run conclusion for ``repo`` and return an emoji."""

    return fetch_repo_status_details(repo, token, branch, attempts).emoji


def _format_failure_links(links: tuple[StatusLink, ...]) -> str:
    """Format failed workflow links for README bullets."""

    if not links:
        return ""
    rendered = ", ".join(f"[{link.label}]({link.url})" for link in links)
    return f" ({rendered})"


def _strip_leading_link_group(text: str) -> str:
    if not text.startswith("("):
        return text
    depth = 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[index + 1 :].lstrip()
    return text


def _strip_generated_prefix(line: str) -> str:
    """Remove any previous generated status/link prefixes from a README bullet."""

    if not line.startswith("- "):
        return OLD_FAILURE_SUFFIX_RE.sub("", line)
    rest = line[2:].lstrip()
    changed = True
    while changed:
        changed = False
        while rest[:1] in {"✅", "❌", "❓"}:
            rest = rest[1:].lstrip()
            changed = True
        without_links = _strip_leading_link_group(rest)
        if without_links != rest:
            rest = without_links
            changed = True
    return OLD_FAILURE_SUFFIX_RE.sub("", f"- {rest}")


def update_readme(
    readme_path: Path,
    token: str | None = None,
    now: datetime | None = None,
) -> None:
    """Update README with status emojis, failure links, and a timestamp."""

    lines = readme_path.read_text(encoding="utf-8").splitlines()
    in_section = False
    if now is None:
        now = datetime.now(UTC)
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")
    ts_line = f"_Last updated: {timestamp}; checks hourly_"
    output: list[str] = []

    for line in lines:
        if line.strip() == "## Related Projects":
            in_section = True
            output.append(line)
            output.append(ts_line)
            continue
        if in_section and line.startswith("## "):
            in_section = False
        if in_section and TIMESTAMP_RE.match(line.strip()):
            continue
        if in_section and line.startswith("- "):
            match = GITHUB_RE.search(line)
            if match:
                repo = f"{match.group(1)}/{match.group(2)}"
                branch = match.group(3)
                status = fetch_repo_status_details(repo, token, branch)
                cleaned = _strip_generated_prefix(line)
                link_prefix = _format_failure_links(status.failure_links)
                line = f"- {status.emoji}{link_prefix} {cleaned[2:].lstrip()}"
        output.append(line)

    readme_path.write_text("\n".join(output) + "\n", encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    token = os.environ.get("GITHUB_TOKEN")
    update_readme(Path(__file__).resolve().parent.parent / "README.md", token)
