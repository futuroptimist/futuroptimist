"""Convert only the assets reported as missing by verify_converted_assets.

Usage:
  python src/convert_missing.py --report verify_report.json
"""

from __future__ import annotations

import argparse
import json
import pathlib

from src import convert_assets

MISSING_PREFIX = "Missing converted for "
VIDEO_EXTS = set(convert_assets.VIDEO_RULES)


def _parse_missing(paths: list[str]) -> list[pathlib.Path]:
    results: list[pathlib.Path] = []
    for raw in paths:
        if not raw.startswith(MISSING_PREFIX):
            continue
        candidate = raw[len(MISSING_PREFIX) :].strip()
        if not candidate:
            continue
        results.append(pathlib.Path(candidate))
    return results


def _group_conversions(
    missing: list[pathlib.Path],
) -> dict[pathlib.Path, dict[str, set[str] | list[str] | bool]]:
    grouped: dict[pathlib.Path, dict[str, set[str] | list[str] | bool]] = {}
    for path in missing:
        parts = path.parts
        try:
            idx = next(i for i, part in enumerate(parts) if part == "footage")
        except StopIteration:
            # If the path does not contain the footage root we cannot resolve it reliably
            continue
        root = pathlib.Path(*parts[: idx + 1])
        slug = parts[idx + 1] if len(parts) > idx + 1 else None
        data = grouped.setdefault(
            root,
            {"slugs": set(), "name_like": [], "include_video": False},
        )
        if slug:
            data["slugs"].add(slug)
        data["name_like"].append(str(path))
        if path.suffix.lower() in VIDEO_EXTS:
            data["include_video"] = True
    return grouped


def _run_conversions(
    groups: dict[pathlib.Path, dict[str, set[str] | list[str] | bool]],
) -> int:
    exit_code = 0
    for root, data in groups.items():
        argv: list[str] = [str(root), "--force"]
        if data["include_video"]:
            argv.append("--include-video")
        for slug in sorted(data["slugs"]):
            argv.extend(["--slug", slug])
        for pattern in data["name_like"]:
            argv.extend(["--name-like", pattern])
        result = convert_assets.main(argv)
        if result != 0:
            exit_code = result
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert missing assets from verify report"
    )
    parser.add_argument("--report", required=True, help="Path to verify_report.json")
    args = parser.parse_args(argv)
    report_path = pathlib.Path(args.report)
    data = json.loads(report_path.read_text())
    errors: list[str] = data.get("errors", [])
    missing_paths = _parse_missing(errors)
    if not missing_paths:
        print("No missing items in report.")
        return 0
    groups = _group_conversions(missing_paths)
    if not groups:
        print("No resolvable footage paths found in report.")
        return 0
    return _run_conversions(groups)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
