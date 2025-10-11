"""Report funnel stats and write a selections.json manifest for a slug.

Usage:
  python src/report_funnel.py --slug YYYYMMDD_slug [--selects-file selects.txt] [-o selections.json]

If a selects file is provided, it should contain one repo-relative path per line
referring to assets under footage/<slug>/converted/. Lines starting with '#'
are comments. The tool will classify kind by extension and include the listed
assets in the manifest. Paths are normalised to repo-relative
``footage/<slug>/converted/...`` entries in the output.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Iterable


IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
VIDEO_EXTS = {".mp4"}
AUDIO_EXTS = {".wav", ".mp3", ".aac", ".m4a", ".flac", ".ogg"}


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


def _normalize_select_path(
    converted_root: pathlib.Path,
    repo_root: pathlib.Path,
    slug: str,
    entry: str,
) -> tuple[pathlib.Path, str] | None:
    """Return the canonical path and display string for a selects entry.

    Entries that resolve outside ``converted_root`` (for example, via absolute
    paths or ``..`` components) return ``None`` so callers can skip them.
    """

    raw = entry.strip()
    if not raw:
        return None
    raw_path = pathlib.Path(raw)

    if raw_path.is_absolute():
        candidate = raw_path.resolve()
    else:
        parts = list(raw_path.parts)
        if parts and parts[0] == "footage":
            parts = parts[1:]
        if parts and parts[0] == slug:
            parts = parts[1:]
        if parts and parts[0].lower() == "converted":
            parts = parts[1:]
        if any(part == ".." for part in parts):
            return None
        filtered = [part for part in parts if part not in {"", "."}]
        tail = pathlib.Path(*filtered) if filtered else pathlib.Path()
        candidate = (converted_root / tail).resolve()

    try:
        rel_within_converted = candidate.relative_to(converted_root)
    except ValueError:
        return None

    rel_suffix = rel_within_converted.as_posix().lstrip("./")
    if not rel_suffix:
        canonical = f"footage/{slug}/converted"
    else:
        canonical = f"footage/{slug}/converted/{rel_suffix}"

    try:
        repo_relative = candidate.relative_to(repo_root).as_posix()
    except ValueError:
        repo_relative = ""

    display = repo_relative if repo_relative.startswith("footage/") else canonical
    return candidate, display


def build_manifest(
    root: pathlib.Path, slug: str, selects_file: pathlib.Path | None
) -> dict:
    footage_root = root.resolve()
    repo_root = footage_root.parent.resolve()
    slug_dir = footage_root / slug
    originals = slug_dir / "originals"
    converted = slug_dir / "converted"
    originals_total = _count_files(originals) if originals.is_dir() else 0
    converted_total = _count_files(converted) if converted.is_dir() else 0

    selected_assets: list[dict] = []
    seen_paths: set[str] = set()
    converted_root = (slug_dir / "converted").resolve()

    if selects_file and selects_file.exists():
        selects = _read_selects(selects_file.read_text().splitlines())
        for p in selects:
            normalized = _normalize_select_path(converted_root, repo_root, slug, p)
            if normalized is None:
                continue
            resolved, display_path = normalized
            if display_path in seen_paths:
                continue
            seen_paths.add(display_path)
            if resolved.is_dir():
                selected_assets.append(
                    {"path": display_path, "kind": "directory_select"}
                )
                continue
            ext = resolved.suffix.lower()
            if ext in IMAGE_EXTS:
                kind = "image"
            elif ext in VIDEO_EXTS:
                kind = "video"
            elif ext in AUDIO_EXTS:
                kind = "audio"
            else:
                kind = "image"
            selected_assets.append({"path": display_path, "kind": kind})

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
