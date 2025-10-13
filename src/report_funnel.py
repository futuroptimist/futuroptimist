"""Report funnel stats and write a selections.json manifest for a slug.

The CLI prints totals and coverage percentages (converted/originals,
selected/converted) and the manifest stores ``converted_coverage`` and
``selected_coverage`` ratios for downstream automation.

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
from pathlib import PurePosixPath, PureWindowsPath
from typing import Iterable


IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
VIDEO_EXTS = {".mp4"}
AUDIO_EXTS = {".wav", ".mp3", ".aac", ".m4a", ".flac", ".ogg"}


def _coverage(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


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


def _split_select_entry(entry: str) -> tuple[list[str], bool, bool]:
    """Return components, absolute flag, and whether the path looked Windows-specific."""

    raw = entry.strip()
    if not raw:
        return [], False, False
    uses_windows = "\\" in raw or (len(raw) >= 2 and raw[0].isalpha() and raw[1] == ":")
    pure = PureWindowsPath(raw) if uses_windows else PurePosixPath(raw)
    parts: list[str] = []
    for part in pure.parts:
        if not part:
            continue
        if part in {pure.anchor, pure.root}:
            continue
        if part == ".":
            continue
        parts.append(part)
    is_absolute = pure.is_absolute() or (
        uses_windows
        and len(raw) >= 3
        and raw[0].isalpha()
        and raw[1] == ":"
        and raw[2] in {"/", "\\"}
    )
    if parts and len(parts[0]) == 2 and parts[0][1] == ":" and parts[0][0].isalpha():
        parts = parts[1:]
        is_absolute = True
    return parts, is_absolute, uses_windows


def _build_display(
    candidate: pathlib.Path,
    converted_root: pathlib.Path,
    repo_root: pathlib.Path,
    slug: str,
) -> tuple[pathlib.Path, str] | None:
    try:
        rel_within_converted = candidate.relative_to(converted_root)
    except ValueError:
        return None

    rel_suffix = rel_within_converted.as_posix().lstrip("./")
    canonical = "footage/{slug}/converted".format(slug=slug)
    if rel_suffix:
        canonical = f"{canonical}/{rel_suffix}"

    try:
        repo_relative = candidate.relative_to(repo_root).as_posix()
    except ValueError:
        repo_relative = ""

    display = repo_relative if repo_relative.startswith("footage/") else canonical
    return candidate, display


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
    parts, is_absolute, uses_windows = _split_select_entry(raw)
    if is_absolute and not uses_windows:
        raw_path = pathlib.Path(raw)
        if raw_path.is_absolute():
            normalized = _build_display(
                raw_path.resolve(), converted_root, repo_root, slug
            )
            if normalized is not None:
                return normalized
    if any(part == ".." for part in parts):
        return None

    footage_index: int | None = next(
        (idx for idx, part in enumerate(parts) if part.lower() == "footage"),
        None,
    )
    footage_found = footage_index is not None
    if footage_found:
        parts = parts[footage_index + 1 :]
    elif is_absolute:
        return None

    if parts and parts[0].lower() == slug.lower():
        parts = parts[1:]
    elif footage_found:
        return None

    if parts and parts[0].lower() == "converted":
        parts = parts[1:]

    filtered = [part for part in parts if part and part != "."]
    tail = pathlib.Path(*filtered) if filtered else pathlib.Path()
    candidate = (converted_root / tail).resolve()

    return _build_display(candidate, converted_root, repo_root, slug)


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
                kind = "other"
            selected_assets.append({"path": display_path, "kind": kind})

    converted_coverage = _coverage(converted_total, originals_total)
    selected_coverage = _coverage(len(selected_assets), converted_total)

    manifest = {
        "slug": slug,
        "generated_at": _utc_now_iso(),
        "originals_total": originals_total,
        "converted_total": converted_total,
        "converted_coverage": converted_coverage,
        "selected_count": len(selected_assets),
        "selected_coverage": selected_coverage,
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
    summary_lines = [
        f"Originals: {manifest['originals_total']}",
        (
            "Converted: {total} ({coverage} of originals)".format(
                total=manifest["converted_total"],
                coverage=_percent(manifest["converted_coverage"]),
            )
        ),
        (
            "Selected: {count} ({coverage} of converted)".format(
                count=manifest["selected_count"],
                coverage=_percent(manifest["selected_coverage"]),
            )
        ),
    ]
    if manifest["selected_assets"]:
        kind_counts: dict[str, int] = {}
        for asset in manifest["selected_assets"]:
            kind = asset.get("kind") or "other"
            kind_counts[kind] = kind_counts.get(kind, 0) + 1
        breakdown = ", ".join(
            f"{kind}={kind_counts[kind]}" for kind in sorted(kind_counts)
        )
        summary_lines.append(f"Selected breakdown: {breakdown}")
    print("\n".join(summary_lines))

    out = pathlib.Path(args.output or (root / args.slug / "selections.json"))
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
