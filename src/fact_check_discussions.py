"""Export GitHub Discussions used for Futuroptimist fact-checks."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any, Iterator

import requests

from . import github_auth


API_URL = "https://api.github.com/repos/{repo}/discussions"
DEFAULT_CATEGORY = "Fact Check"
DEFAULT_OUTPUT = pathlib.Path("data/fact_check_discussions.json")


def fetch_discussions(
    *,
    repo: str,
    token: str | None,
    per_page: int = 30,
    max_pages: int = 5,
    state: str | None = None,
    timeout: int = 10,
) -> Iterator[dict[str, Any]]:
    """Yield discussion payloads from the GitHub REST API."""

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for page in range(1, max_pages + 1):
        params: dict[str, Any] = {"per_page": per_page, "page": page}
        if state:
            params["state"] = state
        response = requests.get(
            API_URL.format(repo=repo),
            headers=headers,
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            break
        for item in payload:
            if isinstance(item, dict):
                yield item
        if len(payload) < per_page:
            break


def _normalise_state(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def _extract_reactions(data: dict[str, Any]) -> dict[str, int]:
    reactions = data.get("reactions") or {}

    def _as_int(key: str) -> int:
        try:
            return int(reactions.get(key) or 0)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            return 0

    return {
        "total": _as_int("total_count"),
        "plus_one": _as_int("+1"),
        "minus_one": _as_int("-1"),
        "confused": _as_int("confused"),
        "heart": _as_int("heart"),
        "hooray": _as_int("hooray"),
        "eyes": _as_int("eyes"),
        "rocket": _as_int("rocket"),
    }


def build_fact_check_index(
    *,
    repo: str,
    token: str | None,
    category: str = DEFAULT_CATEGORY,
    include_closed: bool = False,
    per_page: int = 30,
    max_pages: int = 5,
    output_path: pathlib.Path | None = None,
) -> list[dict[str, Any]]:
    """Return fact-check discussion metadata and optionally write JSON."""

    category_normalised = category.strip().lower()
    records: list[dict[str, Any]] = []
    state = "all" if include_closed else "open"
    for discussion in fetch_discussions(
        repo=repo,
        token=token,
        per_page=per_page,
        max_pages=max_pages,
        state=state,
    ):
        raw_category = (
            (discussion.get("category") or {}).get("name")
            if isinstance(discussion, dict)
            else None
        )
        if (
            not isinstance(raw_category, str)
            or raw_category.strip().lower() != category_normalised
        ):
            continue

        state = _normalise_state(discussion.get("state")) or "open"
        if not include_closed and state != "open":
            continue

        user = discussion.get("user") or {}
        record = {
            "number": discussion.get("number"),
            "title": discussion.get("title"),
            "url": discussion.get("html_url"),
            "state": state,
            "created_at": discussion.get("created_at"),
            "updated_at": discussion.get("updated_at"),
            "author": user.get("login") if isinstance(user, dict) else None,
            "comments": discussion.get("comments"),
            "answer_url": discussion.get("answer_html_url"),
            "category": raw_category,
            "reactions": _extract_reactions(discussion),
        }
        records.append(record)

    records.sort(
        key=lambda item: (
            (item.get("updated_at") or ""),
            item.get("number") or 0,
        ),
        reverse=True,
    )

    if output_path is None:
        output_path = DEFAULT_OUTPUT
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return records


def _resolve_token(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    try:
        return github_auth.get_github_token()
    except EnvironmentError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export GitHub Discussions fact-check threads to JSON",
    )
    parser.add_argument(
        "--repo",
        default="futuroptimist/futuroptimist",
        help="Repository in owner/name format",
    )
    parser.add_argument(
        "--category",
        default=DEFAULT_CATEGORY,
        help="Discussion category name to include",
    )
    parser.add_argument(
        "--include-closed",
        action="store_true",
        help="Include closed discussions",
    )
    parser.add_argument(
        "--per-page",
        type=int,
        default=30,
        help="Results to request per page",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum pages to fetch from the API",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=None,
        help=f"Destination JSON path (defaults to {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Optional GitHub token (falls back to environment variables)",
    )
    args = parser.parse_args(argv)

    token = _resolve_token(args.token)
    records = build_fact_check_index(
        repo=args.repo,
        token=token,
        category=args.category,
        include_closed=args.include_closed,
        per_page=args.per_page,
        max_pages=args.max_pages,
        output_path=args.output,
    )
    print(
        f"Fetched {len(records)} fact-check discussion(s) from {args.repo} in the {args.category!r} category"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
