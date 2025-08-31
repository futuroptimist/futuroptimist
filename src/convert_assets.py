"""Convert incompatible footage assets into Premiere-friendly formats.

Usage:
  python src/convert_assets.py [INPUT_DIR] [-o OUTPUT_BASE] [--force] [--dry-run]

Defaults:
- INPUT_DIR defaults to 'footage'
- OUTPUT_BASE is computed per video slug: 'footage/<slug>/converted'

Rules (ext-based heuristics):
- .heic/.heif → .jpg (ffmpeg)
- .dng        → .jpg (ffmpeg)
- .webp       → .png (ffmpeg)

Originals are preserved; converted files are written under 'converted/'.
The relative path under 'converted/' mirrors the structure after the slug,
with an 'originals' segment stripped if present.
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
from dataclasses import dataclass
from typing import Iterable


EXTENSION_RULES: dict[str, tuple[str, list[str]]] = {
    ".heic": (".jpg", ["-q:v", "2"]),
    ".heif": (".jpg", ["-q:v", "2"]),
    ".dng": (".jpg", ["-q:v", "2"]),
    ".webp": (".png", []),
}


@dataclass
class Conversion:
    src: pathlib.Path
    dst: pathlib.Path
    extra_args: list[str]


def find_slug_root(
    path: pathlib.Path, footage_root: pathlib.Path
) -> tuple[pathlib.Path, pathlib.Path]:
    """Return (slug_dir, rel_after_slug) for a path under footage_root.

    rel_after_slug excludes the slug segment and optionally the 'originals'
    segment if present as the immediate child of the slug.
    """
    rel = path.relative_to(footage_root)
    parts = rel.parts
    if not parts:
        return footage_root, pathlib.Path()
    slug = parts[0]
    rest = pathlib.Path(*parts[1:])
    if len(parts) >= 2 and parts[1].lower() == "originals":
        rest = pathlib.Path(*parts[2:])
    return footage_root / slug, rest


def plan_conversions(
    base: pathlib.Path, exts: Iterable[str] | None = None
) -> list[Conversion]:
    root = base
    footage_root = base
    candidates: list[Conversion] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if exts is not None and ext not in exts:
            continue
        if ext not in EXTENSION_RULES:
            continue
        slug_dir, rel_after_slug = find_slug_root(path, footage_root)
        out_base = slug_dir / "converted"
        out_rel = (
            rel_after_slug.with_suffix(EXTENSION_RULES[ext][0])
            if rel_after_slug.name
            else pathlib.Path(path.stem + EXTENSION_RULES[ext][0])
        )
        dst = out_base / out_rel
        candidates.append(
            Conversion(src=path, dst=dst, extra_args=EXTENSION_RULES[ext][1])
        )
    return candidates


def ensure_parent_dirs(conv: Conversion) -> None:
    conv.dst.parent.mkdir(parents=True, exist_ok=True)


def build_ffmpeg_cmd(conv: Conversion, overwrite: bool) -> list[str]:
    cmd = [
        "ffmpeg",
        "-y" if overwrite else "-n",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(conv.src),
        *conv.extra_args,
        str(conv.dst),
    ]
    return cmd


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert incompatible assets with ffmpeg"
    )
    parser.add_argument(
        "input", nargs="?", default="footage", help="Input directory to scan"
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Ignored; output is computed per slug under converted/",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing outputs"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Only print planned conversions"
    )
    args = parser.parse_args(argv)

    base = pathlib.Path(args.input)
    conversions = plan_conversions(base)
    if args.dry_run:
        for c in conversions:
            print(f"{c.src} -> {c.dst}")
        print(f"Planned {len(conversions)} conversions")
        return 0

    failures = 0
    for conv in conversions:
        ensure_parent_dirs(conv)
        cmd = build_ffmpeg_cmd(conv, overwrite=args.force)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
        except OSError as exc:
            print(f"ffmpeg failed to start for {conv.src}: {exc}")
            failures += 1
            continue
        if res.returncode != 0:
            print(f"ffmpeg error ({conv.src}): {res.stderr.strip()}")
            failures += 1
    if failures:
        print(f"Completed with {failures} failures")
        return 1
    print(f"Converted {len(conversions)} files")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
