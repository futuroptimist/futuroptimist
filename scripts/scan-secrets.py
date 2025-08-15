#!/usr/bin/env python3
"""Detect potential secrets in staged diffs.

Reads unified diff content from ``stdin`` and scans only the **added** lines
for secret-like patterns. The scan is intentionally lightweight and should be
supplemented with dedicated tools for thorough auditing.
"""
from __future__ import annotations

import re
import sys

PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"(?i)(api_key|apikey|password|secret)[\s:=]+[^\n]+"),
]


def main() -> int:
    raw = sys.stdin.read()
    lines: list[str] = []
    for line in raw.splitlines():
        if "allowlist secret" in line:
            continue
        if not line.startswith("+") or line.startswith("+++"):
            # Skip context and removed lines; ignore diff headers like '+++ b/file'.
            continue
        lines.append(line[1:])
    content = "\n".join(lines)

    matches: list[str] = []
    for pattern in PATTERNS:
        matches.extend(m.group(0) for m in pattern.finditer(content))
    if matches:
        sys.stderr.write("Possible secrets detected:\n")
        for m in matches:
            sys.stderr.write(f"{m}\n")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
