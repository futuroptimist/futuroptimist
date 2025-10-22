from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import tempfile
from typing import Iterable


def discover_clips(converted_dir: pathlib.Path) -> list[pathlib.Path]:
    """Return sorted MP4 clips under ``converted_dir``."""

    if not converted_dir.is_dir():
        return []
    clips: list[pathlib.Path] = []
    for candidate in converted_dir.rglob("*"):
        if candidate.is_file() and candidate.suffix.lower() == ".mp4":
            clips.append(candidate.resolve())
    clips.sort()
    return clips


def _ffmpeg_concat_line(path: pathlib.Path) -> str:
    escaped = path.as_posix().replace("'", "'\\''")
    return f"file '{escaped}'"


def _load_metadata(slug: str, repo_root: pathlib.Path) -> dict:
    metadata_path = repo_root / "video_scripts" / slug / "metadata.json"
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def resolve_captions(
    slug: str,
    repo_root: pathlib.Path,
    explicit: pathlib.Path | None,
) -> pathlib.Path | None:
    """Return an absolute captions path for ``slug`` if one exists."""

    candidates: list[pathlib.Path] = []
    if explicit is not None:
        candidates.append(explicit if explicit.is_absolute() else repo_root / explicit)

    metadata = _load_metadata(slug, repo_root)
    transcript_ref = str(metadata.get("transcript_file", "")).strip()
    if transcript_ref:
        path = pathlib.Path(transcript_ref)
        candidates.append(path if path.is_absolute() else repo_root / path)

    youtube_id = str(metadata.get("youtube_id", "")).strip()
    if youtube_id:
        candidates.append(repo_root / "subtitles" / f"{youtube_id}.srt")

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def _escape_subtitles_path(path: pathlib.Path) -> str:
    text = path.as_posix().replace("\\", "\\\\").replace(":", "\\:")
    text = text.replace("'", "\\'")
    return f"subtitles={text}"


def render_slug(
    slug: str,
    *,
    footage_root: pathlib.Path,
    output_dir: pathlib.Path,
    captions: pathlib.Path | None = None,
    ffmpeg: str = "ffmpeg",
    dry_run: bool = False,
) -> pathlib.Path:
    """Render ``slug`` into ``output_dir`` using ffmpeg concat."""

    slug_dir = footage_root / slug
    converted_dir = slug_dir / "converted"
    if not converted_dir.is_dir():
        raise FileNotFoundError(f"Converted footage directory missing: {converted_dir}")

    clips = discover_clips(converted_dir)
    if not clips:
        raise ValueError(f"No MP4 clips found under {converted_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{slug}.mp4"

    with tempfile.TemporaryDirectory() as temp_dir:
        list_path = pathlib.Path(temp_dir) / "inputs.txt"
        list_path.write_text(
            "\n".join(_ffmpeg_concat_line(path) for path in clips) + "\n",
            encoding="utf-8",
        )

        command: list[str] = [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
        ]
        if captions is not None:
            command.extend(["-vf", _escape_subtitles_path(captions)])
        command.append(str(output_path))

        if dry_run:
            print("Dry run: ", " ".join(command))
            return output_path

        subprocess.run(command, check=True)

    print(f"Rendered {slug} to {output_path}")
    return output_path


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render a Futuroptimist rough cut from converted footage",
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
        default=pathlib.Path("dist"),
        help="Directory to write rendered videos",
    )
    parser.add_argument(
        "--repo-root",
        type=pathlib.Path,
        default=None,
        help="Repository root (defaults to parent of footage root)",
    )
    parser.add_argument(
        "--captions",
        type=pathlib.Path,
        default=None,
        help="Optional path to subtitles file for burn-in",
    )
    parser.add_argument(
        "--ffmpeg",
        default="ffmpeg",
        help="ffmpeg executable (defaults to 'ffmpeg')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the ffmpeg command without running it",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    footage_root = args.footage_root.resolve()
    repo_root = args.repo_root.resolve() if args.repo_root else footage_root.parent
    captions_path = None
    if args.captions:
        captions_path = (
            args.captions if args.captions.is_absolute() else repo_root / args.captions
        )
        if not captions_path.exists():
            captions_path = None
    if captions_path is None:
        captions_path = resolve_captions(args.slug, repo_root, None)

    try:
        render_slug(
            args.slug,
            footage_root=footage_root,
            output_dir=args.output_dir.resolve(),
            captions=captions_path,
            ffmpeg=args.ffmpeg,
            dry_run=args.dry_run,
        )
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))
        return 2  # pragma: no cover
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
