from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

DEFAULT_CAD_DIR = Path("cad")
DEFAULT_STL_DIR = Path("stl")
DEFAULT_TIME_TOLERANCE = 1.0  # seconds


def _collect(parts_dir: Path, pattern: str) -> Dict[str, Path]:
    files: Dict[str, Path] = {}
    for path in sorted(parts_dir.rglob(pattern)):
        if path.is_file():
            files[path.stem] = path
    return files


def verify_fit(
    cad_dir: Path | str = DEFAULT_CAD_DIR,
    stl_dir: Path | str = DEFAULT_STL_DIR,
    *,
    time_tolerance: float = DEFAULT_TIME_TOLERANCE,
) -> bool:
    """Ensure each SCAD source has a matching, up-to-date STL export."""

    cad_path = Path(cad_dir)
    stl_path = Path(stl_dir)

    if time_tolerance < 0:
        raise ValueError("time_tolerance must be non-negative")

    if not cad_path.exists():
        print(f"Skipping fit check: {cad_path} not found.")
        return True

    if not stl_path.exists():
        raise FileNotFoundError(f"STL directory {stl_path} not found")

    cad_parts = _collect(cad_path, "*.scad")
    if not cad_parts:
        print(f"No .scad files found under {cad_path}; nothing to verify.")
        return True

    stl_parts = _collect(stl_path, "*.stl")
    missing = sorted(name for name in cad_parts if name not in stl_parts)
    if missing:
        raise AssertionError("Missing STL export(s) for: " + ", ".join(missing))

    stale: list[str] = []
    for name, scad_file in cad_parts.items():
        export = stl_parts[name]
        scad_mtime = scad_file.stat().st_mtime
        stl_mtime = export.stat().st_mtime
        if stl_mtime + time_tolerance < scad_mtime:
            delta = scad_mtime - stl_mtime
            stale.append(f"{name} ({delta:.1f}s stale export)")

    if stale:
        raise AssertionError("Detected stale exports: " + ", ".join(stale))

    extras = sorted(name for name in stl_parts if name not in cad_parts)
    if extras:
        print(
            "Warning: STL files without matching SCAD sources: " + ", ".join(extras),
            file=sys.stderr,
        )

    print(f"All parts up to date across {len(cad_parts)} design(s).")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify CAD sources have matching, fresh STL exports",
    )
    parser.add_argument(
        "--cad-dir",
        type=Path,
        default=DEFAULT_CAD_DIR,
        help="Directory containing .scad files (default: ./cad)",
    )
    parser.add_argument(
        "--stl-dir",
        type=Path,
        default=DEFAULT_STL_DIR,
        help="Directory containing .stl exports (default: ./stl)",
    )
    parser.add_argument(
        "--time-tolerance",
        type=float,
        default=DEFAULT_TIME_TOLERANCE,
        help="Allowed seconds an STL may be older than its SCAD source",
    )
    args = parser.parse_args(argv)

    try:
        success = verify_fit(
            cad_dir=args.cad_dir,
            stl_dir=args.stl_dir,
            time_tolerance=args.time_tolerance,
        )
    except (FileNotFoundError, AssertionError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0 if success else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
