"""Annotate published metadata with final video URLs and processing stats.

Phase 8 of ``INSTRUCTIONS.md`` promises to write publish metadata (video URLs
and processing timings) back into ``metadata.json``. This module delivers that
feature with a testable helper and CLI entry point so publish automation stays
deterministic and well-tested.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
import pathlib
from typing import Iterable


VIDEO_ROOT = pathlib.Path("video_scripts")
METADATA_NAME = "metadata.json"


def _parse_datetime(value: str) -> datetime:
    text = value.strip()
    if not text:
        raise ValueError("datetime value must be non-empty")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _format_datetime(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def build_video_url(youtube_id: str) -> str:
    return f"https://youtu.be/{youtube_id}".strip()


def annotate_metadata(
    metadata_path: pathlib.Path,
    *,
    video_url: str | None = None,
    processing_started_at: str | None = None,
    processing_completed_at: str | None = None,
    processing_duration_seconds: int | None = None,
    dry_run: bool = False,
) -> bool:
    data = json.loads(metadata_path.read_text(encoding="utf-8"))

    changed = False
    youtube_id = str(data.get("youtube_id", "")).strip()

    if not video_url and youtube_id:
        video_url = build_video_url(youtube_id)
    if video_url:
        video_url = video_url.strip()
        if video_url and data.get("video_url") != video_url:
            data["video_url"] = video_url
            changed = True

    processing: dict[str, object]
    existing_processing = data.get("processing")
    if isinstance(existing_processing, dict):
        processing = dict(existing_processing)
    else:
        processing = {}

    started_value: str | None = None
    completed_value: str | None = None
    duration_value: int | None = processing_duration_seconds

    if processing_started_at:
        started_dt = _parse_datetime(processing_started_at)
        started_value = _format_datetime(started_dt)
    if processing_completed_at:
        completed_dt = _parse_datetime(processing_completed_at)
        completed_value = _format_datetime(completed_dt)
    if duration_value is None and started_value and completed_value:
        start_dt = datetime.fromisoformat(started_value)
        end_dt = datetime.fromisoformat(completed_value)
        delta = end_dt - start_dt
        duration_value = max(int(delta.total_seconds()), 0)

    if started_value and processing.get("started_at") != started_value:
        processing["started_at"] = started_value
        changed = True
    if completed_value and processing.get("completed_at") != completed_value:
        processing["completed_at"] = completed_value
        changed = True
    if duration_value is not None:
        if duration_value < 0:
            raise ValueError("processing duration cannot be negative")
        if processing.get("duration_seconds") != duration_value:
            processing["duration_seconds"] = duration_value
            changed = True

    if processing:
        if data.get("processing") != processing:
            data["processing"] = processing
            changed = True
    elif (
        "processing" in data
        and not processing_started_at
        and not processing_completed_at
        and processing_duration_seconds is None
    ):
        pass

    if changed and not dry_run:
        metadata_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    return changed


def _iter_metadata_paths(video_root: pathlib.Path) -> Iterable[pathlib.Path]:
    for path in sorted(video_root.glob("*/")):
        meta = path / METADATA_NAME
        if meta.exists():
            yield meta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Annotate published Futuroptimist videos with URLs and processing stats",
    )
    parser.add_argument(
        "--slug",
        action="append",
        default=None,
        help="Restrict updates to specific slugs (may be repeated)",
    )
    parser.add_argument(
        "--video-root",
        type=pathlib.Path,
        default=VIDEO_ROOT,
        help="Directory containing video_scripts folders",
    )
    parser.add_argument(
        "--video-url",
        default=None,
        help="Explicit video URL to record (defaults to https://youtu.be/<youtube_id>)",
    )
    parser.add_argument(
        "--processing-start",
        dest="processing_start",
        default=None,
        help="Processing start timestamp (ISO-8601)",
    )
    parser.add_argument(
        "--processing-end",
        dest="processing_end",
        default=None,
        help="Processing end timestamp (ISO-8601)",
    )
    parser.add_argument(
        "--processing-seconds",
        dest="processing_seconds",
        type=int,
        default=None,
        help="Processing duration in seconds",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without rewriting files",
    )
    args = parser.parse_args(argv)

    slugs = set(args.slug or []) or None
    video_root = args.video_root.resolve()

    updated = 0
    for meta_path in _iter_metadata_paths(video_root):
        if slugs and meta_path.parent.name not in slugs:
            continue
        changed = annotate_metadata(
            meta_path,
            video_url=args.video_url,
            processing_started_at=args.processing_start,
            processing_completed_at=args.processing_end,
            processing_duration_seconds=args.processing_seconds,
            dry_run=args.dry_run,
        )
        if changed:
            updated += 1
            if args.dry_run:
                print(f"Would update {meta_path}")
            else:
                print(f"Updated {meta_path}")

    if args.dry_run:
        print(f"Would update {updated} metadata file(s)")
    else:
        print(f"Updated {updated} metadata file(s)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
