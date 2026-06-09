from datetime import UTC
from pathlib import Path

import pytest

from src import repo_status
from src.repo_status import status_to_emoji

REPO_ROOT = Path(__file__).resolve().parents[1]


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


def test_status_to_emoji_internal_whitespace() -> None:
    assert status_to_emoji("TIMED\tOUT") == "❌"


def test_status_to_emoji_non_string() -> None:
    """Non-string conclusions should return the unknown emoji."""
    assert status_to_emoji(123) == "❓"


def test_status_to_emoji_failure_variants() -> None:
    assert status_to_emoji("cancelled") == "❌"
    assert status_to_emoji("canceled") == "❌"
    assert status_to_emoji("TIMED_OUT") == "❌"
    assert status_to_emoji("timed-out") == "❌"
    assert status_to_emoji("timed out") == "❌"
    assert status_to_emoji("startup_failure") == "❌"
    assert status_to_emoji("STARTUP FAILURE") == "❌"
    assert status_to_emoji("action_required") == "❌"
    assert status_to_emoji("action-required") == "❌"
    assert status_to_emoji("action required") == "❌"


class DummyResp:
    def __init__(self, data, *, json_error: Exception | None = None):
        self._data = data
        self._json_error = json_error

    def raise_for_status(self) -> None:  # pragma: no cover - no error path
        pass

    def json(self) -> dict:
        if self._json_error is not None:
            raise self._json_error
        return self._data


def test_fetch_repo_status_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append(url)
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: add tests",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        assert url == (
            "https://api.github.com/repos/user/repo/actions/runs?per_page=100&status=completed&branch=main"
        )
        assert "Authorization" in headers
        data = {
            "workflow_runs": [
                {"conclusion": "success", "head_sha": "abc", "name": "tests"}
            ]
        }
        return DummyResp(data)

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo", token="abc") == "✅"
    assert calls == [
        "https://api.github.com/repos/user/repo",
        "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=100&status=completed&branch=main",
        "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=100&status=completed&branch=main",
    ]


def test_fetch_repo_status_no_runs_returns_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append(url)
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: add docs",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        assert url == (
            "https://api.github.com/repos/user/repo/actions/runs?per_page=100&status=completed&branch=main"
        )
        return DummyResp({"workflow_runs": []})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo") == "❓"
    assert calls == [
        "https://api.github.com/repos/user/repo",
        "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=100&status=completed&branch=main",
        "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=100&status=completed&branch=main",
    ]


def test_fetch_repo_status_with_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append(url)
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main", "stargazers_count": 42})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=dev&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: add tests",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        assert url == (
            "https://api.github.com/repos/user/repo/actions/runs?per_page=100&status=completed&branch=dev"
        )
        return DummyResp(
            {
                "workflow_runs": [
                    {"conclusion": "success", "head_sha": "abc", "name": "tests"}
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo", branch="dev") == "✅"
    assert calls == [
        "https://api.github.com/repos/user/repo",
        "https://api.github.com/repos/user/repo/commits?sha=dev&per_page=20",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=100&status=completed&branch=dev",
        "https://api.github.com/repos/user/repo/commits?sha=dev&per_page=20",
        "https://api.github.com/repos/user/repo/actions/runs?per_page=100&status=completed&branch=dev",
    ]


def test_fetch_repo_status_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        raise repo_status.requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo") == "❓"


def test_fetch_repo_status_invalid_commit_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(None, json_error=ValueError("bad json"))
        raise AssertionError("runs API should not be queried when commits fail")

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo") == "❓"


def test_fetch_repo_status_nondeterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    run_calls = 0

    def fake_get(url: str, headers: dict, timeout: int):
        nonlocal run_calls
        calls.append(url)
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: add tests",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        assert url == (
            "https://api.github.com/repos/user/repo/actions/runs?per_page=100&status=completed&branch=main"
        )
        run_calls += 1
        if run_calls == 1:
            return DummyResp(
                {
                    "workflow_runs": [
                        {"conclusion": "success", "head_sha": "abc", "name": "tests"}
                    ]
                }
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {"conclusion": "failure", "head_sha": "abc", "name": "tests"}
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    with pytest.raises(RuntimeError):
        repo_status.fetch_repo_status("user/repo")
    assert (
        calls.count(
            "https://api.github.com/repos/user/repo/actions/runs?per_page=100&status=completed&branch=main"
        )
        == 2
    )


def test_fetch_repo_status_ignores_non_ci_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: add tests",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {
                        "conclusion": "failure",
                        "head_sha": "abc",
                        "name": "deploy",
                    },
                    {
                        "conclusion": "success",
                        "head_sha": "abc",
                        "name": "tests",
                    },
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo") == "✅"


def test_fetch_repo_status_prefers_latest_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: add tests",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {
                        "conclusion": "failure",
                        "head_sha": "abc",
                        "name": "tests",
                        "run_attempt": 1,
                        "run_number": 42,
                        "workflow_id": 123,
                        "updated_at": "2025-09-25T12:00:00Z",
                    },
                    {
                        "conclusion": "success",
                        "head_sha": "abc",
                        "name": "tests",
                        "run_attempt": 2,
                        "run_number": 42,
                        "workflow_id": 123,
                        "updated_at": "2025-09-25T12:05:00Z",
                    },
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo") == "✅"


def test_fetch_repo_status_skips_bot_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append(url)
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "botsha",
                        "commit": {
                            "message": "chore: automated update",
                            "author": {"name": "github-actions[bot]"},
                            "committer": {"name": "github-actions[bot]"},
                        },
                        "author": {"login": "github-actions[bot]"},
                        "committer": {"login": "github-actions[bot]"},
                    },
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: add api",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    },
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {"conclusion": "success", "head_sha": "abc", "name": "tests"}
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    assert repo_status.fetch_repo_status("user/repo") == "✅"
    # ensure we queried for runs twice (two attempts)
    assert (
        calls.count(
            "https://api.github.com/repos/user/repo/actions/runs?per_page=100&status=completed&branch=main"
        )
        == 2
    )


