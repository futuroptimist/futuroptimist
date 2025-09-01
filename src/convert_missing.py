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
    # Group by extension and run convert_assets with --only-ext filters (faster than per-file for now)
    exts = sorted({pathlib.Path(s).suffix.lower() for s in sources})
    cmd = [sys.executable, "src/convert_assets.py", "footage", "--force"]
    # Include video conversions if any video extensions present
    if any(
        e in {".mov", ".mkv", ".avi", ".mts", ".m2ts", ".m4v", ".wmv", ".3gp"}
        for e in exts
    ):
        cmd.append("--include-video")
    for ext in exts:
        cmd += ["--only-ext", ext]
    print("Converting extensions:", ", ".join(exts))
    res = subprocess.run(cmd)
    return res.returncode


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
