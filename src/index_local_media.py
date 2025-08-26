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


def scan_directory(base: pathlib.Path, exclude: Iterable[pathlib.Path] | None = None):
    """Return a list of dictionaries describing files under ``base``.

    Each record contains ``path``, ``mtime`` (ISO timestamp in UTC without
    sub-second precision), and file ``size`` in bytes. The list is sorted by
    modification time and then by path to produce deterministic output. Paths
    listed in ``exclude`` are ignored.
    """
    records = []
    exclude_set: set[str] = set()
    if exclude:
        base_resolved = base.resolve()
        for p in exclude:
            try:
                rel = p.resolve().relative_to(base_resolved).as_posix()
            except ValueError:
                continue
            exclude_set.add(rel)
    for path in base.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        rel_path = path.relative_to(base).as_posix()
        if rel_path in exclude_set:
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
    args = parser.parse_args(argv)

    base = pathlib.Path(args.directory)
    if not base.is_dir():
        parser.error(f"{base} is not a directory")
    output_path = pathlib.Path(args.output)
    index = scan_directory(base, exclude=[output_path])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