def test_fetch_repo_status_skip_ci_message(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "skipsha",
                        "commit": {
                            "message": "docs: update [skip ci]",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    },
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: add api",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    },
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {"conclusion": "success", "head_sha": "abc", "name": "tests"}
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

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            fake_status(repo, token, branch)
        ),
    )
    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)

    lines = readme.read_text().splitlines()
    assert lines[3] == "_Last updated: 2020-01-02 03:04 UTC; checks hourly_"
    assert lines[4] == "- ✅ ⭐ ? https://github.com/user/repo"


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

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            fake_status(repo, token, branch)
        ),
    )

    from datetime import datetime, timezone

    class DummyDatetime(datetime):
        @classmethod
        def now(cls, tz: timezone | None = None) -> datetime:
            return datetime(2020, 1, 2, 3, 4, tzinfo=UTC)

    monkeypatch.setattr(repo_status, "datetime", DummyDatetime)
    repo_status.update_readme(readme)
    lines = readme.read_text().splitlines()
    assert lines[1] == "_Last updated: 2020-01-02 03:04 UTC; checks hourly_"
    assert lines[2] == "- ✅ ⭐ ? https://github.com/user/repo"


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

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            fake_status(repo, token, branch)
        ),
    )

    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)

    lines = readme.read_text().splitlines()
    assert lines[3] == "_Last updated: 2020-01-02 03:04 UTC; checks hourly_"
    assert lines[4] == "- ✅ ⭐ ? https://github.com/user/repo"


def test_fetch_repo_status_details_includes_failed_run_link(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: add failing tests",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {
                        "conclusion": "failure",
                        "head_sha": "abc",
                        "html_url": "https://github.com/user/repo/actions/runs/1",
                        "name": "tests",
                    }
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    assert repo_status.fetch_repo_status_details("user/repo") == repo_status.RepoStatus(
        "❌",
        (
            repo_status.StatusLink(
                "tests", "https://github.com/user/repo/actions/runs/1"
            ),
        ),
    )


def test_fetch_repo_status_details_orders_multiple_failure_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: fail checks",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {
                        "conclusion": "failure",
                        "head_sha": "abc",
                        "html_url": "https://github.com/user/repo/actions/runs/2",
                        "name": "tests",
                    },
                    {
                        "conclusion": "cancelled",
                        "head_sha": "abc",
                        "html_url": "https://github.com/user/repo/actions/runs/1",
                        "name": "lint",
                    },
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    report = repo_status.fetch_repo_status_details("user/repo")

    assert report == repo_status.RepoStatus(
        "❌",
        (
            repo_status.StatusLink(
                "lint", "https://github.com/user/repo/actions/runs/1"
            ),
            repo_status.StatusLink(
                "tests", "https://github.com/user/repo/actions/runs/2"
            ),
        ),
    )


