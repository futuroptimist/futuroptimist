#!/usr/bin/env python3
"""Detect potential secrets in staged diffs.

Reads diff content from ``stdin`` and exits with status ``1`` if any
secret-like patterns are found. The scan is intentionally lightweight and
should be supplemented with dedicated tools for thorough auditing.
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
    lines = []
    for line in raw.splitlines():
        if "allowlist secret" in line:
            continue
        if line.startswith("+"):
            line = line[1:]
        lines.append(line)
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
