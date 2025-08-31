"""Generate rough image descriptions for footage images into a markdown file.

This script currently creates a placeholder list of images with filenames and
basic metadata (size, mtime). Hook points are provided to integrate a real
vision model (e.g., CLIP/LAION/OpenCLIP or cloud APIs) when available.
"""

from __future__ import annotations

import argparse
import mimetypes
import pathlib
from datetime import datetime, timezone


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".dng", ".webp"}


def is_image(path: pathlib.Path) -> bool:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        return True
    # Fallback using mimetypes
    mt, _ = mimetypes.guess_type(path.name)
    return bool(mt and mt.startswith("image/"))


def describe_images(root: pathlib.Path) -> list[dict]:
    entries: list[dict] = []
    for p in root.rglob("*"):
        if p.is_file() and is_image(p):
            stat = p.stat()
            mtime = (
                datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
            entries.append(
                {
                    "path": p.as_posix(),
                    "size": stat.st_size,
                    "mtime": mtime,
                    # Placeholder. Integrate a real model here.
                    "description": "",
                }
            )
    entries.sort(key=lambda e: e["path"])
    return entries


def write_markdown(entries: list[dict], out_path: pathlib.Path) -> None:
    lines = ["# Image Descriptions", ""]
    for e in entries:
        size_kb = e["size"] / 1024.0
        desc = e["description"] or "(description pending)"
        lines.append(f"- {e['path']} — {size_kb:.1f} KB — {e['mtime']}\n  - {desc}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate image descriptions markdown")
    parser.add_argument(
        "directory",
        nargs="?",
        default="footage",
        help="Root directory to scan for images",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="image_descriptions.md",
        help="Markdown file to write",
    )
    args = parser.parse_args(argv)
    root = pathlib.Path(args.directory)
    entries = describe_images(root)
    write_markdown(entries, pathlib.Path(args.output))
    print(f"Wrote {args.output} with {len(entries)} images")


if __name__ == "__main__":
    main()