def test_fetch_repo_status_details_falls_back_to_actions_run_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: fail checks",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {
                        "conclusion": "timed_out",
                        "head_sha": "abc",
                        "id": 123,
                        "name": "build",
                    }
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    assert repo_status.fetch_repo_status_details("user/repo") == repo_status.RepoStatus(
        "❌",
        (
            repo_status.StatusLink(
                "build", "https://github.com/user/repo/actions/runs/123"
            ),
        ),
    )


def test_fetch_repo_status_details_omits_unlinkable_failed_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: fail checks",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {"conclusion": "failure", "head_sha": "abc", "name": "tests"}
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    assert repo_status.fetch_repo_status_details("user/repo") == repo_status.RepoStatus(
        "❌"
    )


def test_fetch_repo_status_details_links_only_failed_workflows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: mixed checks",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {
                        "conclusion": "success",
                        "head_sha": "abc",
                        "html_url": "https://github.com/user/repo/actions/runs/1",
                        "name": "tests",
                    },
                    {
                        "conclusion": "failure",
                        "head_sha": "abc",
                        "html_url": "https://github.com/user/repo/actions/runs/2",
                        "name": "lint",
                    },
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    assert repo_status.fetch_repo_status_details("user/repo") == repo_status.RepoStatus(
        "❌",
        (
            repo_status.StatusLink(
                "lint", "https://github.com/user/repo/actions/runs/2"
            ),
        ),
    )


def test_fetch_repo_status_details_success_and_unknown_have_no_links(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: pass checks",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {
                        "conclusion": "success",
                        "head_sha": "abc",
                        "html_url": "https://github.com/user/repo/actions/runs/1",
                        "name": "tests",
                    }
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    assert repo_status.fetch_repo_status_details("user/repo") == repo_status.RepoStatus(
        "✅"
    )
    monkeypatch.setattr(
        repo_status.requests,
        "get",
        lambda url, headers, timeout: DummyResp({}, json_error=ValueError("bad json")),
    )
    assert repo_status.fetch_repo_status_details("user/repo") == repo_status.RepoStatus(
        "❓"
    )


def test_fetch_repo_status_details_prefers_latest_attempt_without_stale_link(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: retry checks",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {
                        "conclusion": "failure",
                        "head_sha": "abc",
                        "html_url": "https://github.com/user/repo/actions/runs/1",
                        "name": "tests",
                        "run_attempt": 1,
                        "run_number": 42,
                        "workflow_id": 123,
                        "updated_at": "2025-09-25T12:00:00Z",
                    },
                    {
                        "conclusion": "success",
                        "head_sha": "abc",
                        "html_url": "https://github.com/user/repo/actions/runs/1/attempts/2",
                        "name": "tests",
                        "run_attempt": 2,
                        "run_number": 42,
                        "workflow_id": 123,
                        "updated_at": "2025-09-25T12:05:00Z",
                    },
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    assert repo_status.fetch_repo_status_details("user/repo") == repo_status.RepoStatus(
        "✅"
    )


def test_update_readme_includes_failure_links_and_removes_duplicates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = (
        "## Related Projects\n"
        "_Last updated: 1999-01-01 00:00 UTC; checks hourly_\n"
        "_Last updated: 1998-01-01 00:00 UTC; checks hourly_\n"
        "- ✅ https://github.com/user/repo (failing runs: https://old.example/run)\n"
    )
    readme = tmp_path / "README.md"
    readme.write_text(content)

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "tests", "https://github.com/user/repo/actions/runs/1"
                ),
                repo_status.StatusLink(
                    "lint", "https://github.com/user/repo/actions/runs/2"
                ),
            ),
        ),
    )
    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)

    lines = readme.read_text().splitlines()
    assert lines == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        (
            "- ❌ ([tests](https://github.com/user/repo/actions/runs/1), "
            "[lint](https://github.com/user/repo/actions/runs/2)) "
            "<!-- repo-status:failure-links --> ⭐ ? https://github.com/user/repo"
        ),
    ]


