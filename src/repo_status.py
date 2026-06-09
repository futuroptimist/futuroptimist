"""Update README Related Projects with statuses, star counts, and sorting.

Fetches repository metadata and the latest relevant GitHub Actions run for each
repo listed in the README's "Related Projects" section. Each project bullet gets
a status emoji, optional failure links, and a GitHub star count before the list is
sorted by stars descending and alphabetically for ties.
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import requests

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class StatusLink:
    """A labelled URL explaining a failing repository status."""

    label: str
    url: str


@dataclass(frozen=True)
class RepoMetadata:
    """Repository metadata used by the README status renderer."""

    default_branch: str | None = None
    stars: int | None = None


@dataclass(frozen=True)
class RepoStatus:
    """Rendered status plus optional direct links and repository metadata."""

    emoji: str
    failure_links: tuple[StatusLink, ...] = field(default_factory=tuple)
    stars: int | None = None


@dataclass(frozen=True)
class RepoStatusReport:
    """Backward-compatible status report with URL-only failure links."""

    emoji: str
    failure_links: tuple[str, ...] = field(default_factory=tuple)


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


def _github_headers(token: str | None = None) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_repo_metadata(repo: str, token: str | None = None) -> RepoMetadata:
    """Fetch default branch and stargazer count for ``repo``.

    Errors and malformed payloads are non-fatal so a README rebuild can still
    refresh status emojis and render an explicit unknown star marker.
    """

    try:
        repo_resp = requests.get(
            f"https://api.github.com/repos/{repo}",
            headers=_github_headers(token),
            timeout=10,
        )
        repo_resp.raise_for_status()
        repo_data = repo_resp.json()
    except (requests.exceptions.RequestException, ValueError) as exc:
        LOGGER.warning("Unable to fetch repository metadata for %s: %s", repo, exc)
        return RepoMetadata()
    if not isinstance(repo_data, dict):
        LOGGER.warning(
            "Unexpected repository payload for %s: %r", repo, type(repo_data)
        )
        return RepoMetadata()

    default_branch = repo_data.get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        default_branch = None

    raw_stars = repo_data.get("stargazers_count")
    stars = (
        raw_stars
        if isinstance(raw_stars, int) and not isinstance(raw_stars, bool)
        else None
    )
    if stars is None:
        LOGGER.warning("Missing or invalid stargazer count for %s: %r", repo, raw_stars)
    return RepoMetadata(default_branch, stars)


def format_star_count(stars: int | None) -> str:
    """Format a compact star count marker for README bullets."""

    return f"⭐ {stars}" if stars is not None else "⭐ ?"


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

    headers = _github_headers(token)
    metadata = fetch_repo_metadata(repo, token)
    if branch is None:
        branch = metadata.default_branch

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
        return None

    def _run_label(run: dict) -> str:
        name = run.get("name") or run.get("display_title") or "workflow run"
        return str(name).strip() or "workflow run"

    def _disambiguated_failure_links(runs: Iterable[dict]) -> tuple[StatusLink, ...]:
        failed_runs = [
            (run, _run_label(run), url)
            for run in runs
            if _normalize_conclusion(run.get("conclusion")) in failures
            for url in [_failure_url(run)]
            if url
        ]
        labels_by_base: dict[str, list[tuple[dict, str]]] = {}
        for run, base_label, url in failed_runs:
            labels_by_base.setdefault(base_label, []).append((run, url))

        def _unique_labels(
            base_label: str, grouped_runs: list[tuple[dict, str]]
        ) -> list[str]:
            def run_number_label(run: dict, url: str) -> str | None:
                run_number = run.get("run_number")
                if run_number is None:
                    return None
                return f"{base_label} #{run_number}"

            def workflow_label(run: dict, url: str) -> str | None:
                run_number = run.get("run_number")
                workflow_id = run.get("workflow_id")
                if run_number is None or workflow_id is None:
                    return None
                return f"{base_label} #{run_number} workflow {workflow_id}"

            def workflow_only_label(run: dict, url: str) -> str | None:
                workflow_id = run.get("workflow_id")
                if workflow_id is None:
                    return None
                return f"{base_label} workflow {workflow_id}"

            def run_id_label(run: dict, url: str) -> str | None:
                run_number = run.get("run_number")
                run_id = run.get("id")
                if run_number is None or run_id is None:
                    return None
                return f"{base_label} #{run_number} run {run_id}"

            def run_id_only_label(run: dict, url: str) -> str | None:
                run_id = run.get("id")
                if run_id is None:
                    return None
                return f"{base_label} run {run_id}"

            for labeler in (
                run_number_label,
                workflow_label,
                workflow_only_label,
                run_id_label,
                run_id_only_label,
            ):
                labels = [labeler(run, url) for run, url in grouped_runs]
                if all(label is not None for label in labels) and len(
                    set(labels)
                ) == len(labels):
                    return [str(label) for label in labels]
            return [f"{base_label} {url}" for _, url in grouped_runs]

        links: list[StatusLink] = []
        for base_label, grouped_runs in labels_by_base.items():
            if len(grouped_runs) == 1:
                run, url = grouped_runs[0]
                links.append(StatusLink(base_label, url))
                continue
            labels = _unique_labels(base_label, grouped_runs)
            for (_, url), label in zip(grouped_runs, labels, strict=True):
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
            workflow_id = run.get("workflow_id")
            run_number = run.get("run_number")
            run_id = run.get("id")
            if workflow_id is not None and run_number is not None:
                key = (workflow_id, run_number, None)
            elif run_id is not None:
                key = (None, None, run_id)
            else:
                key = (None, None, run.get("name"))
            current = latest_runs.get(key)
            if current is None or _attempt_key(run) > _attempt_key(current):
                latest_runs[key] = run

        latest = sorted(
            latest_runs.values(),
            key=lambda run: (
                _run_label(run).casefold(),
                str(run.get("workflow_id") or ""),
                str(run.get("run_number") or ""),
                str(run.get("id") or ""),
            ),
        )
        failed_links = _disambiguated_failure_links(latest)
        conclusions = {
            _normalize_conclusion(r.get("conclusion")) for r in latest_runs.values()
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
    return RepoStatus(
        status_to_emoji(conclusions[0]), tuple(failure_links), metadata.stars
    )


def fetch_repo_status(
    repo: str,
    token: str | None = None,
    branch: str | None = None,
    attempts: int = 2,
) -> str:
    """Fetch the latest workflow run conclusion for ``repo`` and return an emoji."""

    return fetch_repo_status_details(repo, token, branch, attempts).emoji


def fetch_repo_status_report(
    repo: str,
    token: str | None = None,
    branch: str | None = None,
    attempts: int = 2,
) -> RepoStatusReport:
    """Fetch the old URL-only status report shape for compatibility."""

    details = fetch_repo_status_details(repo, token, branch, attempts)
    return RepoStatusReport(
        details.emoji, tuple(link.url for link in details.failure_links)
    )


def _escape_markdown_label(label: str) -> str:
    return label.replace("\\", "\\\\").replace("]", r"\]")


def _format_failure_links(links: tuple[StatusLink, ...]) -> str:
    """Format direct failure URLs for README bullets."""

    if not links:
        return ""
    rendered = ", ".join(
        f"[{_escape_markdown_label(link.label)}]({link.url})" for link in links
    )
    return f" ({rendered}) {GENERATED_FAILURE_LINKS_MARKER}"


GENERATED_ACTION_RUN_LINK_RE = (
    r"\[(?:\\.|[^\]\\])+\]"
    r"\(https://github\.com/[\w.-]+/[\w.-]+/actions/runs/[^)]*\)"
)
GENERATED_FAILURE_LINKS_MARKER = "<!-- repo-status:failure-links -->"
GENERATED_FAILURE_LINKS_RE = re.compile(
    rf"^\((?:{GENERATED_ACTION_RUN_LINK_RE}(?:,\s*)?)+\)"
    rf"\s*{re.escape(GENERATED_FAILURE_LINKS_MARKER)}\s*"
)
LEGACY_STACKED_FAILURE_LINKS_RE = re.compile(
    rf"^\((?:{GENERATED_ACTION_RUN_LINK_RE}(?:,\s*)?)+\)\s*(?=[✅❌❓])"
)
LEGACY_GENERATED_LABEL_RE = r"(?:\\.|[^\]\\])*?(?:ci|test|lint|build)(?:\\.|[^\]\\])*?"
LEGACY_GENERATED_ACTION_RUN_LINK_RE = (
    rf"\[{LEGACY_GENERATED_LABEL_RE}\]"
    r"\(https://github\.com/[\w.-]+/[\w.-]+/actions/runs/[^)]*\)"
)
LEGACY_UNMARKED_FAILURE_LINKS_BEFORE_REPO_RE = re.compile(
    rf"^\((?:{LEGACY_GENERATED_ACTION_RUN_LINK_RE}(?:,\s*)?)+\)\s*"
    r"(?=https://github\.com/[\w.-]+/[\w.-]+(?:/tree/[\w./-]+)?(?:\s|$))",
    re.IGNORECASE,
)


STAR_PREFIX_RE = re.compile(r"^⭐\s*(?:\?|\d+)\s*")
VISIBLE_MARKDOWN_LINK_RE = re.compile(
    r"\*\*\[([^\]]+)\]\([^)]+\)\*\*|\[([^\]]+)\]\([^)]+\)"
)


@dataclass(frozen=True)
class RelatedProjectItem:
    """A parsed Related Projects bullet plus continuation lines."""

    first_line: str
    continuation_lines: tuple[str, ...] = ()
    cleaned: str = ""
    repo: str | None = None
    branch: str | None = None
    sort_name: str = ""
    status: RepoStatus | None = None


def strip_project_prefix(line: str) -> str:
    """Remove generated status, failure-link, and star prefixes idempotently."""

    content = line[2:].lstrip() if line.startswith("- ") else line.lstrip()
    while True:
        original = content
        emoji_match = re.match(r"^([✅❌❓])\s*", content)
        if emoji_match:
            content = content[emoji_match.end() :].lstrip()
            content = GENERATED_FAILURE_LINKS_RE.sub("", content, count=1).lstrip()
            content = LEGACY_STACKED_FAILURE_LINKS_RE.sub("", content, count=1).lstrip()
            content = LEGACY_UNMARKED_FAILURE_LINKS_BEFORE_REPO_RE.sub(
                "", content, count=1
            ).lstrip()
        content = STAR_PREFIX_RE.sub("", content, count=1).lstrip()
        content = re.sub(r"\s+\(failing runs: [^)]*\)$", "", content)
        if content == original:
            return content


# Backward-compatible private name used by earlier tests and callers.
def _strip_status_prefix(line: str) -> str:
    """Remove generated project prefixes from a Markdown bullet."""

    return strip_project_prefix(line)


def _project_sort_name(cleaned: str, repo: str) -> str:
    """Return the visible project name, falling back to owner/repo."""

    match = VISIBLE_MARKDOWN_LINK_RE.search(cleaned)
    if match:
        return (match.group(1) or match.group(2) or repo).strip() or repo
    return repo


def parse_related_project_items(lines: list[str]) -> list[RelatedProjectItem]:
    """Parse Markdown project bullets with indented continuation lines."""

    items: list[RelatedProjectItem] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith("- "):
            index += 1
            continue
        continuation: list[str] = []
        index += 1
        while index < len(lines) and lines[index].startswith((" ", "\t")):
            continuation.append(lines[index])
            index += 1
        cleaned = strip_project_prefix(line)
        match = GITHUB_RE.search(cleaned)
        repo = None
        branch = None
        sort_name = ""
        if match:
            repo = f"{match.group(1)}/{match.group(2)}"
            branch = match.group(3)
            sort_name = _project_sort_name(cleaned, repo)
        items.append(
            RelatedProjectItem(
                first_line=line,
                continuation_lines=tuple(continuation),
                cleaned=cleaned,
                repo=repo,
                branch=branch,
                sort_name=sort_name,
            )
        )
    return items


def render_project_item(item: RelatedProjectItem, details: RepoStatus) -> list[str]:
    """Render one project item with a fresh status and star prefix."""

    link_suffix = _format_failure_links(details.failure_links)
    first_line = (
        f"- {details.emoji}{link_suffix} {format_star_count(details.stars)} "
        f"{item.cleaned}"
    )
    return [first_line, *item.continuation_lines]


def sort_project_items(items: list[RelatedProjectItem]) -> list[RelatedProjectItem]:
    """Sort project items by stars descending, then name case-insensitively."""

    return sorted(
        items,
        key=lambda item: (
            -(
                item.status.stars
                if item.status and item.status.stars is not None
                else -1
            ),
            item.sort_name.casefold(),
            item.repo or "",
        ),
    )


def _render_related_project_block(
    block: list[RelatedProjectItem], token: str | None
) -> list[str]:
    hydrated: list[RelatedProjectItem] = []
    for item in block:
        if item.repo is None:
            hydrated.append(item)
            continue
        report = fetch_repo_status_details(item.repo, token, item.branch)
        hydrated.append(
            RelatedProjectItem(
                item.first_line,
                item.continuation_lines,
                item.cleaned,
                item.repo,
                item.branch,
                item.sort_name,
                report,
            )
        )

    rendered: list[str] = []
    for item in sort_project_items(hydrated):
        if item.status is None:
            rendered.extend([item.first_line, *item.continuation_lines])
        else:
            rendered.extend(render_project_item(item, item.status))
    return rendered


def _update_related_section_lines(lines: list[str], token: str | None) -> list[str]:
    """Refresh and sort project bullet blocks without moving prose."""

    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith("- "):
            output.append(line)
            index += 1
            continue

        raw_block: list[str] = []
        while index < len(lines):
            current = lines[index]
            if current.startswith("- "):
                raw_block.append(current)
                index += 1
                while index < len(lines) and lines[index].startswith((" ", "\t")):
                    raw_block.append(lines[index])
                    index += 1
                continue
            break

        project_items = parse_related_project_items(raw_block)
        if project_items and all(item.repo is not None for item in project_items):
            output.extend(_render_related_project_block(project_items, token))
        else:
            output.extend(raw_block)
    return output


def update_readme(
    readme_path: Path,
    token: str | None = None,
    now: datetime | None = None,
) -> None:
    """Update README with status emojis, star counts, failure links, and timestamp."""

    lines = readme_path.read_text(encoding="utf-8").splitlines()
    if now is None:
        now = datetime.now(UTC)
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")
    ts_line = f"_Last updated: {timestamp}; checks hourly_"

    output: list[str] = []
    section_lines: list[str] = []
    in_section = False

    def flush_section() -> None:
        nonlocal section_lines
        filtered = [
            line for line in section_lines if not line.startswith("_Last updated:")
        ]
        output.extend(_update_related_section_lines(filtered, token))
        section_lines = []

    for line in lines:
        if line.strip() == "## Related Projects":
            in_section = True
            output.append(line)
            output.append(ts_line)
            continue
        if in_section and line.startswith("## "):
            flush_section()
            in_section = False
            output.append(line)
            continue
        if in_section:
            section_lines.append(line)
        else:
            output.append(line)

    if in_section:
        flush_section()

    # Ensure output file encoded as UTF-8 so emoji render correctly on Windows
    readme_path.write_text("\n".join(output) + "\n", encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    token = os.environ.get("GITHUB_TOKEN")
    update_readme(Path(__file__).resolve().parent.parent / "README.md", token)
