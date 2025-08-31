#!/usr/bin/env python3
"""Pre-commit wrapper to scan staged diff for secrets/PII.

Runs `git diff --cached -U0` and feeds the diff to `scripts/scan-secrets.py`.
Exits non-zero if potential secrets are detected.
"""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    try:
        diff_proc = subprocess.run(
            ["git", "diff", "--cached", "-U0"],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"Failed to run git diff: {exc}\n")
        return 2

    scan_proc = subprocess.run(
        [sys.executable, "scripts/scan-secrets.py"],
        input=diff_proc.stdout,
        capture_output=True,
        text=True,
    )
    # Mirror scanner output
    if scan_proc.stdout:
        sys.stdout.write(scan_proc.stdout)
    if scan_proc.stderr:
        sys.stderr.write(scan_proc.stderr)
    return scan_proc.returncode


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
