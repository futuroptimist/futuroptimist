from pathlib import Path

import pytest

from src import repo_status
from src.repo_status import status_to_emoji


def test_status_to_emoji() -> None:
    assert status_to_emoji("success") == "✅"
    assert status_to_emoji("failure") == "❌"
    assert status_to_emoji(None) == "❓"
    assert status_to_emoji("neutral") == "❓"


class DummyResp:
    def __init__(self, data: dict):
        self._data = data

    def raise_for_status(self) -> None:  # pragma: no cover - no error path
        pass

    def json(self) -> dict:
        return self._data


def test_fetch_repo_status_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append(url)
        assert url == (
            "https://api.github.com/repos/user/repo/actions/runs?per_page=10&status=completed"
        )
        assert "Authorization" in headers
        return DummyResp({"workflow_runs": [{"conclusion": "success"}]})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo", token="abc") == "✅"
    assert calls == [
        "https://api.github.com/repos/user/repo/actions/runs?per_page=10&status=completed",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=10&status=completed",
    ]


def test_fetch_repo_status_no_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append(url)
        assert url == (
            "https://api.github.com/repos/user/repo/actions/runs?per_page=10&status=completed"
        )
        return DummyResp({"workflow_runs": []})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo") == "❓"
    assert calls == [
        "https://api.github.com/repos/user/repo/actions/runs?per_page=10&status=completed",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=10&status=completed",
    ]


def test_fetch_repo_status_with_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append(url)
        assert url == (
            "https://api.github.com/repos/user/repo/actions/runs?per_page=10&status=completed&branch=dev"
        )
        return DummyResp({"workflow_runs": [{"conclusion": "success"}]})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo", branch="dev") == "✅"
    assert calls == [
        "https://api.github.com/repos/user/repo/actions/runs?per_page=10&status=completed&branch=dev",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=10&status=completed&branch=dev",
    ]


def test_fetch_repo_status_nondeterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        {"workflow_runs": [{"conclusion": "success"}]},
        {"workflow_runs": [{"conclusion": "failure"}]},
    ]

    def fake_get(url: str, headers: dict, timeout: int):
        return DummyResp(responses.pop(0))

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    with pytest.raises(RuntimeError):
        repo_status.fetch_repo_status("user/repo")


def test_fetch_repo_status_ignores_non_ci_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        return DummyResp(
            {
                "workflow_runs": [
                    {"conclusion": "skipped", "event": "issue_comment"},
                    {"conclusion": "success", "event": "push"},
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo") == "✅"


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
