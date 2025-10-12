from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

DEFAULT_CAD_DIR = Path("cad")
DEFAULT_STL_DIR = Path("stl")
DEFAULT_TIME_TOLERANCE = 1.0  # seconds

_EXPORT_PATTERNS: dict[str, str] = {
    "STL": "*.stl",
    "OBJ": "*.obj",
}


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
    """Ensure each SCAD source has matching, up-to-date STL and OBJ exports."""

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

    exports: dict[str, Dict[str, Path]] = {
        kind: _collect(stl_path, pattern) for kind, pattern in _EXPORT_PATTERNS.items()
    }

    missing_errors: list[str] = []
    for kind, parts in exports.items():
        missing = sorted(name for name in cad_parts if name not in parts)
        if missing:
            missing_errors.append(
                f"Missing {kind} export(s) for: " + ", ".join(missing)
            )
    if missing_errors:
        raise AssertionError("; ".join(missing_errors))

    stale: list[str] = []
    for name, scad_file in cad_parts.items():
        scad_mtime = scad_file.stat().st_mtime
        for parts in exports.values():
            export_file = parts[name]
            export_mtime = export_file.stat().st_mtime
            if export_mtime + time_tolerance < scad_mtime:
                delta = scad_mtime - export_mtime
                stale.append(
                    f"{name}.{export_file.suffix.lstrip('.')} ({delta:.1f}s stale export)"
                )

    if stale:
        raise AssertionError("Detected stale exports: " + ", ".join(stale))

    extras_messages: list[str] = []
    for kind, parts in exports.items():
        extras = sorted(name for name in parts if name not in cad_parts)
        if extras:
            extras_messages.append(f"{kind}: " + ", ".join(extras))
    if extras_messages:
        print(
            "Warning: exports without matching SCAD sources -> "
            + "; ".join(extras_messages),
            file=sys.stderr,
        )

    print(f"All parts up to date across {len(cad_parts)} design(s).")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify CAD sources have matching, fresh STL/OBJ exports",
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
        help="Directory containing .stl/.obj exports (default: ./stl)",
    )
    parser.add_argument(
        "--time-tolerance",
        type=float,
        default=DEFAULT_TIME_TOLERANCE,
        help="Allowed seconds an export may be older than its SCAD source",
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
