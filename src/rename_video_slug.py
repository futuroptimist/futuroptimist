"""Rename a video script folder and update related metadata.

The helper renames ``video_scripts/<date>_<slug>`` directories to use a
new slug while keeping the date prefix intact. When a matching
``footage/<date>_<slug>`` directory exists it is renamed as well. JSON
metadata such as ``metadata.json``, ``assets.json``,
``footage/<slug>/selections.json`` and ``labels.json`` are rewritten so
references to the old slug continue to resolve after the rename.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _split_folder_name(name: str) -> tuple[str, str]:
    if "_" not in name:
        raise ValueError(
            "Folder name must include an underscore separating date and slug"
        )
    prefix, slug = name.split("_", 1)
    if not prefix.isdigit() or len(prefix) != 8:
        raise ValueError(
            "Folder name must start with YYYYMMDD date prefix (e.g. 20240101_slug)"
        )
    return prefix, slug


def _validate_new_slug(value: str) -> str:
    trimmed = value.strip()
    if not trimmed:
        raise ValueError("New slug cannot be blank")
    if not SLUG_RE.fullmatch(trimmed):
        raise ValueError(
            "Slug must contain lowercase letters, numbers, or hyphens (e.g. fresh-slug)"
        )
    return trimmed


def _replace_slug_in_data(
    obj: Any, old_folder: str, new_folder: str
) -> tuple[Any, bool]:
    """Recursively replace slug references in ``obj``.

    Strings receive ``str.replace`` calls while dictionaries have their keys
    updated when necessary. Returns the transformed object and whether a
    change was applied.
    """

    if isinstance(obj, dict):
        changed = False
        new_dict: dict[Any, Any] = {}
        for key, value in obj.items():
            new_key = key.replace(old_folder, new_folder)
            if new_key != key:
                changed = True
            new_value, child_changed = _replace_slug_in_data(
                value, old_folder, new_folder
            )
            if child_changed:
                changed = True
            new_dict[new_key] = new_value
        return new_dict, changed
    if isinstance(obj, list):
        changed = False
        new_list = []
        for item in obj:
            new_item, child_changed = _replace_slug_in_data(
                item, old_folder, new_folder
            )
            if child_changed:
                changed = True
            new_list.append(new_item)
        return new_list, changed
    if isinstance(obj, str):
        new_value = obj.replace(old_folder, new_folder)
        return new_value, new_value != obj
    return obj, False


def _rewrite_json(
    path: pathlib.Path,
    *,
    old_folder: str,
    new_folder: str,
    slug_value: str | None = None,
    slug_only: bool = False,
) -> bool:
    """Rewrite ``path`` with updated slug references.

    ``slug_value`` sets/overrides a top-level ``slug`` field when provided.
    ``slug_only`` skips recursive replacement and only updates ``slug``.
    Returns ``True`` when the file changed.
    """

    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False

    changed = False
    if slug_value is not None:
        if not isinstance(data, dict):
            raise ValueError(f"Expected object in {path} to update slug field")
        if data.get("slug") != slug_value:
            data["slug"] = slug_value
            changed = True

    if not slug_only:
        data, replaced = _replace_slug_in_data(data, old_folder, new_folder)
        if replaced:
            changed = True

    if not changed:
        return False

    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def rename_slug(
    current_folder: str,
    new_slug: str,
    *,
    repo_root: pathlib.Path = REPO_ROOT,
    rename_footage: bool = True,
    dry_run: bool = False,
) -> pathlib.Path:
    """Rename ``current_folder`` under ``video_scripts`` to use ``new_slug``.

    Returns the destination path. Raises ``FileNotFoundError`` if the source
    folder is missing and ``FileExistsError`` when the destination already
    exists.
    """

    new_slug = _validate_new_slug(new_slug)
    prefix, old_slug = _split_folder_name(current_folder)
    new_folder_name = f"{prefix}_{new_slug}"
    video_root = repo_root / "video_scripts"
    source_dir = video_root / current_folder
    if not source_dir.is_dir():
        raise FileNotFoundError(f"video_scripts/{current_folder} not found")
    dest_dir = video_root / new_folder_name
    if dest_dir.exists():
        raise FileExistsError(f"video_scripts/{new_folder_name} already exists")

    footage_source = repo_root / "footage" / current_folder
    footage_dest = repo_root / "footage" / new_folder_name
    if rename_footage and footage_dest.exists():
        raise FileExistsError(f"footage/{new_folder_name} already exists")

    if dry_run:
        return dest_dir

    source_dir.rename(dest_dir)
    if rename_footage and footage_source.exists():
        footage_source.rename(footage_dest)

    old_folder = current_folder
    new_folder = new_folder_name

    metadata_path = dest_dir / "metadata.json"
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
            raise ValueError(f"Invalid JSON in {metadata_path}: {exc}") from exc
        changed = False
        if metadata.get("slug") != new_slug:
            metadata["slug"] = new_slug
            changed = True
        metadata, replaced = _replace_slug_in_data(metadata, old_folder, new_folder)
        if replaced:
            changed = True
        if changed:
            metadata_path.write_text(
                json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
            )

    assets_path = dest_dir / "assets.json"
    _rewrite_json(
        assets_path,
        old_folder=old_folder,
        new_folder=new_folder,
        slug_value=None,
    )

    if rename_footage and footage_dest.exists():
        _rewrite_json(
            footage_dest / "selections.json",
            old_folder=old_folder,
            new_folder=new_folder,
            slug_value=new_folder,
        )
        _rewrite_json(
            footage_dest / "labels.json",
            old_folder=old_folder,
            new_folder=new_folder,
        )
        _rewrite_json(
            footage_dest / "verify_report.json",
            old_folder=old_folder,
            new_folder=new_folder,
        )

    return dest_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rename a video script folder and matching footage directory"
    )
    parser.add_argument(
        "current",
        help="Existing folder under video_scripts (format: YYYYMMDD_slug)",
    )
    parser.add_argument(
        "--slug",
        required=True,
        help="New slug (lowercase letters, numbers, hyphens)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the target folder without applying changes",
    )
    parser.add_argument(
        "--no-footage",
        dest="rename_footage",
        action="store_false",
        help="Do not rename the matching footage directory",
    )
    args = parser.parse_args(argv)

    try:
        dest = rename_slug(
            args.current,
            args.slug,
            rename_footage=args.rename_footage,
            dry_run=args.dry_run,
        )
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        parser.error(str(exc))

    relative = dest.relative_to(REPO_ROOT)
    if args.dry_run:
        print(f"Would rename to {relative}")
    else:
        print(f"Renamed to {relative}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
