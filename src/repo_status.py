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
class StatusLink:
    """A direct Markdown-ready link target for a failed check."""

    label: str
    url: str


@dataclass(frozen=True)
class RepoStatus:
    """Structured repo status, designed to grow with future repo metadata."""

    emoji: str
    failure_links: tuple[StatusLink, ...] = ()


# Backwards-compatible name for older callers/tests.
RepoStatusReport = RepoStatus


GITHUB_RE = re.compile(r"https://github.com/([\w-]+)/([\w.-]+)(?:/tree/([\w./-]+))?")
GENERATED_FAILURE_SUFFIX_RE = re.compile(r"\s+\(failing runs: [^)]*\)$")
GENERATED_STATUS_PREFIX_RE = re.compile(
    r"^(-\s*)(?:(?:[✅❌❓]\s*)+(?:\((?:\[[^\]]+\]\([^)]*\),?\s*)+\)\s*)?)+"
)
SKIP_COMMIT_RE = re.compile(
    r"(?i)(?:\[(?:ci|actions)[-_/\s]*skip\]|\[skip[-_/\s]*(?:ci|actions)\]|skip[-_/\s]*(?:ci|actions))"
)
FAILURE_LINK_FALLBACK_KEYS = ("logs_url", "artifacts_url", "check_suite_url")


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
    """Fetch the latest workflow run conclusion and failure links for ``repo``.

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

    def _failure_url(run: dict) -> str | None:
        html_url = run.get("html_url")
        if isinstance(html_url, str) and html_url:
            return html_url
        run_id = run.get("id")
        if run_id is not None:
            return f"https://github.com/{repo}/actions/runs/{run_id}"
        for key in FAILURE_LINK_FALLBACK_KEYS:
            url_value = run.get(key)
            if isinstance(url_value, str) and url_value:
                return url_value
        return None

    def _run_label(run: dict) -> str:
        name = run.get("display_title") or run.get("name") or run.get("workflow_name")
        return str(name).strip() if name else "workflow run"

    def _failure_status_links(runs: Iterable[dict]) -> tuple[StatusLink, ...]:
        failed_runs = [
            run
            for run in runs
            if _normalize_conclusion(run.get("conclusion")) in failures
            and _failure_url(run)
        ]
        base_labels = [_run_label(run) for run in failed_runs]
        duplicate_labels = {
            label for label in base_labels if base_labels.count(label) > 1
        }
        links: list[StatusLink] = []
        for run, base_label in zip(failed_runs, base_labels, strict=True):
            label = base_label
            if base_label in duplicate_labels:
                run_number = run.get("run_number")
                if run_number is not None:
                    label = f"{base_label} #{run_number}"
                run_attempt = run.get("run_attempt")
                if run_attempt not in (None, 1, "1"):
                    label = f"{label} attempt {run_attempt}"
            url = _failure_url(run)
            if url:
                links.append(StatusLink(label, url))
        return tuple(
            sorted(
                links,
                key=lambda link: (link.label.casefold(), link.url),
            )
        )

    def _evaluate_runs(runs: Iterable[dict]) -> tuple[str, tuple[StatusLink, ...]]:
        """Return conclusion and failure links for each workflow latest attempt."""

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

        latest_run_values = tuple(latest_runs.values())
        failed_links = _failure_status_links(latest_run_values)
        conclusions = {
            _normalize_conclusion(r.get("conclusion")) for r in latest_run_values
        }
        if any(c in failures for c in conclusions):
            return "failure", failed_links
        if "success" in conclusions:
            return "success", ()
        # Default to failure so lack of CI coverage surfaces as ❌
        return "failure", failed_links

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
    """Backward-compatible alias for ``fetch_repo_status_details``."""

    return fetch_repo_status_details(repo, token, branch, attempts)


def fetch_repo_status(
    repo: str,
    token: str | None = None,
    branch: str | None = None,
    attempts: int = 2,
) -> str:
    """Fetch the latest workflow run conclusion for ``repo`` and return an emoji."""

    return fetch_repo_status_details(repo, token, branch, attempts).emoji


def _escape_markdown_link_label(label: str) -> str:
    """Escape the small subset needed for generated Markdown link labels."""

    return label.replace("\\", "\\\\").replace("]", "\\]")


def _format_failure_links(links: tuple[StatusLink, ...]) -> str:
    """Format direct failure links for README bullets."""

    if not links:
        return ""
    rendered = ", ".join(
        f"[{_escape_markdown_link_label(link.label)}]({link.url})" for link in links
    )
    return f" ({rendered})"


def _strip_generated_status_prefix(line: str) -> str:
    """Remove previously generated status emoji and failure-link prefixes."""

    previous = None
    cleaned = line
    while cleaned != previous:
        previous = cleaned
        cleaned = GENERATED_STATUS_PREFIX_RE.sub(r"\1", cleaned)
    return GENERATED_FAILURE_SUFFIX_RE.sub("", cleaned)


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
        if in_section and line.startswith("_Last updated:"):
            continue
        if in_section and line.startswith("- "):
            match = GITHUB_RE.search(line)
            if match:
                repo = f"{match.group(1)}/{match.group(2)}"
                branch = match.group(3)
                report = fetch_repo_status_details(repo, token, branch)
                # Remove existing generated emoji/link prefixes before rendering.
                cleaned = _strip_generated_status_prefix(line)
                failure_prefix = _format_failure_links(report.failure_links)
                line = f"- {report.emoji}{failure_prefix} {cleaned[2:].lstrip()}"
        output.append(line)

    # Ensure output file encoded as UTF-8 so emoji render correctly on Windows
    readme_path.write_text("\n".join(output) + "\n", encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    token = os.environ.get("GITHUB_TOKEN")
    update_readme(Path(__file__).resolve().parent.parent / "README.md", token)
