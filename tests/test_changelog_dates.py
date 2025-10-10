from __future__ import annotations

from datetime import date
from pathlib import Path
import re


def test_changelog_entries_are_not_future_dated() -> None:
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8").splitlines()
    today = date.today()
    future_entries: list[str] = []

    heading_pattern = re.compile(r"^## (\d{4}-\d{2}-\d{2})$")

    for line in changelog:
        match = heading_pattern.match(line.strip())
        if match:
            entry_date = date.fromisoformat(match.group(1))
            if entry_date > today:
                future_entries.append(match.group(1))

    assert (
        not future_entries
    ), "CHANGELOG.md contains future-dated entries: " + ", ".join(future_entries)
