"""Update video metadata.json files with details from YouTube Data API v3."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import urllib.error
import urllib.request
from typing import Iterable

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
VIDEO_ROOT = BASE_DIR / "video_scripts"
YOUTUBE_KEY_ENV = "YOUTUBE_API_KEY"
API_URL = (
    "https://www.googleapis.com/youtube/v3/videos"
    "?part=snippet,contentDetails,statistics&id={video_id}&key={youtube_key}"
)

_DURATION_RE = re.compile(
    r"^P(?:(?P<weeks>\d+)W)?(?:(?P<days>\d+)D)?"
    r"(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$"
)


def parse_duration(value: str | None) -> int:
    """Return total seconds represented by an ISO-8601 duration string."""

    if not value:
        return 0
    match = _DURATION_RE.match(value)
    if not match:
        return 0
    parts = {k: int(v) if v else 0 for k, v in match.groupdict().items()}
    seconds = (
        parts["weeks"] * 7 * 24 * 3600
        + parts["days"] * 24 * 3600
        + parts["hours"] * 3600
        + parts["minutes"] * 60
        + parts["seconds"]
    )
    return seconds


def iter_metadata_files(
    root: pathlib.Path, slugs: set[str] | None
) -> Iterable[pathlib.Path]:
    for meta in sorted(root.glob("*/metadata.json")):
        if slugs and meta.parent.name not in slugs:
            continue
        yield meta


def _parse_view_count(value: object) -> int | None:
    if isinstance(value, str):
        value = value.strip()
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def fetch_metadata(video_id: str, youtube_key: str, timeout: int = 10) -> dict | None:
    url = API_URL.format(video_id=video_id, youtube_key=youtube_key)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        print(f"failed to fetch metadata for {video_id}: {exc}")
        return None
    items = payload.get("items") or []
    if not items:
        print(f"no metadata found for {video_id}")
        return None
    item = items[0]
    snippet = item.get("snippet") or {}
    details = item.get("contentDetails") or {}
    duration_seconds = parse_duration(details.get("duration"))
    published = snippet.get("publishedAt", "")
    publish_date = published.split("T", 1)[0] if published else ""
    thumbnails = snippet.get("thumbnails") or {}
    statistics = item.get("statistics") or {}
    view_count = _parse_view_count(statistics.get("viewCount"))

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
        # Sometimes thumbnails dict is a simple mapping of size->URL string
        for value in data.values():
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, dict):
                url = value.get("url")
                if isinstance(url, str) and url.strip():
                    return url.strip()
        return ""

    return {
        "title": snippet.get("title", ""),
        "publish_date": publish_date,
        "duration_seconds": duration_seconds,
        "description": snippet.get("description", ""),
        "keywords": list(snippet.get("tags", []) or []),
        "thumbnail": _select_thumbnail(thumbnails),
        "view_count": view_count,
    }


def update_metadata_file(path: pathlib.Path, updates: dict) -> bool:
    original = json.loads(path.read_text())
    youtube_id = original.get("youtube_id")
    if not youtube_id:
        return False
    changed = False
    for key, value in updates.items():
        if value is None:
            continue
        if key == "keywords" and value == [] and original.get(key):
            continue
        if key == "thumbnail" and not value:
            continue
        if original.get(key) != value:
            original[key] = value
            changed = True
    if changed:
        path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Update video metadata using YouTube Data API"
    )
    parser.add_argument(
        "--slug",
        action="append",
        default=None,
        help="Limit updates to specific slug folders",
    )
    args = parser.parse_args(argv)

    youtube_key = os.getenv(YOUTUBE_KEY_ENV, "").strip()
    if not youtube_key:
        print(f"{YOUTUBE_KEY_ENV} must be set")
        return 1

    slugs = set(args.slug) if args.slug else None
    updated = 0
    failures = 0
    for meta_path in iter_metadata_files(VIDEO_ROOT, slugs):
        data = json.loads(meta_path.read_text())
        video_id = data.get("youtube_id")
        if not isinstance(video_id, str) or not video_id:
            continue
        info = fetch_metadata(video_id, youtube_key)
        if info is None:
            failures += 1
            continue
        if update_metadata_file(meta_path, info):
            updated += 1
            print(f"updated {meta_path}")
    if updated:
        print(f"Updated {updated} metadata file(s)")
    else:
        print("No metadata updates applied")
    if failures:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
