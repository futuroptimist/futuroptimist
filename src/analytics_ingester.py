"""Fetch YouTube Analytics metrics and persist them to metadata files."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Iterable


DEFAULT_METRICS = (
    "views",
    "estimatedMinutesWatched",
    "averageViewDuration",
    "impressions",
    "impressionsClickThroughRate",
)

API_URL = "https://youtubeanalytics.googleapis.com/v2/reports"
TOKEN_ENV = "YOUTUBE_ANALYTICS_TOKEN"


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _iter_metadata_paths(
    video_root: pathlib.Path, slugs: Iterable[str] | None
) -> list[tuple[pathlib.Path, str, str]]:
    allowed = {slug.strip() for slug in slugs or [] if slug and slug.strip()} or None
    entries: list[tuple[pathlib.Path, str, str]] = []
    for meta_path in sorted(video_root.glob("*/metadata.json")):
        slug = meta_path.parent.name
        if allowed is not None and slug not in allowed:
            continue
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        youtube_id = str(data.get("youtube_id", "")).strip()
        if not youtube_id:
            continue
        entries.append((meta_path, slug, youtube_id))
    return entries


def _build_request(
    video_id: str,
    token: str,
    start_date: str,
    end_date: str,
    metrics: Iterable[str] = DEFAULT_METRICS,
) -> urllib.request.Request:
    params = {
        "ids": "channel==MINE",
        "filters": f"video=={video_id}",
        "dimensions": "video",
        "metrics": ",".join(metrics),
        "startDate": start_date,
        "endDate": end_date,
    }
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    return urllib.request.Request(url, headers=headers)


def _column_mapping() -> dict[str, tuple[str, type]]:
    return {
        "views": ("views", int),
        "estimatedMinutesWatched": ("watch_time_minutes", float),
        "averageViewDuration": ("average_view_duration_seconds", float),
        "impressions": ("impressions", int),
        "impressionsClickThroughRate": ("impressions_click_through_rate", float),
    }


def fetch_video_metrics(
    *, video_id: str, token: str, start_date: str, end_date: str
) -> dict[str, float | int]:
    """Return analytics metrics for ``video_id``.

    The YouTube Analytics API requires an OAuth 2 bearer token. The caller is
    responsible for obtaining it and passing it via ``token``.
    """

    request = _build_request(video_id, token, start_date, end_date)
    with urllib.request.urlopen(request) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    headers = payload.get("columnHeaders") or []
    rows = payload.get("rows") or []
    if not headers or not rows:
        return {}

    mapping = _column_mapping()
    name_to_index: dict[str, int] = {}
    for idx, header in enumerate(headers):
        name = header.get("name")
        if isinstance(name, str):
            name_to_index[name] = idx

    values: dict[str, float | int] = {}
    row = rows[0]
    for column, (alias, caster) in mapping.items():
        position = name_to_index.get(column)
        if position is None or position >= len(row):
            continue
        raw = row[position]
        try:
            value = caster(raw)
        except (TypeError, ValueError):
            continue
        values[alias] = value
    return values


def _update_metadata(path: pathlib.Path, metrics: dict[str, float | int]) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    analytics = data.get("analytics")
    if not isinstance(analytics, dict):
        analytics = {}
    analytics.update(metrics)
    analytics["updated_at"] = _now_iso()
    data["analytics"] = analytics
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def ingest(
    *,
    video_root: pathlib.Path,
    start_date: str,
    end_date: str,
    slugs: Iterable[str] | None = None,
    token: str | None = None,
    dry_run: bool = False,
) -> list[dict[str, float | int | str]]:
    """Fetch analytics for metadata files under ``video_root``."""

    token = (token or os.getenv(TOKEN_ENV, "")).strip()
    if not token:
        raise EnvironmentError(f"{TOKEN_ENV} must be set")

    records: list[dict[str, float | int | str]] = []
    for meta_path, slug, youtube_id in _iter_metadata_paths(video_root, slugs):
        metrics = fetch_video_metrics(
            video_id=youtube_id,
            token=token,
            start_date=start_date,
            end_date=end_date,
        )
        if not metrics:
            continue
        if not dry_run:
            _update_metadata(meta_path, metrics)
        entry: dict[str, float | int | str] = {"slug": slug, "youtube_id": youtube_id}
        entry.update(metrics)
        records.append(entry)
    return records


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Fetch YouTube Analytics metrics and update metadata files",
    )
    parser.add_argument(
        "--video-root",
        default="video_scripts",
        type=pathlib.Path,
        help="Directory containing video script folders",
    )
    parser.add_argument(
        "--start-date",
        required=True,
        help="Analytics window start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="Analytics window end date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--slug",
        action="append",
        default=None,
        help="Limit ingestion to specific slugs",
    )
    parser.add_argument(
        "--output",
        default=pathlib.Path("analytics/report.json"),
        type=pathlib.Path,
        help="Path to write a JSON summary",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Collect metrics without modifying metadata files",
    )
    args = parser.parse_args(argv)

    video_root = args.video_root.resolve()
    summary = ingest(
        video_root=video_root,
        start_date=args.start_date,
        end_date=args.end_date,
        slugs=args.slug,
        dry_run=args.dry_run,
    )

    if args.output:
        output_path = args.output.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    count = len(summary)
    message = (
        "No analytics data fetched"
        if count == 0
        else f"Fetched analytics for {count} video(s)"
    )
    print(message)


if __name__ == "__main__":  # pragma: no cover
    main()
