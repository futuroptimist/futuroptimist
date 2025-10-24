"""Generate assets.json manifests from footage directories."""

from __future__ import annotations

import argparse
import json
import pathlib
from collections.abc import Iterable
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _normalise_repo_path(path: pathlib.Path, repo_root: pathlib.Path) -> str:
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _collect_footage_directories(
    footage_dir: pathlib.Path,
    repo_root: pathlib.Path,
) -> list[str]:
    if not footage_dir.exists():
        return []

    directories: set[pathlib.Path] = set()
    file_found = False
    for file_path in footage_dir.rglob("*"):
        if not file_path.is_file():
            continue
        file_found = True
        parent = file_path.parent
        while parent != footage_dir.parent and parent.is_relative_to(footage_dir):
            directories.add(parent)
            if parent == footage_dir:
                break
            parent = parent.parent
    if not file_found:
        directories.add(footage_dir)

    return sorted(
        {_normalise_repo_path(directory, repo_root) for directory in directories}
    )


def _collect_label_files(
    footage_dir: pathlib.Path, repo_root: pathlib.Path
) -> list[str]:
    if not footage_dir.exists():
        return []
    labels: set[str] = set()
    for candidate in footage_dir.rglob("labels.json"):
        if candidate.is_file():
            labels.add(_normalise_repo_path(candidate, repo_root))
    return sorted(labels)


def _find_notes_file(
    slug_dir: pathlib.Path,
    footage_dir: pathlib.Path,
    repo_root: pathlib.Path,
) -> str | None:
    for candidate in (
        footage_dir / "notes.md",
        footage_dir / "notes.txt",
        slug_dir / "notes.md",
        slug_dir / "notes.txt",
    ):
        if candidate.exists():
            return _normalise_repo_path(candidate, repo_root)
    return None


def _iter_slugs(
    video_root: pathlib.Path,
    slugs: Iterable[str] | None,
) -> list[str]:
    if slugs:
        cleaned = {slug.strip() for slug in slugs if slug and slug.strip()}
        return sorted(cleaned)
    if not video_root.exists():
        return []
    return sorted(p.name for p in video_root.iterdir() if p.is_dir())


def generate_manifests(
    *,
    video_root: pathlib.Path = REPO_ROOT / "video_scripts",
    footage_root: pathlib.Path = REPO_ROOT / "footage",
    slugs: Iterable[str] | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Generate assets.json manifests for the provided slugs."""

    video_root = video_root.resolve()
    footage_root = footage_root.resolve()
    repo_root = video_root.parent

    results: list[dict[str, Any]] = []
    for slug in _iter_slugs(video_root, slugs):
        slug_dir = video_root / slug
        footage_dir = footage_root / slug
        manifest_path = slug_dir / "assets.json"

        if manifest_path.exists() and not overwrite and not dry_run:
            print(f"Skipping {slug}: assets.json already exists")
            try:
                existing = json.loads(manifest_path.read_text(encoding="utf-8"))
                footage_dirs = list(existing.get("footage_dirs", []))
            except json.JSONDecodeError:
                footage_dirs = []
            results.append(
                {
                    "slug": slug,
                    "written": False,
                    "path": manifest_path,
                    "footage_dirs": footage_dirs,
                }
            )
            continue

        footage_dirs = _collect_footage_directories(footage_dir, repo_root)
        if not footage_dirs:
            print(f"Skipping {slug}: no footage found under {footage_dir}")
            results.append(
                {
                    "slug": slug,
                    "written": False,
                    "path": manifest_path,
                    "footage_dirs": [],
                }
            )
            continue

        manifest: dict[str, Any] = {"footage_dirs": footage_dirs}
        labels = _collect_label_files(footage_dir, repo_root)
        if labels:
            manifest["labels_files"] = labels
        notes_file = _find_notes_file(slug_dir, footage_dir, repo_root)
        if notes_file:
            manifest["notes_file"] = notes_file

        if not dry_run:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            print(f"Wrote {manifest_path}")
        else:
            print(f"Dry run for {slug}: would write {manifest_path}")

        results.append(
            {
                "slug": slug,
                "written": not dry_run,
                "path": manifest_path,
                "footage_dirs": footage_dirs,
            }
        )
    return results


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate assets.json manifests from footage directories",
    )
    parser.add_argument(
        "--slug",
        action="append",
        dest="slugs",
        default=None,
        help="Slug(s) to process (repeatable). Defaults to all video_scripts/* folders.",
    )
    parser.add_argument(
        "--video-root",
        type=pathlib.Path,
        default=pathlib.Path("video_scripts"),
        help="Directory containing script folders",
    )
    parser.add_argument(
        "--footage-root",
        type=pathlib.Path,
        default=pathlib.Path("footage"),
        help="Directory containing footage folders",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing assets.json files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview manifests without writing files",
    )
    args = parser.parse_args(argv)

    generate_manifests(
        video_root=args.video_root,
        footage_root=args.footage_root,
        slugs=args.slugs,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