def test_update_readme_strips_linked_failure_prefixes_idempotently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = (
        "## Related Projects\n"
        "_Last updated: 1999-01-01 00:00 UTC; checks hourly_\n"
        "_Last updated: 1998-01-01 00:00 UTC; checks hourly_\n"
        "- ❌ ([old tests](https://github.com/user/repo/actions/runs/0), "
        "[old lint](https://github.com/user/repo/actions/runs/9)) "
        "❌ ✅ **[repo](https://github.com/user/repo)** - description\n"
    )
    readme = tmp_path / "README.md"
    readme.write_text(content)

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "tests", "https://github.com/user/repo/actions/runs/1"
                ),
                repo_status.StatusLink(
                    "lint", "https://github.com/user/repo/actions/runs/2"
                ),
            ),
        ),
    )
    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)
    first = readme.read_text()
    repo_status.update_readme(readme, now=now)

    assert readme.read_text() == first
    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        (
            "- ❌ ([tests](https://github.com/user/repo/actions/runs/1), "
            "[lint](https://github.com/user/repo/actions/runs/2)) "
            "<!-- repo-status:failure-links --> "
            "⭐ ? **[repo](https://github.com/user/repo)** - description"
        ),
    ]


def test_update_readme_uses_status_details_not_compatibility_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("## Related Projects\n- https://github.com/user/repo\n")

    def fail_report(*args, **kwargs):
        raise AssertionError("update_readme should use fetch_repo_status_details")

    monkeypatch.setattr(repo_status, "fetch_repo_status_report", fail_report)
    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "tests", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        ),
    )
    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)

    assert (
        "- ❌ ([tests](https://github.com/user/repo/actions/runs/1)) "
        "<!-- repo-status:failure-links --> ⭐ ? https://github.com/user/repo"
    ) in readme.read_text().splitlines()


def test_fetch_repo_status_report_returns_url_strings_for_compatibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: fail checks",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {
                        "conclusion": "failure",
                        "head_sha": "abc",
                        "html_url": "https://github.com/user/repo/actions/runs/1",
                        "name": "tests",
                    }
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    report = repo_status.fetch_repo_status_report("user/repo", attempts=1)

    assert report == repo_status.RepoStatusReport(
        "❌", ("https://github.com/user/repo/actions/runs/1",)
    )
    assert (
        ", ".join(report.failure_links) == "https://github.com/user/repo/actions/runs/1"
    )


def test_fetch_repo_status_details_collapses_renamed_latest_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: rerun renamed check",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {
                        "conclusion": "failure",
                        "head_sha": "abc",
                        "html_url": "https://github.com/user/repo/actions/runs/1",
                        "name": "tests",
                        "run_attempt": 1,
                        "run_number": 42,
                        "workflow_id": 123,
                        "updated_at": "2025-09-25T12:00:00Z",
                    },
                    {
                        "conclusion": "success",
                        "head_sha": "abc",
                        "html_url": "https://github.com/user/repo/actions/runs/1/attempts/2",
                        "name": "CI",
                        "run_attempt": 2,
                        "run_number": 42,
                        "workflow_id": 123,
                        "updated_at": "2025-09-25T12:05:00Z",
                    },
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    assert repo_status.fetch_repo_status_details(
        "user/repo", attempts=1
    ) == repo_status.RepoStatus("✅")


def test_fetch_repo_status_details_disambiguates_same_name_and_run_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp(
                [
                    {
                        "sha": "abc",
                        "commit": {
                            "message": "feat: fail duplicate checks",
                            "author": {"name": "Alice"},
                            "committer": {"name": "Alice"},
                        },
                        "author": {"login": "alice"},
                        "committer": {"login": "alice"},
                    }
                ]
            )
        return DummyResp(
            {
                "workflow_runs": [
                    {
                        "conclusion": "failure",
                        "head_sha": "abc",
                        "html_url": "https://github.com/user/repo/actions/runs/1",
                        "id": 1,
                        "name": "CI",
                        "run_number": 42,
                        "workflow_id": 101,
                    },
                    {
                        "conclusion": "failure",
                        "head_sha": "abc",
                        "html_url": "https://github.com/user/repo/actions/runs/2",
                        "id": 2,
                        "name": "CI",
                        "run_number": 42,
                        "workflow_id": 102,
                    },
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    report = repo_status.fetch_repo_status_details("user/repo", attempts=1)

    assert report.failure_links == (
        repo_status.StatusLink(
            "CI #42 workflow 101", "https://github.com/user/repo/actions/runs/1"
        ),
        repo_status.StatusLink(
            "CI #42 workflow 102", "https://github.com/user/repo/actions/runs/2"
        ),
    )
    assert len({link.label for link in report.failure_links}) == len(
        report.failure_links
    )


def test_update_readme_strips_escaped_failure_label_idempotently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ❌ ([bad\\]name](https://github.com/user/repo/actions/runs/0)) "
        "<!-- repo-status:failure-links --> https://github.com/user/repo\n"
    )

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "bad]name", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        ),
    )
    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)
    first = readme.read_text()
    repo_status.update_readme(readme, now=now)

    assert readme.read_text() == first
    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        "- ❌ ([bad\\]name](https://github.com/user/repo/actions/runs/1)) "
        "<!-- repo-status:failure-links --> ⭐ ? https://github.com/user/repo",
    ]


