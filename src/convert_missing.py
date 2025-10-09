"""Convert only missing items listed in verify_report.json.

Usage:
  python src/convert_missing.py --report verify_report.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert missing assets from verify report"
    )
    parser.add_argument("--report", required=True, help="Path to verify_report.json")
    args = parser.parse_args(argv)
    report_path = pathlib.Path(args.report)
    data = json.loads(report_path.read_text())
    errors: list[str] = data.get("errors", [])
    missing = [e for e in errors if e.startswith("Missing converted for ")]
    # Extract unique source paths
    sources = sorted({e.replace("Missing converted for ", "").strip() for e in missing})
    if not sources:
        print("No missing items in report.")
        return 0
    exts = sorted({pathlib.Path(s).suffix.lower() for s in sources if s})
    footage_root = pathlib.Path("footage")
    video_exts = {".mov", ".mkv", ".avi", ".mts", ".m2ts", ".m4v", ".wmv", ".3gp"}
    include_video = any(ext in video_exts for ext in exts)
    slugs: set[str] = set()
    normalized_sources: list[str] = []
    for raw in sources:
        if not raw:
            continue
        src_path = pathlib.Path(raw)
        under_base = False
        if not src_path.is_absolute():
            candidate = src_path
            under_base = True
        else:
            try:
                candidate = src_path.relative_to(footage_root.resolve())
                under_base = True
            except ValueError:
                candidate = src_path
        parts = candidate.parts
        rel_parts = parts
        if parts and parts[0] == "footage":
            rel_parts = parts[1:]
            under_base = True
        if rel_parts and under_base:
            slugs.add(rel_parts[0])
        rel_candidate = pathlib.Path(*rel_parts) if rel_parts else candidate
        normalized_sources.append(str(rel_candidate))

    unique_sources = sorted(set(normalized_sources))
    if not unique_sources:
        print("No convertible sources found in report.")
        return 0

    cmd = [sys.executable, "src/convert_assets.py", "footage"]
    if include_video:
        cmd.append("--include-video")
    for ext in exts:
        cmd += ["--only-ext", ext]
    for slug in sorted(slugs):
        cmd += ["--slug", slug]
    for source in unique_sources:
        cmd += ["--source", source]
    print(f"Converting {len(unique_sources)} missing source(s)")
    res = subprocess.run(cmd)
    return res.returncode


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
