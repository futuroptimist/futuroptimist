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
import shutil


# Image conversions (library-first)
EXTENSION_RULES: dict[str, tuple[str, list[str]]] = {
    # Prefer PNG to preserve color and avoid JPEG subsampling shifts
    ".heic": (".png", []),
    ".heif": (".png", []),
    ".dng": (".png", []),
    ".webp": (".png", []),
}

# Video conversions (ffmpeg)
VIDEO_RULES: dict[str, tuple[str, list[str]]] = {
    ".mov": (
        ".mp4",
        [
            "-map",
            "0",
            "-map",
            "-0:d?",
            "-map",
            "-0:s?",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
        ],
    ),
    ".avi": (
        ".mp4",
        [
            "-map",
            "0",
            "-map",
            "-0:d?",
            "-map",
            "-0:s?",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
        ],
    ),
    ".mkv": (
        ".mp4",
        [
            "-map",
            "0",
            "-map",
            "-0:d?",
            "-map",
            "-0:s?",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
        ],
    ),
    ".mts": (
        ".mp4",
        [
            "-map",
            "0",
            "-map",
            "-0:d?",
            "-map",
            "-0:s?",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
        ],
    ),
    ".m2ts": (
        ".mp4",
        [
            "-map",
            "0",
            "-map",
            "-0:d?",
            "-map",
            "-0:s?",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
        ],
    ),
    ".m4v": (
        ".mp4",
        [
            "-map",
            "0",
            "-map",
            "-0:d?",
            "-map",
            "-0:s?",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
        ],
    ),
    ".wmv": (
        ".mp4",
        [
            "-map",
            "0",
            "-map",
            "-0:d?",
            "-map",
            "-0:s?",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
        ],
    ),
    ".3gp": (
        ".mp4",
        [
            "-map",
            "0",
            "-map",
            "-0:d?",
            "-map",
            "-0:s?",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
        ],
    ),
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
    base: pathlib.Path,
    exts: Iterable[str] | None = None,
    include_video: bool = False,
    reencode_mp4: bool = False,
    only_slugs: set[str] | None = None,
    name_like: list[str] | None = None,
    mirror_compatible: bool = False,
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
        rule_map: dict[str, tuple[str, list[str]]] = EXTENSION_RULES.copy()
        if include_video:
            rule_map.update(VIDEO_RULES)
            if reencode_mp4:
                rule_map[".mp4"] = VIDEO_RULES[".mov"]  # use same args
        mirror_exts: set[str] = set()
        if mirror_compatible:
            mirror_exts = {".mp4", ".jpg", ".jpeg", ".png"}
        if ext not in rule_map and ext not in mirror_exts:
            continue
        slug_dir, rel_after_slug = find_slug_root(path, footage_root)
        if only_slugs is not None and slug_dir.name not in only_slugs:
            continue
        if name_like:
            full_name = str(path)
            if not any(s.lower() in full_name.lower() for s in name_like):
                continue
        out_base = slug_dir / "converted"
        if ext in rule_map:
            out_rel = (
                rel_after_slug.with_suffix(rule_map[ext][0])
                if rel_after_slug.name
                else pathlib.Path(path.stem + EXTENSION_RULES[ext][0])
            )
            dst = out_base / out_rel
            candidates.append(
                Conversion(src=path, dst=dst, extra_args=rule_map[ext][1])
            )
        else:
            # Mirror compatible file types without transcoding
            out_rel = rel_after_slug if rel_after_slug.name else pathlib.Path(path.name)
            dst = out_base / out_rel
            candidates.append(Conversion(src=path, dst=dst, extra_args=["__COPY__"]))
    return candidates


def ensure_parent_dirs(conv: Conversion) -> None:
    conv.dst.parent.mkdir(parents=True, exist_ok=True)


def build_ffmpeg_cmd(conv: Conversion, overwrite: bool) -> list[str]:
    # Standardize video stream mapping to avoid data/subtitle streams causing failures
    video_codec_args = [
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
    ]
    src_ext = conv.src.suffix.lower()
    is_video = src_ext in VIDEO_RULES
    args = []
    if is_video:
        args = ["-map", "0:v:0", "-map", "0:a:0?", "-sn", "-dn", *video_codec_args]
    else:
        args = list(conv.extra_args)
    cmd = [
        _resolve_ffmpeg(),
        "-y" if overwrite else "-n",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(conv.src),
        *args,
        str(conv.dst),
    ]
    return cmd


def _resolve_ffmpeg() -> str:
    """Return ffmpeg executable name or path.

    Attempts to use imageio-ffmpeg if available, otherwise falls back to 'ffmpeg'
    on PATH.
    """
    try:
        import imageio_ffmpeg

        path = imageio_ffmpeg.get_ffmpeg_exe()
        if path:
            return path
    except Exception:
        pass
    return "ffmpeg"


def _convert_with_ffmpeg(conv: Conversion, overwrite: bool) -> bool:
    cmd = build_ffmpeg_cmd(conv, overwrite=overwrite)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as exc:
        print(f"ffmpeg failed to start for {conv.src}: {exc}")
        return False
    if res.returncode != 0:
        print(f"ffmpeg error ({conv.src}): {res.stderr.strip()}")
        return False
    return True


def _apply_hdr_tonemap_if_needed(image):
    try:
        from PIL import Image

        # Heuristic: brighten very dark images that still have highlights
        im = image
        if im.mode != "RGB":
            im = im.convert("RGB")
        import numpy as _np

        arr = _np.asarray(im).astype("float32") / 255.0
        mean_luma = arr.mean()
        p99 = _np.quantile(arr, 0.99)
        # If overall dark and highlights are low, scale so 99th percentile reaches ~0.92
        if mean_luma < 0.3 or p99 < 0.8:
            target = 0.92
            scale = min(1.9, max(1.0, target / max(1e-6, p99)))
            arr = _np.clip(arr * scale, 0.0, 1.0)
            gamma = 0.95 if mean_luma < 0.22 else 1.0
            if gamma != 1.0:
                arr = _np.clip(arr**gamma, 0.0, 1.0)
            im = Image.fromarray((arr * 255.0 + 0.5).astype("uint8"), "RGB")
        return im
    except Exception:
        return image


CLI_HDR_TONEMAP = "auto"


def _convert_with_libraries(conv: Conversion) -> bool:
    ext = conv.src.suffix.lower()
    try:
        if ext in {".heic", ".heif"}:
            from PIL import Image, ImageOps, ImageCms
            import io

            # Use pillow-heif to read HEIF/HEIC images
            image = None
            icc = None
            try:
                from pillow_heif import read_heif

                heif = read_heif(str(conv.src), convert_hdr_to_8bit=True)
                image = Image.frombytes(heif.mode, heif.size, heif.data)
                icc = heif.info.get("icc_profile")
            except Exception:
                image = None
            if image is None:
                return False
            # Apply EXIF orientation
            try:
                image = ImageOps.exif_transpose(image)
            except Exception:
                pass
            # Convert from embedded profile to sRGB if present
            try:
                icc = icc or image.info.get("icc_profile")
                if icc:
                    src_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
                    dst_profile = ImageCms.createProfile("sRGB")
                    # Ensure 3-channel
                    if image.mode not in ("RGB", "RGBA"):
                        image = image.convert("RGB")
                    image = ImageCms.profileToProfile(
                        image, src_profile, dst_profile, outputMode="RGB"
                    )
                else:
                    image = image.convert("RGB")
            except Exception:
                image = image.convert("RGB")
            # Optional HDR tonemap
            if CLI_HDR_TONEMAP in {"on", "auto"}:
                if CLI_HDR_TONEMAP == "on":
                    image = _apply_hdr_tonemap_if_needed(image)
                else:  # auto
                    image = _apply_hdr_tonemap_if_needed(image)
            conv.dst.parent.mkdir(parents=True, exist_ok=True)
            # Embed sRGB ICC profile to avoid NLE desaturation
            try:
                srgb = ImageCms.createProfile("sRGB")
                bio = io.BytesIO()
                ImageCms.ImageCmsProfile(srgb).tobytesio(bio)
                image.save(str(conv.dst), icc_profile=bio.getvalue())
            except Exception:
                image.save(str(conv.dst))
            return True
        if ext == ".dng":
            import rawpy
            import numpy as _np
            from PIL import Image, ImageCms
            import io

            with rawpy.imread(str(conv.src)) as raw:
                rgb = raw.postprocess(
                    use_camera_wb=True,
                    no_auto_bright=True,
                    output_color=rawpy.ColorSpace.sRGB,
                    gamma=(2.222, 4.5),
                    output_bps=8,
                    demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD,
                )
            # Optional lift if very dark
            if CLI_HDR_TONEMAP in {"on", "auto"}:
                arr = rgb.astype("float32") / 255.0
                mean_luma = arr.mean()
                hi = _np.quantile(arr, 0.98)
                if mean_luma < 0.22 and hi > 0.7:
                    factor = min(1.8, max(1.0, 0.45 / max(1e-6, mean_luma)))
                    arr = _np.clip(arr * factor, 0.0, 1.0)
                    gamma = 0.9
                    arr = _np.clip(arr**gamma, 0.0, 1.0)
                    rgb = (arr * 255.0 + 0.5).astype("uint8")
            im = Image.fromarray(rgb, "RGB")
            conv.dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                srgb = ImageCms.createProfile("sRGB")
                bio = io.BytesIO()
                ImageCms.ImageCmsProfile(srgb).tobytesio(bio)
                im.save(str(conv.dst), icc_profile=bio.getvalue())
            except Exception:
                im.save(str(conv.dst))
            return True
        if ext == ".webp":
            from PIL import Image

            im = Image.open(str(conv.src))
            im = im.convert("RGBA" if im.mode in {"P", "LA"} else im.mode)
            conv.dst.parent.mkdir(parents=True, exist_ok=True)
            im.save(str(conv.dst))
            return True
    except Exception as exc:
        print(f"library conversion failed for {conv.src}: {exc}")
        return False
    return False


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
    parser.add_argument(
        "--only-ext",
        action="append",
        default=None,
        help="Limit conversions to these extensions (e.g., --only-ext .heic)",
    )
    parser.add_argument(
        "--hdr-tonemap",
        choices=["auto", "off", "on"],
        default="auto",
        help="Apply HDR tonemapping to HEIC/HEIF stills",
    )
    parser.add_argument(
        "--include-video",
        action="store_true",
        help="Include video format conversions to Premiere-friendly MP4",
    )
    parser.add_argument(
        "--reencode-mp4",
        action="store_true",
        help="Re-encode .mp4 sources instead of skipping",
    )
    parser.add_argument(
        "--slug",
        action="append",
        default=None,
        help="Limit to specific slug(s) like 20251001_indoor-aquariums-tour",
    )
    parser.add_argument(
        "--name-like",
        action="append",
        default=None,
        help="Only convert files whose path contains this substring (repeatable)",
    )
    parser.add_argument(
        "--mirror-compatible",
        action="store_true",
        help="Copy through compatible files (.mp4/.jpg/.jpeg/.png) to converted/",
    )
    args = parser.parse_args(argv)

    base = pathlib.Path(args.input)
    global CLI_HDR_TONEMAP
    CLI_HDR_TONEMAP = args.hdr_tonemap
    exts = set(e.lower() for e in args.only_ext) if args.only_ext else None
    conversions = plan_conversions(
        base,
        exts=exts,
        include_video=args.include_video,
        reencode_mp4=args.reencode_mp4,
        only_slugs=set(args.slug) if args.slug else None,
        name_like=args.name_like or None,
        mirror_compatible=args.mirror_compatible,
    )
    if args.dry_run:
        for c in conversions:
            print(f"{c.src} -> {c.dst}")
        print(f"Planned {len(conversions)} conversions")
        return 0

    failures = 0
    for conv in conversions:
        ensure_parent_dirs(conv)
        # Prefer robust library decoding for images; fall back to ffmpeg
        if conv.extra_args == ["__COPY__"]:
            try:
                if args.force or not conv.dst.exists():
                    shutil.copy2(conv.src, conv.dst)
                ok = True
            except Exception as exc:
                print(f"copy failed for {conv.src}: {exc}")
                ok = False
        else:
            ok = _convert_with_libraries(conv)
        if not ok:
            ok = _convert_with_ffmpeg(conv, overwrite=args.force)
        if not ok:
            failures += 1
    if failures:
        print(f"Completed with {failures} failures")
        return 1
    print(f"Converted {len(conversions)} files")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