def test_update_readme_strips_bracketed_failure_label_idempotently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ❌ ([CI [lint\\]](https://github.com/user/repo/actions/runs/0)) "
        "<!-- repo-status:failure-links --> https://github.com/user/repo\n"
    )

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "CI [lint]", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        ),
    )
    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)
    first = readme.read_text()
    repo_status.update_readme(readme, now=now)

    assert readme.read_text() == first
    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        "- ❌ ([CI [lint\\]](https://github.com/user/repo/actions/runs/1)) "
        "<!-- repo-status:failure-links --> ⭐ ? https://github.com/user/repo",
    ]


def test_update_readme_migrates_legacy_unmarked_failure_links_before_raw_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ❌ ([old tests](https://github.com/user/repo/actions/runs/0)) "
        "https://github.com/user/repo\n"
    )

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "tests", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        ),
    )
    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)
    first = readme.read_text()
    repo_status.update_readme(readme, now=now)

    assert readme.read_text() == first
    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        "- ❌ ([tests](https://github.com/user/repo/actions/runs/1)) "
        "<!-- repo-status:failure-links --> ⭐ ? https://github.com/user/repo",
    ]


def test_update_readme_preserves_hand_authored_leading_notes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ✅ (archived) **[repo](https://github.com/user/repo)** - desc\n"
        "- ([docs](https://example.com)) "
        "**[docs-repo](https://github.com/user/docs-repo)** - desc\n"
        "- ❌ ([debug run](https://github.com/user/debug-repo/actions/runs/123)) "
        "**[debug-repo](https://github.com/user/debug-repo)** - desc\n"
    )

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus("✅"),
    )
    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)
    first = readme.read_text()
    repo_status.update_readme(readme, now=now)

    assert readme.read_text() == first
    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        "- ✅ ⭐ ? ([debug run](https://github.com/user/debug-repo/actions/runs/123)) "
        "**[debug-repo](https://github.com/user/debug-repo)** - desc",
        "- ✅ ⭐ ? ([docs](https://example.com)) "
        "**[docs-repo](https://github.com/user/docs-repo)** - desc",
        "- ✅ ⭐ ? (archived) **[repo](https://github.com/user/repo)** - desc",
    ]


def test_update_readme_preserves_hand_authored_run_note_before_raw_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ❌ ([debug run](https://github.com/user/repo/actions/runs/123)) "
        "https://github.com/user/repo - desc\n"
    )

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus("✅"),
    )
    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)
    first = readme.read_text()
    repo_status.update_readme(readme, now=now)

    assert readme.read_text() == first
    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        "- ✅ ⭐ ? ([debug run](https://github.com/user/repo/actions/runs/123)) "
        "https://github.com/user/repo - desc",
    ]


def test_profile_readme_related_projects_copy_is_parseable() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("## Related Projects", 1)[1].split("\n## ", 1)[0]

    assert section.count("_Last updated:") == 1
    assert "tests/test_" not in section
    assert "failing runs:" not in section
    assert "✅ latest relevant run succeeded" in section
    assert "❌ one or more relevant runs need attention" in section
    assert (
        "❓ no completed relevant run was found or GitHub could not be queried"
        in section
    )
    assert readme.count("docs/repository-guide.md") == 1

    project_lines = [line for line in section.splitlines() if line.startswith("- ")]
    assert project_lines
    assert all(repo_status.GITHUB_RE.search(line) for line in project_lines)


