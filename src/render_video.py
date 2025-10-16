"""Assemble a rough-cut video from converted footage with optional captions.

This fulfils the Phase 7 render milestone in ``INSTRUCTIONS.md`` by wiring up a
minimal FFmpeg pipeline. The helper concatenates ``footage/<slug>/converted``
clips (optionally ordered via a selects file) and can burn in subtitle tracks
referenced by ``metadata.json``. The resulting file lands in ``dist/`` so it can
flow into the publishing step once thumbnails and descriptions are finalised.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shlex
import shutil
import subprocess
import tempfile
from typing import Iterable, Sequence

from .report_funnel import _normalize_select_path, _read_selects


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_DIST = REPO_ROOT / "dist"
DEFAULT_FOOTAGE = REPO_ROOT / "footage"
DEFAULT_VIDEO_ROOT = REPO_ROOT / "video_scripts"


class RenderError(RuntimeError):
    """Raised when rendering cannot proceed."""


def _iter_converted_videos(converted_root: pathlib.Path) -> list[pathlib.Path]:
    return sorted(converted_root.glob("*.mp4"))


def _load_metadata(slug: str, video_root: pathlib.Path) -> dict[str, object]:
    meta_path = video_root / slug / "metadata.json"
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _resolve_captions(
    slug: str,
    *,
    explicit: pathlib.Path | None,
    video_root: pathlib.Path,
) -> pathlib.Path | None:
    if explicit is not None:
        path = explicit if explicit.is_absolute() else (REPO_ROOT / explicit)
        return path if path.exists() else None
    metadata = _load_metadata(slug, video_root)
    transcript = str(metadata.get("transcript_file") or "").strip()
    if not transcript:
        return None
    transcript_path = pathlib.Path(transcript)
    candidates: list[pathlib.Path] = []
    if transcript_path.is_absolute():
        candidates.append(transcript_path)
    else:
        repo_candidate = (REPO_ROOT / transcript_path).resolve()
        candidates.append(repo_candidate)
        candidates.append((video_root / slug / transcript_path).resolve())
        candidates.append((video_root / transcript_path).resolve())

    seen: set[pathlib.Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists():
            return candidate
    return None


def _collect_segments(
    slug: str,
    *,
    footage_root: pathlib.Path,
    video_root: pathlib.Path,
    selects_file: pathlib.Path | None,
) -> list[pathlib.Path]:
    slug_dir = footage_root / slug
    converted_root = slug_dir / "converted"
    if not converted_root.is_dir():
        raise RenderError(f"Converted footage not found for {slug}")

    segments: list[pathlib.Path] = []
    seen: set[pathlib.Path] = set()
    if selects_file and selects_file.exists():
        entries = _read_selects(selects_file.read_text(encoding="utf-8").splitlines())
        for entry in entries:
            normalized = _normalize_select_path(
                converted_root.resolve(), REPO_ROOT.resolve(), slug, entry
            )
            if normalized is None:
                continue
            resolved, _ = normalized
            if resolved.suffix.lower() != ".mp4" or not resolved.exists():
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            segments.append(resolved)
    else:
        for path in _iter_converted_videos(converted_root):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            segments.append(resolved)

    if not segments:
        raise RenderError(f"No converted MP4 clips found for {slug}")
    return segments


def _quote_for_concat(path: pathlib.Path) -> str:
    escaped = str(path).replace("'", "'\\''")
    return f"file '{escaped}'"


def _build_ffmpeg_command(
    *,
    inputs: Sequence[pathlib.Path],
    output: pathlib.Path,
    captions: pathlib.Path | None,
    overwrite: bool,
    concat_file: pathlib.Path,
) -> list[str]:
    command: list[str] = ["ffmpeg"]
    command.append("-y" if overwrite else "-n")
    command.extend(["-f", "concat", "-safe", "0", "-i", str(concat_file)])
    if captions is not None:
        command.extend(["-vf", f"subtitles={shlex.quote(str(captions))}"])
    command.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    return command


def render_video(
    slug: str,
    *,
    footage_root: pathlib.Path = DEFAULT_FOOTAGE,
    video_root: pathlib.Path = DEFAULT_VIDEO_ROOT,
    dist_root: pathlib.Path = DEFAULT_DIST,
    selects_file: pathlib.Path | None = None,
    captions: pathlib.Path | None = None,
    output: pathlib.Path | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
) -> pathlib.Path:
    if shutil.which("ffmpeg") is None:
        raise RenderError("ffmpeg executable not found in PATH")

    segments = _collect_segments(
        slug,
        footage_root=footage_root,
        video_root=video_root,
        selects_file=selects_file,
    )

    captions_path = _resolve_captions(
        slug,
        explicit=captions,
        video_root=video_root,
    )

    output_path = output
    if output_path is None:
        output_path = dist_root / f"{slug}.mp4"
    if not output_path.is_absolute():
        output_path = (REPO_ROOT / output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as concat:
        concat_path = pathlib.Path(concat.name)
        for clip in segments:
            concat.write(_quote_for_concat(clip) + "\n")

    try:
        command = _build_ffmpeg_command(
            inputs=segments,
            output=output_path,
            captions=captions_path,
            overwrite=overwrite,
            concat_file=concat_path,
        )
        if dry_run:
            print(" ".join(shlex.quote(part) for part in command))
            print(f"Dry run: would write {output_path}")
        else:
            subprocess.run(command, check=True)
            print(f"Wrote {output_path}")
    finally:
        concat_path.unlink(missing_ok=True)

    return output_path


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Concatenate converted footage into a rough-cut MP4",
    )
    parser.add_argument("slug", help="Slug like YYYYMMDD_demo")
    parser.add_argument(
        "--footage-root",
        default=str(DEFAULT_FOOTAGE),
        help="Directory containing footage/<slug> folders",
    )
    parser.add_argument(
        "--video-root",
        default=str(DEFAULT_VIDEO_ROOT),
        help="Directory containing video_scripts/<slug> folders",
    )
    parser.add_argument(
        "--dist-root",
        default=str(DEFAULT_DIST),
        help="Directory to place rendered MP4s",
    )
    parser.add_argument(
        "--selects-file",
        type=pathlib.Path,
        default=None,
        help="Optional selects.txt to determine clip order",
    )
    parser.add_argument(
        "--captions",
        type=pathlib.Path,
        default=None,
        help="Optional subtitle file to burn in",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=None,
        help="Explicit output path (defaults to dist/<slug>.mp4)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing outputs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print ffmpeg command without executing",
    )
    args = parser.parse_args(argv)

    try:
        render_video(
            args.slug,
            footage_root=pathlib.Path(args.footage_root),
            video_root=pathlib.Path(args.video_root),
            dist_root=pathlib.Path(args.dist_root),
            selects_file=args.selects_file,
            captions=args.captions,
            output=args.output,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
        )
    except RenderError as exc:
        parser.error(str(exc))
    except subprocess.CalledProcessError as exc:  # pragma: no cover - passthrough
        parser.error(f"ffmpeg exited with status {exc.returncode}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
