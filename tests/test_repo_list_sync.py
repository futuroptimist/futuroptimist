from __future__ import annotations

from pathlib import Path


def _read_entries(path: Path) -> list[str]:
    entries: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            entries.append(line)
    return entries


def test_prompt_repo_lists_match() -> None:
    repos_from = Path("dict/prompt-doc-repos.txt")
    repo_list = Path("docs/repo_list.txt")

    assert repos_from.exists(), "dict/prompt-doc-repos.txt must exist"
    assert repo_list.exists(), "docs/repo_list.txt must exist"

    repos_entries = _read_entries(repos_from)
    list_entries = _read_entries(repo_list)

    assert list_entries == repos_entries, (
        "docs/repo_list.txt must match dict/prompt-doc-repos.txt. "
        f"Expected {repos_entries}, got {list_entries}."
    )
