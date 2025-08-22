from pathlib import Path

import pytest

from src import repo_status
from src.repo_status import status_to_emoji


def test_status_to_emoji() -> None:
    assert status_to_emoji("success") == "✅"
    assert status_to_emoji("failure") == "❌"
    # should be case-insensitive
    assert status_to_emoji("SUCCESS") == "✅"
    assert status_to_emoji("FAILURE") == "❌"
    assert status_to_emoji(None) == "❓"
    assert status_to_emoji("neutral") == "❓"


def test_status_to_emoji_strips_whitespace() -> None:
    assert status_to_emoji(" success ") == "✅"
    assert status_to_emoji("\nFAILURE\t") == "❌"


def test_status_to_emoji_failure_variants() -> None:
    assert status_to_emoji("cancelled") == "❌"
    assert status_to_emoji("TIMED_OUT") == "❌"


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
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        assert url == (
            "https://api.github.com/repos/user/repo/actions/runs?per_page=1&status=completed&event=push&branch=main"
        )
        assert "Authorization" in headers
        return DummyResp({"workflow_runs": [{"conclusion": "success"}]})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo", token="abc") == "✅"
    assert calls == [
        "https://api.github.com/repos/user/repo",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=1&status=completed&event=push&branch=main",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=1&status=completed&event=push&branch=main",
    ]


def test_fetch_repo_status_no_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append(url)
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        assert url == (
            "https://api.github.com/repos/user/repo/actions/runs?per_page=1&status=completed&event=push&branch=main"
        )
        return DummyResp({"workflow_runs": []})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo") == "❓"
    assert calls == [
        "https://api.github.com/repos/user/repo",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=1&status=completed&event=push&branch=main",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=1&status=completed&event=push&branch=main",
    ]


def test_fetch_repo_status_with_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append(url)
        assert url == (
            "https://api.github.com/repos/user/repo/actions/runs?per_page=1&status=completed&event=push&branch=dev"
        )
        return DummyResp({"workflow_runs": [{"conclusion": "success"}]})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo", branch="dev") == "✅"
    assert calls == [
        "https://api.github.com/repos/user/repo/actions/runs?per_page=1&status=completed&event=push&branch=dev",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=1&status=completed&event=push&branch=dev",
    ]


def test_fetch_repo_status_nondeterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        DummyResp({"default_branch": "main"}),
        DummyResp({"workflow_runs": [{"conclusion": "success"}]}),
        DummyResp({"workflow_runs": [{"conclusion": "failure"}]}),
    ]

    def fake_get(url: str, headers: dict, timeout: int):
        return responses.pop(0)

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    with pytest.raises(RuntimeError):
        repo_status.fetch_repo_status("user/repo")


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
    from datetime import datetime, timezone

    now = datetime(2020, 1, 2, 3, 4, tzinfo=timezone.utc)
    repo_status.update_readme(readme, now=now)

    lines = readme.read_text().splitlines()
    assert lines[3] == "_Last updated: 2020-01-02 03:04 UTC; checks hourly_"
    assert lines[4] == "- ✅ https://github.com/user/repo"


def test_update_readme_uses_current_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = "## Related Projects\n- https://github.com/user/repo\n"
    readme = tmp_path / "README.md"
    readme.write_text(content)

    def fake_status(
        repo: str, token: str | None = None, branch: str | None = None
    ) -> str:
        return "✅"

    monkeypatch.setattr(repo_status, "fetch_repo_status", fake_status)

    from datetime import datetime, timezone

    class DummyDatetime(datetime):
        @classmethod
        def now(cls, tz: timezone | None = None) -> datetime:
            return datetime(2020, 1, 2, 3, 4, tzinfo=timezone.utc)

    monkeypatch.setattr(repo_status, "datetime", DummyDatetime)
    repo_status.update_readme(readme)
    lines = readme.read_text().splitlines()
    assert lines[1] == "_Last updated: 2020-01-02 03:04 UTC; checks hourly_"
    assert lines[2] == "- ✅ https://github.com/user/repo"


def test_update_readme_existing_timestamp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = (
        "intro\n\n## Related Projects\n"
        "_Last updated: 1999-01-01 00:00 UTC; checks hourly_\n"
        "- https://github.com/user/repo\n\n"
        "## Footer\n"
    )
    readme = tmp_path / "README.md"
    readme.write_text(content)

    def fake_status(
        repo: str, token: str | None = None, branch: str | None = None
    ) -> str:
        return "✅"

    monkeypatch.setattr(repo_status, "fetch_repo_status", fake_status)

    from datetime import datetime, timezone

    now = datetime(2020, 1, 2, 3, 4, tzinfo=timezone.utc)
    repo_status.update_readme(readme, now=now)

    lines = readme.read_text().splitlines()
    assert lines[3] == "_Last updated: 2020-01-02 03:04 UTC; checks hourly_"
    assert lines[4] == "- ✅ https://github.com/user/repo"
