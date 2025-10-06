"""Generate Markdown scripts from downloaded SRT transcripts.

Iterates through ``video_scripts/*/metadata.json`` files, locates their
transcripts under ``subtitles/`` (preferring the ``transcript_file`` value when
present and falling back to ``subtitles/<youtube_id>.srt``), and writes a
``script.md`` file for each folder using :mod:`src.srt_to_markdown`.

Existing scripts are left untouched unless ``--force`` is provided.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Iterable

from src import srt_to_markdown


def _resolve_transcript(
    repo_root: pathlib.Path,
    subtitles_root: pathlib.Path,
    transcript_ref: str,
    youtube_id: str,
) -> pathlib.Path | None:
    candidates: list[pathlib.Path] = []
    if transcript_ref:
        ref_path = repo_root / transcript_ref
        candidates.append(ref_path)
    if youtube_id:
        candidates.append(subtitles_root / f"{youtube_id}.srt")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _load_metadata_paths(
    video_root: pathlib.Path, slugs: Iterable[str] | None
) -> list[pathlib.Path]:
    allowed = set(slugs) if slugs is not None else None
    paths: list[pathlib.Path] = []
    for meta_path in sorted(video_root.glob("*/metadata.json")):
        slug = meta_path.parent.name
        if allowed is not None and slug not in allowed:
            continue
        paths.append(meta_path)
    return paths


def generate_scripts(
    *,
    video_root: pathlib.Path,
    subtitles_root: pathlib.Path,
    force: bool = False,
    slugs: Iterable[str] | None = None,
    dry_run: bool = False,
) -> dict[str, list[pathlib.Path]]:
    """Generate scripts from subtitles and return a summary of the run."""

    video_root = video_root.resolve()
    subtitles_root = subtitles_root.resolve()
    repo_root = video_root.parent

    written: list[pathlib.Path] = []
    skipped: list[pathlib.Path] = []
    missing: list[pathlib.Path] = []

    for meta_path in _load_metadata_paths(video_root, slugs):
        slug_dir = meta_path.parent
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        youtube_id = str(data.get("youtube_id", "")).strip()
        transcript_ref = str(data.get("transcript_file", "")).strip()
        transcript_path = _resolve_transcript(
            repo_root, subtitles_root, transcript_ref, youtube_id
        )
        if transcript_path is None:
            missing.append(meta_path)
            continue
        script_path = slug_dir / "script.md"
        if script_path.exists() and not force:
            skipped.append(script_path)
            continue

        entries = srt_to_markdown.parse_srt(transcript_path)
        title = str(data.get("title") or slug_dir.name.replace("_", " ").title())
        markdown = srt_to_markdown.to_markdown(entries, title, youtube_id)
        if not markdown.endswith("\n"):
            markdown += "\n"
        if not markdown.endswith("\n\n"):
            markdown += "\n"
        if dry_run:
            written.append(script_path)
            continue
        script_path.write_text(markdown, encoding="utf-8")
        written.append(script_path)

    return {"written": written, "skipped": skipped, "missing": missing}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate script.md files from subtitles",
    )
    parser.add_argument(
        "--video-root",
        default="video_scripts",
        help="Directory containing video script folders",
    )
    parser.add_argument(
        "--subtitles-root",
        default="subtitles",
        help="Directory containing downloaded SRT files",
    )
    parser.add_argument(
        "--slug",
        action="append",
        default=None,
        help="Limit to specific slug(s)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing script.md files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview generated files without writing",
    )
    args = parser.parse_args(argv)

    video_root = pathlib.Path(args.video_root)
    subtitles_root = pathlib.Path(args.subtitles_root)

    result = generate_scripts(
        video_root=video_root,
        subtitles_root=subtitles_root,
        force=args.force,
        slugs=args.slug,
        dry_run=args.dry_run,
    )

    for path in result["written"]:
        print(f"Wrote {path}")
    for path in result["skipped"]:
        print(f"Skipped existing {path}")
    for meta in result["missing"]:
        print(f"Missing transcript for {meta}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
