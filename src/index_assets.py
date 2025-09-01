"""Build a rich assets index across all video scripts.

Scans each `video_scripts/*/assets.json` manifest (validated against
`schemas/assets_manifest.schema.json`) and produces `assets_index.json` with
per-asset records including path, size, UTC mtime, related script folder,
tags, and any labels provided by optional `labels.json` files.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable
from PIL import Image

from jsonschema import Draft7Validator


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_schema() -> dict[str, Any]:
    schema_path = REPO_ROOT / "schemas" / "assets_manifest.schema.json"
    return json.loads(schema_path.read_text())


def _iter_assets_manifests(
    base: pathlib.Path,
) -> Iterable[tuple[pathlib.Path, dict[str, Any]]]:
    schema = _load_schema()
    validator = Draft7Validator(schema)
    for manifest in base.glob("video_scripts/*/assets.json"):
        try:
            data = json.loads(manifest.read_text())
        except json.JSONDecodeError:
            raise SystemExit(f"Invalid JSON in {manifest}")
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        if errors:
            messages = "; ".join([f"{list(e.path)}: {e.message}" for e in errors])
            raise SystemExit(f"Manifest {manifest} failed schema: {messages}")
        yield manifest, data


def _iso_utc(ts: float) -> str:
    return (
        datetime.fromtimestamp(ts, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass
class AssetRecord:
    path: str
    size: int
    mtime: str
    script_folder: str
    tags: list[str]
    capture_date: str | None
    labels: dict[str, Any] | None
    width: int | None = None
    height: int | None = None
    aspect_ratio: float | None = None
    orientation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "size": self.size,
            "mtime": self.mtime,
            "script_folder": self.script_folder,
            "tags": self.tags,
            "capture_date": self.capture_date,
            "labels": self.labels,
            "width": self.width,
            "height": self.height,
            "aspect_ratio": self.aspect_ratio,
            "orientation": self.orientation,
        }


def _load_labels(paths: list[str]) -> dict[str, dict[str, Any]]:
    labels_map: dict[str, dict[str, Any]] = {}
    for p in paths:
        path = REPO_ROOT / p
        if path.exists():
            try:
                data = json.loads(path.read_text())
                # Expect either an array of objects or a dict keyed by relative path
                if isinstance(data, list):
                    for entry in data:
                        asset_path = entry.get("path")
                        if isinstance(asset_path, str):
                            labels_map[asset_path] = entry
                elif isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(k, str) and isinstance(v, dict):
                            labels_map[k] = v
            except json.JSONDecodeError:
                continue
    return labels_map


def build_index() -> list[dict[str, Any]]:
    results: list[AssetRecord] = []
    for manifest_path, data in _iter_assets_manifests(REPO_ROOT):
        script_folder = manifest_path.parent.name
        tags = list(data.get("tags", []))
        capture_date = data.get("capture_date")
        labels_map = _load_labels(list(data.get("labels_files", [])))
        for dir_str in data["footage_dirs"]:
            d = REPO_ROOT / dir_str
            if not d.exists() or not d.is_dir():
                continue
            for f in d.rglob("*"):
                if not f.is_file():
                    continue
                stat = f.stat()
                rel = f.relative_to(REPO_ROOT / "footage").as_posix()
                # labels are keyed by either full repo-relative path or by footage-relative path; support both
                labels = labels_map.get(rel) or labels_map.get(
                    (REPO_ROOT / "footage" / rel).as_posix()
                )
                width: int | None = None
                height: int | None = None
                aspect: float | None = None
                orientation: str | None = None
                try:
                    # HEIC support
                    try:
                        from pillow_heif import register_heif_opener  # type: ignore

                        register_heif_opener()
                    except Exception:
                        pass
                    if f.suffix.lower() == ".dng":
                        try:
                            import rawpy  # type: ignore

                            with rawpy.imread(str(f)) as raw:
                                width, height = int(raw.sizes.width), int(
                                    raw.sizes.height
                                )
                        except Exception:
                            width = height = None
                    if width is None or height is None:
                        with Image.open(f) as im:
                            width, height = im.size
                    if width and height:
                        aspect = round(width / height, 6)
                        orientation = (
                            "landscape"
                            if width > height
                            else ("portrait" if height > width else "square")
                        )
                except Exception:
                    pass
                results.append(
                    AssetRecord(
                        path=f"footage/{rel}",
                        size=stat.st_size,
                        mtime=_iso_utc(stat.st_mtime),
                        script_folder=script_folder,
                        tags=tags,
                        capture_date=capture_date,
                        labels=labels,
                        width=width,
                        height=height,
                        aspect_ratio=aspect,
                        orientation=orientation,
                    )
                )
    # Sort deterministically for stable diffs
    results.sort(key=lambda r: (r.mtime, r.path))
    return [r.to_dict() for r in results]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Build rich assets index from manifests"
    )
    parser.add_argument(
        "-o", "--output", default="assets_index.json", help="Output JSON file path"
    )
    args = parser.parse_args(argv)
    index = build_index()
    out = REPO_ROOT / args.output
    out.write_text(json.dumps(index, indent=2) + "\n")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
