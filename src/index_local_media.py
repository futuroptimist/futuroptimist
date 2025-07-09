import argparse
import json
import pathlib
from datetime import datetime


def scan_directory(base: pathlib.Path):
    """Return a list of dictionaries describing files under ``base``."""
    records = []
    for path in base.rglob("*"):
        if path.is_file():
            mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            rel_path = str(path.relative_to(base)).replace("\\", "/")
            records.append({"path": rel_path, "mtime": mtime})
    return sorted(records, key=lambda r: r["mtime"])


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
    pathlib.Path(args.output).write_text(json.dumps(index, indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
