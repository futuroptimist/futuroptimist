"""Generate heuristic image descriptions for footage assets.

The script scans a footage directory, gathers lightweight metadata, and now
generates a short natural-language summary for each image by sampling colours,
estimating brightness, and reporting the orientation. This keeps
``image_descriptions.md`` useful even without an external vision model while
leaving room to swap in richer captions later.
"""

from __future__ import annotations

import argparse
import colorsys
import mimetypes
import pathlib
from datetime import datetime, timezone

from PIL import Image, ImageStat


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".dng", ".webp"}


def _register_heif() -> None:
    try:
        from pillow_heif import register_heif_opener  # type: ignore

        register_heif_opener()
    except Exception:
        pass


_register_heif()


def is_image(path: pathlib.Path) -> bool:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        return True
    # Fallback using mimetypes
    mt, _ = mimetypes.guess_type(path.name)
    return bool(mt and mt.startswith("image/"))


def _load_image_stats(
    path: pathlib.Path,
) -> tuple[int, int, tuple[float, float, float]]:
    with Image.open(path) as image:
        width, height = image.size
        preview = image.copy()
        preview.thumbnail((96, 96))
        stat = ImageStat.Stat(preview.convert("RGB"))
    return width, height, (stat.mean[0], stat.mean[1], stat.mean[2])


def _raw_dimensions(path: pathlib.Path) -> tuple[int, int] | None:
    if path.suffix.lower() != ".dng":
        return None
    try:
        import rawpy  # type: ignore

        with rawpy.imread(str(path)) as raw:
            return int(raw.sizes.width), int(raw.sizes.height)
    except Exception:
        return None


def _orientation(width: int | None, height: int | None) -> str:
    if not width or not height:
        return "framed"
    ratio = width / height
    if ratio >= 1.15:
        return "landscape"
    if ratio <= 0.87:
        return "portrait"
    return "square"


def _color_summary(mean: tuple[float, float, float] | None) -> tuple[str, str]:
    if mean is None:
        return "Textured", "neutral tones"
    r, g, b = (channel / 255.0 for channel in mean)
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    brightness = (
        "Dim" if lightness < 0.35 else "Vivid" if lightness > 0.65 else "Balanced"
    )
    if saturation < 0.12:
        return brightness, "neutral tones"
    hue = (hue * 360.0) % 360.0
    palette_map = [
        (30, "warm red tones"),
        (60, "orange highlights"),
        (90, "golden yellow tones"),
        (150, "fresh green tones"),
        (210, "cool teal tones"),
        (270, "ocean blue tones"),
        (330, "purple accents"),
        (360, "warm red tones"),
    ]
    for boundary, label in palette_map:
        if hue < boundary:
            return brightness, label
    return brightness, "neutral tones"


def _summarise_image(path: pathlib.Path) -> str:
    width: int | None = None
    height: int | None = None
    mean: tuple[float, float, float] | None = None
    try:
        width, height, mean = _load_image_stats(path)
    except Exception:
        dims = _raw_dimensions(path)
        if dims:
            width, height = dims
    orientation = _orientation(width, height)
    brightness, palette = _color_summary(mean)
    base = (
        f"{brightness} {orientation} image"
        if orientation != "framed"
        else f"{brightness} image"
    )
    description = f"{base} with {palette}" if palette else base
    details: list[str] = []
    ext = path.suffix.lstrip(".")
    if ext:
        details.append(ext.upper())
    if width and height:
        details.append(f"{width}x{height}")
    if details:
        description = f"{description} ({', '.join(details)})"
    return description


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
                    "description": _summarise_image(p),
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
