"""Generate a Markdown newsletter from Futuroptimist video metadata.

This fulfils the Phase 6 "Community" roadmap promise in ``INSTRUCTIONS.md``
to ship a scheduled newsletter builder that stitches recent scripts and
watch links together.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
from dataclasses import dataclass
from typing import Iterable, Sequence

DEFAULT_STATUSES = {"live"}
_SUMMARY_LIMIT = 200


@dataclass(slots=True)
class NewsletterItem:
    """Structured representation of a single newsletter entry."""

    slug: str
    title: str
    publish_date: dt.date | None
    summary: str
    youtube_url: str | None
    script_path: pathlib.Path | None
    tags: list[str]

    def formatted_date(self) -> str:
        return self.publish_date.isoformat() if self.publish_date else "date tbd"


def _parse_date(value: str | None) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _load_metadata(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_summary(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= _SUMMARY_LIMIT:
        return collapsed
    truncated = collapsed[: _SUMMARY_LIMIT - 1].rstrip()
    return f"{truncated}…"


def _summary_from_metadata(data: dict) -> str:
    for key in ("summary", "description"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            first_line = value.strip().splitlines()[0]
            return _clean_summary(first_line)
    return "Summary coming soon."


def _parse_tags(data: dict) -> list[str]:
    raw = data.get("tags")
    if isinstance(raw, list):
        return [str(tag) for tag in raw if isinstance(tag, str) and tag.strip()]
    return []


def collect_items(
    video_root: pathlib.Path,
    *,
    statuses: Iterable[str] | None = None,
    since: dt.date | None = None,
    limit: int | None = None,
) -> list[NewsletterItem]:
    """Return newsletter items filtered by status and date."""

    resolved_root = video_root.resolve()
    repo_root = resolved_root.parent
    status_filter = {
        status.strip().lower()
        for status in (statuses or DEFAULT_STATUSES)
        if status and status.strip()
    }
    if not status_filter:
        status_filter = DEFAULT_STATUSES

    items: list[NewsletterItem] = []
    for folder in sorted(resolved_root.glob("*/")):
        metadata_path = folder / "metadata.json"
        if not metadata_path.exists():
            continue
        try:
            data = _load_metadata(metadata_path)
        except json.JSONDecodeError:
            continue
        status = str(data.get("status", "")).strip().lower()
        if status_filter and status not in status_filter:
            continue
        publish_date = _parse_date(data.get("publish_date"))
        if since and publish_date and publish_date < since:
            continue
        title = data.get("title") or folder.name
        summary = _summary_from_metadata(data)
        youtube_id = data.get("youtube_id")
        youtube_url = (
            f"https://www.youtube.com/watch?v={youtube_id}"
            if isinstance(youtube_id, str) and youtube_id.strip()
            else None
        )
        script_fs_path = folder / "script.md"
        script_path: pathlib.Path | None = None
        if script_fs_path.exists():
            try:
                script_path = script_fs_path.relative_to(repo_root)
            except ValueError:
                script_path = script_fs_path
        tags = _parse_tags(data)
        items.append(
            NewsletterItem(
                slug=folder.name,
                title=str(title),
                publish_date=publish_date,
                summary=summary,
                youtube_url=youtube_url,
                script_path=script_path,
                tags=tags,
            )
        )

    items.sort(
        key=lambda item: (
            item.publish_date or dt.date.min,
            item.slug,
        ),
        reverse=True,
    )
    if limit is not None and limit >= 0:
        items = items[:limit]
    return items


def render_markdown(
    items: Sequence[NewsletterItem], *, newsletter_date: dt.date | None = None
) -> str:
    """Return a Markdown newsletter for ``items``."""

    today = newsletter_date or dt.date.today()
    lines = [f"# Futuroptimist Newsletter — {today.isoformat()}", ""]
    if not items:
        lines.append("_No published videos matched the current filters._")
        lines.append("")
        return "\n".join(lines)

    lines.append("Here’s what shipped recently:")
    lines.append("")
    for item in items:
        tag_suffix = f" _(tags: {', '.join(item.tags)})_" if item.tags else ""
        links: list[str] = []
        if item.script_path:
            links.append(f"[Script]({item.script_path.as_posix()})")
        if item.youtube_url:
            links.append(f"[Watch on YouTube]({item.youtube_url})")
        link_text = f" — {' · '.join(links)}" if links else ""
        lines.append(
            "- **{title}** ({date}) — {summary}{tags}{links}".format(
                title=item.title,
                date=item.formatted_date(),
                summary=item.summary,
                tags=tag_suffix,
                links=link_text,
            )
        )
    lines.append("")
    return "\n".join(lines)


def _parse_status_args(values: Sequence[str]) -> set[str]:
    statuses: set[str] = set()
    for raw in values:
        for part in raw.split(","):
            part = part.strip()
            if part:
                statuses.add(part.lower())
    return statuses


def _parse_limit(value: int | None) -> int | None:
    if value is None:
        return None
    if value < 0:
        return None
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a Markdown newsletter from video metadata",
    )
    parser.add_argument(
        "--video-root",
        type=pathlib.Path,
        default=pathlib.Path("video_scripts"),
        help="Directory containing video script folders",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=None,
        help="Optional path to write the newsletter (prints to stdout if omitted)",
    )
    parser.add_argument(
        "--status",
        action="append",
        default=[],
        help="Status to include (repeatable or comma-separated, defaults to 'live')",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Only include videos published on or after YYYY-MM-DD",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of entries to include",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Override the newsletter date (YYYY-MM-DD)",
    )
    args = parser.parse_args(argv)

    statuses = _parse_status_args(args.status)
    since = _parse_date(args.since)
    limit = _parse_limit(args.limit)
    items = collect_items(
        args.video_root,
        statuses=statuses or None,
        since=since,
        limit=limit,
    )
    newsletter_date = _parse_date(args.date) or dt.date.today()
    markdown = render_markdown(items, newsletter_date=newsletter_date)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        end = "" if markdown.endswith("\n") else "\n"
        print(markdown, end=end)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
