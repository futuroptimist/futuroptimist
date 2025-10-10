"""Index local media files and write a JSON inventory.

The generated index lists file paths, modification times in UTC,
and file sizes in bytes. Modification timestamps are truncated to
whole seconds for stable output. The output file's parent directories
are created automatically.
"""

import argparse
import json
import pathlib
from collections.abc import Iterable
from datetime import datetime, timezone


IMAGE_EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".heic",
    ".heif",
    ".dng",
    ".raw",
    ".webp",
}

VIDEO_EXTS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".wmv",
    ".mpg",
    ".mpeg",
    ".mts",
    ".m2ts",
    ".m4v",
    ".webm",
}

AUDIO_EXTS = {
    ".wav",
    ".mp3",
    ".aac",
    ".m4a",
    ".flac",
    ".ogg",
    ".oga",
}


def _classify_kind(path: pathlib.Path) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    if ext in AUDIO_EXTS:
        return "audio"
    return "other"


def scan_directory(base: pathlib.Path, exclude: Iterable[pathlib.Path] | None = None):
    """Return a list of dictionaries describing files under ``base``.

    Each record contains ``path``, ``mtime`` (ISO timestamp in UTC without
    sub-second precision), file ``size`` in bytes, and a ``kind`` classification
    (``image``, ``video``, ``audio``, or ``other``). The list is sorted by
    modification time and then by path to produce deterministic output. Paths
    listed in ``exclude`` are ignored. Directories in ``exclude`` skip all
    nested files.
    """
    records = []
    exclude_rel: set[str] = set()
    if exclude:
        base_resolved = base.resolve()
        for raw_path in exclude:
            candidate_paths: list[pathlib.Path] = []
            path = pathlib.Path(raw_path)
            if path.is_absolute():
                candidate_paths.append(path)
            else:
                candidate_paths.append(base_resolved / path)
                candidate_paths.append(path.resolve())
            for candidate in candidate_paths:
                try:
                    resolved = candidate.resolve()
                    rel = resolved.relative_to(base_resolved)
                except ValueError:
                    continue
                rel_posix = rel.as_posix()
                exclude_rel.add("" if rel_posix == "." else rel_posix)
    for path in base.rglob("*"):
        if path.is_file():
            rel_path = path.relative_to(base).as_posix()
            if any(
                ex == "" or rel_path == ex or rel_path.startswith(f"{ex}/")
                for ex in exclude_rel
            ):
                continue
            stat = path.stat()
            mtime = (
                datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
            records.append(
                {
                    "path": rel_path,
                    "mtime": mtime,
                    "size": stat.st_size,
                    "kind": _classify_kind(path),
                }
            )
    return sorted(records, key=lambda r: (r["mtime"], r["path"]))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Index local media files for quick reference"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default="footage",
        help="Root folder containing local footage",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="footage_index.json",
        help="JSON file to write",
    )
    parser.add_argument(
        "-x",
        "--exclude",
        action="append",
        default=[],
        type=pathlib.Path,
        help="Additional files or directories to ignore",
    )
    args = parser.parse_args(argv)

    base = pathlib.Path(args.directory)
    if not base.is_dir():
        parser.error(f"{base} is not a directory")
    output_path = pathlib.Path(args.output)
    index = scan_directory(base, exclude=[output_path, *args.exclude])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
