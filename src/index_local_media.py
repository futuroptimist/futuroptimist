"""Index local media files and write a JSON inventory.

The generated index lists file paths, modification times in UTC,
and file sizes in bytes. Modification timestamps are truncated to
whole seconds for stable output. The output file's parent directories
are created automatically.
"""

import argparse
import json
import pathlib
from datetime import datetime, timezone


def scan_directory(base: pathlib.Path):
    """Return a list of dictionaries describing files under ``base``.

    Each record contains ``path``, ``mtime`` (ISO timestamp in UTC without
    sub-second precision), and file ``size`` in bytes. The list is sorted by
    modification time and
    then by path to produce deterministic output.
    """
    records = []
    for path in base.rglob("*"):
        if path.is_file():
            stat = path.stat()
            mtime = (
                datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
            rel_path = str(path.relative_to(base)).replace("\\", "/")
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
    index = scan_directory(base)
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
