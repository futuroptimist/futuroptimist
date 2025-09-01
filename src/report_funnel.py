"""Report funnel stats and write a selections.json manifest for a slug.

Usage:
  python src/report_funnel.py --slug YYYYMMDD_slug [--selects-file selects.txt] [-o selections.json]

If a selects file is provided, it should contain one repo-relative path per line
referring to assets under footage/<slug>/converted/. Lines starting with '#'
are comments. The tool will classify kind by extension and include the listed
assets in the manifest.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Iterable


IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
VIDEO_EXTS = {".mp4"}


def _utc_now_iso() -> str:
    return (
        datetime.now(tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _count_files(base: pathlib.Path) -> int:
    return sum(1 for f in base.rglob("*") if f.is_file())


def _read_selects(paths: Iterable[str]) -> list[str]:
    result: list[str] = []
    for raw in paths:
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        result.append(s)
    return result


def build_manifest(
    root: pathlib.Path, slug: str, selects_file: pathlib.Path | None
) -> dict:
    slug_dir = root / slug
    originals = slug_dir / "originals"
    converted = slug_dir / "converted"
    originals_total = _count_files(originals) if originals.is_dir() else 0
    converted_total = _count_files(converted) if converted.is_dir() else 0

    selected_assets: list[dict] = []
    if selects_file and selects_file.exists():
        selects = _read_selects(selects_file.read_text().splitlines())
        for p in selects:
            path = pathlib.Path(p)
            # Support both repo-relative and footage-relative entries
            if not path.is_absolute():
                if not path.parts or path.parts[0] != "footage":
                    path = root / slug / "converted" / path
                else:
                    path = root.parents[0] / path  # repo root + footage/...
            ext = path.suffix.lower()
            kind = (
                "image"
                if ext in IMAGE_EXTS
                else ("video" if ext in VIDEO_EXTS else "image")
            )
            selected_assets.append({"path": str(path.as_posix()), "kind": kind})

    manifest = {
        "slug": slug,
        "generated_at": _utc_now_iso(),
        "originals_total": originals_total,
        "converted_total": converted_total,
        "selected_count": len(selected_assets),
        "selected_assets": selected_assets,
    }
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write selections.json for a slug")
    parser.add_argument("--slug", required=True, help="Slug like YYYYMMDD_slug")
    parser.add_argument("--root", default="footage", help="Footage root")
    parser.add_argument(
        "--selects-file", default=None, help="Optional selects.txt path"
    )
    parser.add_argument("-o", "--output", default=None, help="Output JSON file path")
    args = parser.parse_args(argv)

    root = pathlib.Path(args.root)
    selects = pathlib.Path(args.selects_file) if args.selects_file else None
    manifest = build_manifest(root, args.slug, selects)
    out = pathlib.Path(args.output or (root / args.slug / "selections.json"))
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
