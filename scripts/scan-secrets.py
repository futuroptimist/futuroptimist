#!/usr/bin/env python3
"""Detect potential secrets in staged diffs.

Reads unified diff content from ``stdin`` and scans only the **added** lines for
secret-like patterns such as AWS keys, private keys, generic API key
assignments, GitHub tokens (``ghp_…`` or ``github_pat_…``), and Slack tokens
(``xoxb-…``). The scan is intentionally lightweight and should be supplemented
with dedicated tools for thorough auditing.
"""
from __future__ import annotations

import re
import sys

PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
    re.compile(r"(?i)(api_key|apikey|password|secret)[\s:=]+[^\n]+"),
    re.compile(r"gh[pousr]_[0-9A-Za-z]{36}"),
    re.compile(r"github_pat_[0-9A-Za-z_]{22}_[0-9A-Za-z]{59}"),
    re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,48}"),
    # US SSN-like patterns (simple heuristic)
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
]


def _luhn_ok(digits: str) -> bool:
    total = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        n = ord(ch) - 48
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


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
    # Credit card detection: gather 13-19 digit sequences (ignore separators), Luhn validate
    cc_candidates = re.findall(r"(?:\b[\d][\d -]{11,}\d\b)", content)
    for raw in cc_candidates:
        digits = re.sub(r"[^0-9]", "", raw)
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            matches.append(digits)
    if matches:
        sys.stderr.write("Possible secrets detected:\n")
        for m in matches:
            sys.stderr.write(f"{m}\n")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