def test_update_readme_renders_star_counts_and_sorts_projects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ✅ ⭐ 1 **[zero](https://github.com/user/zero)** - desc\n"
        "- ❓ ⭐ ? **[alpha](https://github.com/user/alpha)** - desc\n"
        "- ❌ ([old](https://github.com/user/bravo/actions/runs/0)) "
        "<!-- repo-status:failure-links --> ⭐ 999 "
        "**[bravo](https://github.com/user/bravo)** - desc\n"
    )

    statuses = {
        "zero": repo_status.RepoStatus("✅", stars=0),
        "alpha": repo_status.RepoStatus("✅", stars=7),
        "bravo": repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "tests", "https://github.com/user/bravo/actions/runs/1"
                ),
            ),
            stars=7,
        ),
    }

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: statuses[repo.rsplit("/", 1)[1]],
    )
    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)
    first = readme.read_text()
    repo_status.update_readme(readme, now=now)

    assert readme.read_text() == first
    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        "- ✅ ⭐ 7 **[alpha](https://github.com/user/alpha)** - desc",
        "- ❌ ([tests](https://github.com/user/bravo/actions/runs/1)) "
        "<!-- repo-status:failure-links --> ⭐ 7 "
        "**[bravo](https://github.com/user/bravo)** - desc",
        "- ✅ ⭐ 0 **[zero](https://github.com/user/zero)** - desc",
    ]


def test_update_readme_unknown_stars_sort_after_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- **[unknown](https://github.com/user/unknown)** - desc\n"
        "- **[zero](https://github.com/user/zero)** - desc\n"
    )
    statuses = {
        "unknown": repo_status.RepoStatus("✅", stars=None),
        "zero": repo_status.RepoStatus("✅", stars=0),
    }
    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: statuses[repo.rsplit("/", 1)[1]],
    )
    from datetime import datetime

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert readme.read_text().splitlines()[2:] == [
        "- ✅ ⭐ 0 **[zero](https://github.com/user/zero)** - desc",
        "- ✅ ⭐ ? **[unknown](https://github.com/user/unknown)** - desc",
    ]


def test_update_readme_preserves_multiline_and_external_repo_links(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- **[Website](https://example.com)** - desc "
        "([repo](https://github.com/user/site))\n"
        "  continued detail\n"
        "- **[Tool](https://github.com/user/tool)** - desc\n"
        "  tool continuation\n"
    )
    statuses = {
        "site": repo_status.RepoStatus("✅", stars=5),
        "tool": repo_status.RepoStatus("✅", stars=10),
    }
    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: statuses[repo.rsplit("/", 1)[1]],
    )
    from datetime import datetime

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        "- ✅ ⭐ 10 **[Tool](https://github.com/user/tool)** - desc",
        "  tool continuation",
        "- ✅ ⭐ 5 **[Website](https://example.com)** - desc "
        "([repo](https://github.com/user/site))",
        "  continued detail",
    ]


def test_fetch_repo_metadata_handles_invalid_stars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        repo_status.requests,
        "get",
        lambda url, headers, timeout: DummyResp(
            {"default_branch": "main", "stargazers_count": "42"}
        ),
    )

    assert repo_status.fetch_repo_metadata("user/repo") == repo_status.RepoMetadata(
        default_branch="main", stars=None
    )


def test_update_readme_branch_url_checks_branch_but_fetches_repo_stars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- **[repo](https://github.com/user/repo/tree/dev)** - desc\n"
    )
    calls: list[tuple[str, str | None]] = []

    def fake_status(repo: str, token=None, branch=None):
        calls.append((repo, branch))
        return repo_status.RepoStatus("✅", stars=42)

    monkeypatch.setattr(repo_status, "fetch_repo_status_details", fake_status)
    from datetime import datetime

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert calls == [("user/repo", "dev")]
    assert (
        "- ✅ ⭐ 42 **[repo](https://github.com/user/repo/tree/dev)** - desc"
        in readme.read_text().splitlines()
    )


def test_update_readme_leaves_non_project_bullets_in_place(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "Intro prose.\n"
        "- not a GitHub project\n"
        "- **[Beta](https://github.com/user/beta)** - desc\n"
        "- **[Alpha](https://github.com/user/alpha)** - desc\n"
        "Closing prose.\n"
    )
    statuses = {
        "alpha": repo_status.RepoStatus("✅", stars=2),
        "beta": repo_status.RepoStatus("✅", stars=1),
    }
    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: statuses[repo.rsplit("/", 1)[1]],
    )
    from datetime import datetime

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        "Intro prose.",
        "- not a GitHub project",
        "- ✅ ⭐ 2 **[Alpha](https://github.com/user/alpha)** - desc",
        "- ✅ ⭐ 1 **[Beta](https://github.com/user/beta)** - desc",
        "Closing prose.",
    ]
