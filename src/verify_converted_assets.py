"""Verify converted assets match originals and flag quality issues.

Checks for:
- Missing converted outputs for target image types (HEIC/HEIF/DNG/WEBP)
- Missing converted outputs for target video types (MOV/MKV/AVI/MTS/M2TS/M4V/WMV/3GP)
- Dimension and aspect-ratio mismatches (images only)
- Likely grayscale conversions (images only)

Writes a JSON report if requested and exits non-zero on failures.
"""

from __future__ import annotations

import argparse
import pathlib
from PIL import Image
import json
import numpy as np

CONVERT_IMAGE_EXTS = {".heic", ".heif", ".dng", ".webp"}
CONVERT_VIDEO_EXTS = {".mov", ".mkv", ".avi", ".mts", ".m2ts", ".m4v", ".wmv", ".3gp"}
# Skip only already-compatible or non-media files; video inputs are handled above
SKIP_ORIGINAL_EXTS = {".mp4", ".mpg", ".mpeg", ".txt", ".md", ".json"}


def _register_heif():
    try:
        from pillow_heif import register_heif_opener  # type: ignore

        register_heif_opener()
    except Exception:
        pass


_register_heif()


def image_size(path: pathlib.Path) -> tuple[int, int] | None:
    ext = path.suffix.lower()
    if ext == ".dng":
        try:
            import rawpy  # type: ignore

            with rawpy.imread(str(path)) as raw:
                return int(raw.sizes.width), int(raw.sizes.height)
        except Exception:
            pass
    try:
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def is_likely_grayscale(
    path: pathlib.Path, sample_max: int = 512, tol: int = 2, frac: float = 0.98
) -> bool:
    """Return True if image appears grayscale: most pixels have nearly equal RGB channels.

    - sample_max: resize longest side to this many pixels for speed
    - tol: per-channel absolute difference tolerance (0-255)
    - frac: fraction of pixels that must meet grayscale condition to flag
    """
    try:
        with Image.open(path) as im:
            if im.mode not in ("RGB", "RGBA", "P", "L"):
                im = im.convert("RGB")
            if im.mode == "P":
                im = im.convert("RGB")
            if im.mode == "RGBA":
                im = im.convert("RGB")
            w, h = im.size
            scale = max(w, h)
            if scale > sample_max:
                if w >= h:
                    new_w = sample_max
                    new_h = max(1, int(h * sample_max / w))
                else:
                    new_h = sample_max
                    new_w = max(1, int(w * sample_max / h))
                im = im.resize((new_w, new_h))
            arr = np.asarray(im)
            if arr.ndim != 3 or arr.shape[2] < 3:
                return True
            r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
            close_rg = np.abs(r.astype(np.int16) - g.astype(np.int16)) <= tol
            close_rb = np.abs(r.astype(np.int16) - b.astype(np.int16)) <= tol
            close_gb = np.abs(g.astype(np.int16) - b.astype(np.int16)) <= tol
            close_all = close_rg & close_rb & close_gb
            return close_all.mean() >= frac
    except Exception:
        return False


def verify_slug(slug_dir: pathlib.Path, tolerance: float = 0.01) -> list[str]:
    originals = slug_dir / "originals"
    converted = slug_dir / "converted"
    if not originals.is_dir() or not converted.is_dir():
        return []
    errors: list[str] = []
    missing: list[str] = []
    mismatched: list[str] = []
    grayscale: list[str] = []
    for src in originals.rglob("*"):
        if not src.is_file():
            continue
        ext = src.suffix.lower()
        # Videos: ensure converted .mp4 exists
        if ext in CONVERT_VIDEO_EXTS:
            rel = src.relative_to(originals)
            dst = converted / rel.with_suffix(".mp4")
            if not dst.exists():
                missing.append(str(src))
            continue
        if ext in SKIP_ORIGINAL_EXTS:
            continue
        # Only verify images we expect to convert
        if ext not in CONVERT_IMAGE_EXTS:
            continue
        # Map extension to expected converted path suffix
        rel = src.relative_to(originals)
        # Primary expected output: .png
        dst_png = converted / rel.with_suffix(".png")
        # Accept legacy .jpg conversions too
        dst_jpg = converted / rel.with_suffix(".jpg")
        dst = dst_png if dst_png.exists() else dst_jpg
        if not dst.exists():
            missing.append(str(src))
            continue
        src_wh = image_size(src)
        dst_wh = image_size(dst)
        if not src_wh or not dst_wh:
            errors.append(f"Unreadable image (src or dst): {src} -> {dst}")
            continue
        sw, sh = src_wh
        dw, dh = dst_wh
        if sw == 0 or sh == 0 or dw == 0 or dh == 0:
            errors.append(f"Zero dimension encountered: {src} -> {dst}")
            continue
        if sw != dw or sh != dh:
            sa = sw / sh
            da = dw / dh
            if abs(sa - da) > tolerance:
                mismatched.append(
                    f"Aspect mismatch: {src} ({sw}x{sh}) -> {dst} ({dw}x{dh}), Δ={abs(sa-da):.4f}"
                )
        # Grayscale detection on converted outputs only
        try:
            if is_likely_grayscale(dst):
                grayscale.append(str(dst))
        except Exception:
            pass
    errors.extend([f"Missing converted for {p}" for p in missing])
    errors.extend(mismatched)
    errors.extend([f"Likely grayscale: {p}" for p in grayscale])
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify converted assets match originals"
    )
    parser.add_argument("root", nargs="?", default="footage", help="Footage root")
    parser.add_argument(
        "--tolerance", type=float, default=0.01, help="Aspect ratio tolerance"
    )
    parser.add_argument(
        "--slug", default=None, help="Only verify this slug (YYYYMMDD_slug)"
    )
    parser.add_argument("--report", default=None, help="Optional JSON report path")
    args = parser.parse_args(argv)
    root = pathlib.Path(args.root)
    all_errors: list[str] = []
    slugs = (
        [root / args.slug] if args.slug else [p for p in root.iterdir() if p.is_dir()]
    )
    for slug in slugs:
        if slug.is_dir():
            all_errors.extend(verify_slug(slug, tolerance=args.tolerance))
    if args.report:
        report = {"errors": all_errors, "count": len(all_errors)}
        pathlib.Path(args.report).write_text(json.dumps(report, indent=2))
    if all_errors:
        print("Verification failed:")
        for e in all_errors:
            print(e)
        return 1
    print("Verification passed: all converted assets match")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
