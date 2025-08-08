from pathlib import Path

import pytest

from src import repo_status
from src.repo_status import status_to_emoji


def test_status_to_emoji() -> None:
    assert status_to_emoji("success") == "✅"
    assert status_to_emoji("failure") == "❌"
    assert status_to_emoji(None) == "❌"


class DummyResp:
    def __init__(self, data: dict):
        self._data = data

    def raise_for_status(self) -> None:  # pragma: no cover - no error path
        pass

    def json(self) -> dict:
        return self._data


def test_fetch_repo_status_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        assert "Authorization" in headers
        return DummyResp({"workflow_runs": [{"conclusion": "success"}]})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo", token="abc") == "✅"


def test_fetch_repo_status_no_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        return DummyResp({"workflow_runs": []})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo") == "❌"


def test_update_readme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    content = (
        "intro\n\n## Related Projects\n"
        "- https://github.com/user/repo\n"
        "- ❌ https://github.com/other/repo/tree/dev\n\n## Footer\n"
    )
    readme = tmp_path / "README.md"
    readme.write_text(content)

    calls: list[tuple[str, str | None]] = []

    def fake_status(
        repo: str, token: str | None = None, branch: str | None = None
    ) -> str:
        calls.append((repo, branch))
        return {"user/repo": "✅", "other/repo": "❌"}[repo]

    monkeypatch.setattr(repo_status, "fetch_repo_status", fake_status)
    repo_status.update_readme(readme)

    lines = readme.read_text().splitlines()
    assert lines[3] == "- ✅ https://github.com/user/repo"
    assert lines[4] == "- ❌ https://github.com/other/repo/tree/dev"
    assert lines[6] == "## Footer"
    assert calls == [("user/repo", None), ("other/repo", "dev")]
