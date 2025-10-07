"""Build a JSON index of `[NARRATOR]` lines from video scripts.

This lightweight exporter powers the "Next Steps" roadmap item in
INSTRUCTIONS.md that promised a starter RAG index. Each segment records the
slug, YouTube metadata, segment number, text, and optional timestamps so the
output can be embedded or searched.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Iterable, List

SCRIPT_NAME = "script.md"
METADATA_NAME = "metadata.json"
DEFAULT_OUTPUT = pathlib.Path("data/script_segments.json")

_NARRATOR_RE = re.compile(
    r"^\[NARRATOR\]:\s*(?P<text>.*?)(?:\s*<!--\s*(?P<start>[0-9:,]+)\s*->\s*(?P<end>[0-9:,]+)\s*-->)?\s*$"
)


def _iter_script_dirs(video_root: pathlib.Path) -> Iterable[pathlib.Path]:
    for path in sorted(video_root.glob("*/")):
        if path.is_dir() and (path / METADATA_NAME).exists():
            yield path


def _load_metadata(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:  # pragma: no cover - caller guards file existence
        return {}


def _extract_segments(script_path: pathlib.Path) -> List[dict]:
    segments: List[dict] = []
    if not script_path.exists():
        return segments
    for line in script_path.read_text(encoding="utf-8").splitlines():
        match = _NARRATOR_RE.match(line.strip())
        if not match:
            continue
        text = match.group("text").strip()
        if not text:
            continue
        segments.append(
            {
                "text": text,
                "start": match.group("start"),
                "end": match.group("end"),
            }
        )
    return segments


def build_index(
    *,
    video_root: pathlib.Path,
    output_path: pathlib.Path | None = None,
) -> List[dict]:
    """Return a list of script segments and optionally write them to JSON."""

    video_root = video_root.resolve()
    records: List[dict] = []
    for script_dir in _iter_script_dirs(video_root):
        metadata = _load_metadata(script_dir / METADATA_NAME)
        slug = script_dir.name
        youtube_id = metadata.get("youtube_id")
        title = metadata.get("title")
        publish_date = metadata.get("publish_date")
        script_path = script_dir / SCRIPT_NAME
        segments = _extract_segments(script_path)
        for idx, segment in enumerate(segments, start=1):
            records.append(
                {
                    "slug": slug,
                    "youtube_id": youtube_id,
                    "title": title,
                    "publish_date": publish_date,
                    "segment": idx,
                    "text": segment["text"],
                    "start": segment.get("start"),
                    "end": segment.get("end"),
                }
            )
    if output_path is None:
        output_path = DEFAULT_OUTPUT
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Index Futuroptimist scripts for retrieval and embeddings",
    )
    parser.add_argument(
        "--video-root",
        default="video_scripts",
        type=pathlib.Path,
        help="Directory containing video script folders",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=None,
        help=f"Destination JSON path (defaults to {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args(argv)

    records = build_index(video_root=args.video_root, output_path=args.output)
    print(f"Indexed {len(records)} segment(s)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
