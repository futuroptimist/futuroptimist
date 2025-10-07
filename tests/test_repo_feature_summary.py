from __future__ import annotations

from pathlib import Path


def test_repo_feature_summary_exists() -> None:
    summary_path = Path("docs/repo-feature-summary.md")
    assert summary_path.exists(), "docs/repo-feature-summary.md must exist"
    content = summary_path.read_text(encoding="utf-8")
    assert "# Repo Feature Summary" in content

    lines = [line.strip() for line in content.splitlines()]
    assert "| Feature | Status | Notes |" in lines
    header_index = lines.index("| Feature | Status | Notes |")
    assert lines[header_index + 1].startswith("| ----")

    data_lines: list[str] = []
    for line in lines[header_index + 2 :]:
        if not line.startswith("|"):
            break
        data_lines.append(line)
    assert data_lines, "Feature table must contain at least one row"
