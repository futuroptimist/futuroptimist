"""Export the opening hook from each Futuroptimist script.

This fulfils the Phase 4 "Creative Toolkit" roadmap item in INSTRUCTIONS.md
that promised a prompt library for hook/headline generation. The exporter scans
`video_scripts/*/script.md`, captures the first `[NARRATOR]` line (and optional
timestamp comment), enriches it with metadata, and writes the collection to
`data/script_hooks.json` for downstream prompt builders.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Iterable


SCRIPT_NAME = "script.md"
METADATA_NAME = "metadata.json"
DEFAULT_OUTPUT = pathlib.Path("data/script_hooks.json")

_HOOK_RE = re.compile(
    r"^\[NARRATOR\]:\s*(?P<text>.*?)(?:\s*<!--\s*(?P<start>[0-9:,]+)\s*->\s*(?P<end>[0-9:,]+)\s*-->)?\s*$"
)


def _iter_script_dirs(video_root: pathlib.Path) -> Iterable[pathlib.Path]:
    for path in sorted(video_root.glob("*/")):
        if path.is_dir() and (path / METADATA_NAME).exists():
            yield path


def _load_metadata(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:  # pragma: no cover - guarded by caller
        return {}


def _extract_hook(script_path: pathlib.Path) -> dict | None:
    if not script_path.exists():
        return None
    for raw in script_path.read_text(encoding="utf-8").splitlines():
        match = _HOOK_RE.match(raw.strip())
        if not match:
            continue
        text = match.group("text").strip()
        if not text:
            continue
        return {
            "text": text,
            "start": match.group("start"),
            "end": match.group("end"),
        }
    return None


def build_hooks_index(
    *,
    video_root: pathlib.Path,
    output_path: pathlib.Path | None = None,
) -> list[dict]:
    """Return hook records and optionally write them to JSON."""

    video_root = video_root.resolve()
    records: list[dict] = []
    for script_dir in _iter_script_dirs(video_root):
        metadata = _load_metadata(script_dir / METADATA_NAME)
        hook = _extract_hook(script_dir / SCRIPT_NAME)
        if hook is None:
            continue
        records.append(
            {
                "slug": script_dir.name,
                "youtube_id": metadata.get("youtube_id"),
                "title": metadata.get("title"),
                "publish_date": metadata.get("publish_date"),
                "text": hook["text"],
                "start": hook.get("start"),
                "end": hook.get("end"),
            }
        )
    records.sort(key=lambda r: r["slug"])

    if output_path is None:
        output_path = DEFAULT_OUTPUT
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export opening hook lines from Futuroptimist scripts",
    )
    parser.add_argument(
        "--video-root",
        type=pathlib.Path,
        default="video_scripts",
        help="Directory containing video script folders",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=None,
        help=f"Destination JSON path (defaults to {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args(argv)

    hooks = build_hooks_index(video_root=args.video_root, output_path=args.output)
    print(f"Indexed {len(hooks)} hook(s)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
