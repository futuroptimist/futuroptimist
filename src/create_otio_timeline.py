"""Generate OpenTimelineIO timelines from converted Futuroptimist footage.

The Phase 7 roadmap in ``INSTRUCTIONS.md`` promises an OpenTimelineIO export so
rough cuts stay reproducible across editing apps.  This helper scans
``footage/<slug>/converted`` for video clips, arranges them in alphabetical
order, and writes ``<slug>.otio`` with Futuroptimist-specific metadata
recording the relative clip paths.  Durations default to one second per clip
(rounded to the nearest frame) to provide editable placeholders without
requiring ffprobe.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Iterable

import opentimelineio as otio


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}
DEFAULT_FRAME_RATE = 24.0
DEFAULT_DURATION_SECONDS = 1.0


def _resolve_path(path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else path.resolve()


def discover_video_clips(converted_dir: pathlib.Path) -> list[pathlib.Path]:
    """Return sorted video clips under ``converted_dir``."""

    if not converted_dir.is_dir():
        return []

    clips: list[pathlib.Path] = []
    for candidate in converted_dir.rglob("*"):
        if candidate.is_file() and candidate.suffix.lower() in VIDEO_EXTENSIONS:
            clips.append(candidate.resolve())
    clips.sort(key=lambda path: path.relative_to(converted_dir).as_posix())
    return clips


def _relative_repo_path(path: pathlib.Path, repo_root: pathlib.Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.name


def build_timeline(
    slug: str,
    clips: Iterable[pathlib.Path],
    *,
    converted_dir: pathlib.Path,
    repo_root: pathlib.Path,
    frame_rate: float = DEFAULT_FRAME_RATE,
    default_duration: float = DEFAULT_DURATION_SECONDS,
) -> otio.schema.Timeline:
    """Return an OpenTimelineIO timeline for ``slug``."""

    if frame_rate <= 0:
        raise ValueError("frame_rate must be positive")
    if default_duration <= 0:
        raise ValueError("default_duration must be positive")

    timeline = otio.schema.Timeline(name=slug)
    meta = timeline.metadata.setdefault("futuroptimist", {})
    meta.update(
        {
            "slug": slug,
            "frame_rate": frame_rate,
            "default_duration_seconds": default_duration,
            "clip_count": 0,
        }
    )

    track = otio.schema.Track(name="Video", kind=otio.schema.TrackKind.Video)
    timeline.tracks.append(track)

    for clip_path in clips:
        rel_converted = clip_path.relative_to(converted_dir).as_posix()
        clip = otio.schema.Clip(name=f"converted/{rel_converted}")
        clip.media_reference = otio.schema.ExternalReference(
            target_url=clip_path.as_uri()
        )
        clip.metadata["futuroptimist"] = {
            "relative_path": _relative_repo_path(clip_path, repo_root),
        }
        duration_frames = max(1, int(round(default_duration * frame_rate)))
        clip.source_range = otio.opentime.TimeRange(
            duration=otio.opentime.RationalTime(duration_frames, frame_rate)
        )
        track.append(clip)
        meta["clip_count"] += 1

    return timeline


def create_timeline(
    slug: str,
    *,
    footage_root: pathlib.Path = pathlib.Path("footage"),
    output_dir: pathlib.Path = pathlib.Path("timelines"),
    frame_rate: float = DEFAULT_FRAME_RATE,
    default_duration: float = DEFAULT_DURATION_SECONDS,
) -> pathlib.Path:
    """Write an OTIO timeline for ``slug`` and return the output path."""

    footage_root = _resolve_path(footage_root)
    output_dir = _resolve_path(output_dir)

    converted_dir = (footage_root / slug / "converted").resolve()
    clips = discover_video_clips(converted_dir)
    if not clips:
        raise ValueError(f"No video clips found under {converted_dir}")

    repo_root = footage_root.parent.resolve()
    timeline = build_timeline(
        slug,
        clips,
        converted_dir=converted_dir,
        repo_root=repo_root,
        frame_rate=frame_rate,
        default_duration=default_duration,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{slug}.otio"
    otio.adapters.write_to_file(timeline, str(output_path))
    return output_path


def _parse_args(argv: Iterable[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an OpenTimelineIO timeline for a Futuroptimist slug",
    )
    parser.add_argument("--slug", required=True, help="Slug like YYYYMMDD_slug")
    parser.add_argument(
        "--footage-root",
        type=pathlib.Path,
        default=pathlib.Path("footage"),
        help="Root directory containing footage",
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("timelines"),
        help="Directory to write OTIO timelines",
    )
    parser.add_argument(
        "--frame-rate",
        type=float,
        default=DEFAULT_FRAME_RATE,
        help="Frame rate used for placeholder durations",
    )
    parser.add_argument(
        "--default-duration",
        type=float,
        default=DEFAULT_DURATION_SECONDS,
        help="Seconds allocated to each clip placeholder",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        timeline_path = create_timeline(
            args.slug,
            footage_root=args.footage_root,
            output_dir=args.output_dir,
            frame_rate=args.frame_rate,
            default_duration=args.default_duration,
        )
    except Exception as exc:  # pragma: no cover - surface failure to CLI
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote timeline to {timeline_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
