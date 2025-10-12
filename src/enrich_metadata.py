"""Enrich metadata.json files with details from the YouTube Data API."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Sequence
import urllib.parse
import urllib.request

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
VIDEO_ROOT = BASE_DIR / "video_scripts"
ENV_VAR = "YOUTUBE_API_KEY"
API_PARTS = ("snippet", "contentDetails", "statistics")
API_URL = (
    "https://www.googleapis.com/youtube/v3/videos?part={parts}&id={ids}&key={key}"
)


@dataclass(frozen=True)
class VideoInfo:
    """Minimal metadata returned by the YouTube API."""

    title: str
    publish_date: str | None
    duration_seconds: int
    thumbnail: str
    view_count: int


_DURATION_RE = re.compile(
    r"^P(?:(?P<weeks>\d+)W)?(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$"
)


def parse_duration(value: str) -> int:
    """Return the number of seconds represented by an ISO-8601 duration string."""

    if not value:
        return 0
    match = _DURATION_RE.match(value)
    if not match:
        return 0
    parts = {name: match.group(name) for name in _DURATION_RE.groupindex}
    total = 0
    if parts.get("weeks"):
        total += int(parts["weeks"]) * 7 * 24 * 3600
    if parts.get("days"):
        total += int(parts["days"]) * 24 * 3600
    if parts.get("hours"):
        total += int(parts["hours"]) * 3600
    if parts.get("minutes"):
        total += int(parts["minutes"]) * 60
    if parts.get("seconds"):
        total += int(parts["seconds"])
    return total


def _extract_date(value: str) -> str | None:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.date().isoformat()


def _chunked(items: Sequence[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(items), size):
        yield list(items[i : i + size])


def fetch_video_metadata(
    video_ids: Sequence[str], youtube_key: str
) -> dict[str, VideoInfo]:
    """Fetch metadata for ``video_ids`` using the YouTube Data v3 API."""

    results: dict[str, VideoInfo] = {}
    if not video_ids:
        return results
    for batch in _chunked(video_ids, 50):
        ids = ",".join(batch)
        url = API_URL.format(
            parts=",".join(API_PARTS),
            ids=urllib.parse.quote(ids, safe=","),
            key=urllib.parse.quote(youtube_key, safe=""),
        )
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for item in data.get("items", []):
            video_id = item.get("id")
            if not isinstance(video_id, str):
                continue
            snippet = item.get("snippet") or {}
            content = item.get("contentDetails") or {}
            statistics = item.get("statistics") or {}
            title = snippet.get("title") or ""
            published_at = snippet.get("publishedAt")
            publish_date = (
                _extract_date(published_at) if isinstance(published_at, str) else None
            )
            duration_seconds = parse_duration(content.get("duration", ""))
            thumbnails = snippet.get("thumbnails") or {}

            def _select_thumbnail(data: dict) -> str:
                if not isinstance(data, dict):
                    return ""
                preference = ["maxres", "standard", "high", "medium", "default"]
                for key in preference:
                    entry = data.get(key)
                    if isinstance(entry, dict):
                        url = entry.get("url")
                        if isinstance(url, str) and url.strip():
                            return url.strip()
                    elif isinstance(entry, str) and entry.strip():
                        return entry.strip()
                for value in data.values():
                    if isinstance(value, str) and value.strip():
                        return value.strip()
                    if isinstance(value, dict):
                        url = value.get("url")
                        if isinstance(url, str) and url.strip():
                            return url.strip()
                return ""

            raw_view_count = statistics.get("viewCount", "0")
            try:
                view_count = int(str(raw_view_count))
            except (TypeError, ValueError):
                view_count = 0

            thumbnail = _select_thumbnail(thumbnails)
            if thumbnail and not thumbnail.startswith("http"):
                thumbnail = ""
            results[video_id] = VideoInfo(
                title=title,
                publish_date=publish_date,
                duration_seconds=duration_seconds,
                thumbnail=thumbnail,
                view_count=view_count,
            )
    return results


def apply_updates(
    metadata_paths: Iterable[pathlib.Path],
    info_map: dict[str, VideoInfo],
    *,
    dry_run: bool = False,
) -> list[pathlib.Path]:
    """Apply API data to each metadata file and return the ones that changed."""

    updated: list[pathlib.Path] = []
    for meta_path in metadata_paths:
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"Skipping invalid JSON: {meta_path}", file=sys.stderr)
            continue
        youtube_id = str(data.get("youtube_id", "")).strip()
        if not youtube_id:
            continue
        info = info_map.get(youtube_id)
        if not info:
            continue
        changed = False
        if info.title and data.get("title") != info.title:
            data["title"] = info.title
            changed = True
        if info.publish_date and data.get("publish_date") != info.publish_date:
            data["publish_date"] = info.publish_date
            changed = True
        if data.get("duration_seconds") != info.duration_seconds:
            data["duration_seconds"] = info.duration_seconds
            changed = True
        if info.thumbnail:
            if data.get("thumbnail") != info.thumbnail:
                data["thumbnail"] = info.thumbnail
                changed = True
        if info.view_count > 0:
            if data.get("view_count") != info.view_count:
                data["view_count"] = info.view_count
                changed = True
        elif "view_count" not in data:
            data["view_count"] = 0
            changed = True
        if changed:
            if not dry_run:
                meta_path.write_text(
                    json.dumps(data, indent=2) + "\n", encoding="utf-8"
                )
            updated.append(meta_path)
    return updated


def _collect_metadata(video_root: pathlib.Path) -> tuple[list[pathlib.Path], list[str]]:
    paths: list[pathlib.Path] = []
    ids: list[str] = []
    seen: set[str] = set()
    for meta_path in sorted(video_root.glob("*/metadata.json")):
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"Skipping invalid JSON: {meta_path}", file=sys.stderr)
            continue
        youtube_id = str(data.get("youtube_id", "")).strip()
        if not youtube_id:
            continue
        paths.append(meta_path)
        if youtube_id not in seen:
            seen.add(youtube_id)
            ids.append(youtube_id)
    return paths, ids


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Enrich video metadata using the YouTube Data API",
    )
    parser.add_argument(
        "--video-root",
        default=str(VIDEO_ROOT),
        help="Directory containing video_scripts/*/metadata.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would change without writing",
    )
    args = parser.parse_args(argv)

    youtube_key = os.getenv(ENV_VAR)
    if not youtube_key:
        print(f"{ENV_VAR} must be set", file=sys.stderr)
        return 1

    video_root = pathlib.Path(args.video_root)
    paths, ids = _collect_metadata(video_root)
    if not ids:
        print("No metadata files with youtube_id found.")
        return 0

    info_map = fetch_video_metadata(ids, youtube_key)
    updated = apply_updates(paths, info_map, dry_run=args.dry_run)

    if args.dry_run:
        if updated:
            print("Would update:")
            for path in updated:
                print(f" - {path}")
        else:
            print("No changes needed.")
    else:
        if updated:
            print("Updated:")
            for path in updated:
                print(f" - {path}")
        else:
            print("Metadata already up to date.")

    missing = sorted(set(ids) - set(info_map))
    if missing:
        print("No API data for:", ", ".join(missing))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
