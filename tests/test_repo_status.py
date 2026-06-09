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


def _commit(sha: str = "abc", message: str = "feat: update") -> dict:
    return {
        "sha": sha,
        "commit": {
            "message": message,
            "author": {"name": "Alice"},
            "committer": {"name": "Alice"},
        },
        "author": {"login": "alice"},
        "committer": {"login": "alice"},
    }


def _mock_repo_status_api(
    monkeypatch: pytest.MonkeyPatch,
    runs: list[dict],
    *,
    branch: str = "main",
    default_branch: str = "main",
    commits: list[dict] | None = None,
) -> None:
    commits = commits if commits is not None else [_commit("new"), _commit("old")]

    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": default_branch})
        if url.startswith(
            f"https://api.github.com/repos/user/repo/commits?sha={branch}&per_page=20"
        ):
            return DummyResp(commits)
        assert url == (
            "https://api.github.com/repos/user/repo/actions/runs?"
            f"per_page=100&status=completed&branch={branch}"
        )
        return DummyResp({"workflow_runs": runs})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)


def _run(
    conclusion: str,
    *,
    name: str = "CI",
    workflow_id: int | None = 1,
    path: str | None = None,
    head_sha: str = "new",
    head_branch: str = "main",
    run_number: int = 1,
    run_attempt: int = 1,
    created_at: str = "2026-01-01T00:00:00Z",
    run_id: int | None = None,
) -> dict:
    run = {
        "conclusion": conclusion,
        "created_at": created_at,
        "head_branch": head_branch,
        "head_sha": head_sha,
        "html_url": f"https://github.com/user/repo/actions/runs/{run_id or run_number}",
        "name": name,
        "run_attempt": run_attempt,
        "run_number": run_number,
        "updated_at": created_at,
    }
    if workflow_id is not None:
        run["workflow_id"] = workflow_id
    if path is not None:
        run["path"] = path
    if run_id is not None:
        run["id"] = run_id
    return run


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


def test_fetch_repo_status_newer_success_overrides_failure_by_workflow_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_api(
        monkeypatch,
        [
            _run(
                "failure",
                workflow_id=42,
                head_sha="old",
                run_number=9,
                created_at="2026-01-01T00:00:00Z",
            ),
            _run(
                "success",
                workflow_id=42,
                head_sha="new",
                run_number=10,
                created_at="2026-01-02T00:00:00Z",
            ),
        ],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_newer_success_overrides_failure_by_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_api(
        monkeypatch,
        [
            _run(
                "failure",
                workflow_id=None,
                path=".github/workflows/ci.yml",
                head_sha="old",
                run_number=4,
                created_at="2026-01-01T00:00:00Z",
            ),
            _run(
                "success",
                workflow_id=None,
                path=".github/workflows/CI.yml",
                head_sha="new",
                run_number=5,
                created_at="2026-01-02T00:00:00Z",
            ),
        ],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_newer_success_overrides_failure_by_normalized_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_api(
        monkeypatch,
        [
            _run(
                "failure",
                name="Update   Repo Statuses",
                workflow_id=None,
                head_sha="old",
                run_number=4,
                created_at="2026-01-01T00:00:00Z",
            ),
            _run(
                "success",
                name="update repo statuses",
                workflow_id=None,
                head_sha="new",
                run_number=5,
                created_at="2026-01-02T00:00:00Z",
            ),
        ],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_unrelated_name_does_not_override_current_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_api(
        monkeypatch,
        [
            _run(
                "failure",
                name="CI",
                workflow_id=None,
                head_sha="old",
                run_number=4,
                created_at="2026-01-01T00:00:00Z",
                run_id=4,
            ),
            _run(
                "success",
                name="Release",
                workflow_id=None,
                head_sha="new",
                run_number=5,
                created_at="2026-01-02T00:00:00Z",
                run_id=5,
            ),
        ],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "CI", "https://github.com/user/repo/actions/runs/4"
                ),
            ),
        )
    )


def test_fetch_repo_status_newer_different_workflow_success_does_not_hide_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_api(
        monkeypatch,
        [
            _run(
                "failure",
                name="CI",
                workflow_id=1,
                head_sha="old",
                run_number=4,
                created_at="2026-01-01T00:00:00Z",
                run_id=4,
            ),
            _run(
                "success",
                name="Build",
                workflow_id=2,
                head_sha="new",
                run_number=5,
                created_at="2026-01-02T00:00:00Z",
                run_id=5,
            ),
        ],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "CI", "https://github.com/user/repo/actions/runs/4"
                ),
            ),
        )
    )


def test_fetch_repo_status_newer_different_branch_success_does_not_override_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_api(
        monkeypatch,
        [
            _run(
                "failure",
                workflow_id=1,
                head_branch="main",
                run_number=4,
                created_at="2026-01-01T00:00:00Z",
                run_id=4,
            ),
            _run(
                "success",
                workflow_id=1,
                head_branch="dev",
                run_number=5,
                created_at="2026-01-02T00:00:00Z",
                run_id=5,
            ),
        ],
        branch="main",
    )

    assert repo_status.fetch_repo_status_details(
        "user/repo", branch="main", attempts=1
    ) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "CI", "https://github.com/user/repo/actions/runs/4"
                ),
            ),
        )
    )


def test_fetch_repo_status_bot_success_can_stale_normal_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot_commit = {
        "sha": "new",
        "commit": {
            "message": "chore: automated status refresh",
            "author": {"name": "github-actions[bot]"},
            "committer": {"name": "github-actions[bot]"},
        },
        "author": {"login": "github-actions[bot]"},
        "committer": {"login": "github-actions[bot]"},
    }
    _mock_repo_status_api(
        monkeypatch,
        [
            _run(
                "failure",
                workflow_id=1,
                head_sha="old",
                run_number=4,
                created_at="2026-01-01T00:00:00Z",
            ),
            _run(
                "success",
                workflow_id=1,
                head_sha="new",
                run_number=5,
                created_at="2026-01-02T00:00:00Z",
            ),
        ],
        commits=[bot_commit, _commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_latest_failure_links_newer_run_after_older_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_api(
        monkeypatch,
        [
            _run(
                "success",
                workflow_id=1,
                head_sha="old",
                run_number=4,
                created_at="2026-01-01T00:00:00Z",
                run_id=4,
            ),
            _run(
                "failure",
                workflow_id=1,
                head_sha="new",
                run_number=5,
                created_at="2026-01-02T00:00:00Z",
                run_id=5,
            ),
        ],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "CI", "https://github.com/user/repo/actions/runs/5"
                ),
            ),
        )
    )


def test_fetch_repo_status_multiple_workflows_link_only_latest_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_api(
        monkeypatch,
        [
            _run(
                "failure",
                name="CI",
                workflow_id=1,
                head_sha="old",
                run_number=1,
                created_at="2026-01-01T00:00:00Z",
                run_id=1,
            ),
            _run(
                "success",
                name="CI",
                workflow_id=1,
                head_sha="new",
                run_number=2,
                created_at="2026-01-02T00:00:00Z",
                run_id=2,
            ),
            _run(
                "failure",
                name="Lint",
                workflow_id=2,
                head_sha="new",
                run_number=7,
                created_at="2026-01-02T00:00:00Z",
                run_id=7,
            ),
        ],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Lint", "https://github.com/user/repo/actions/runs/7"
                ),
            ),
        )
    )


def test_update_readme_flywheel_regression_suppresses_stale_failure_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ❌ ([Update Repo Statuses]"
        "(https://github.com/futuroptimist/flywheel/actions/runs/27123196602)) "
        "<!-- repo-status:failure-links --> ⭐ 2 "
        "**[flywheel](https://github.com/futuroptimist/flywheel)** - template\n"
    )

    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/futuroptimist/flywheel":
            return DummyResp({"default_branch": "main", "stargazers_count": 2})
        if url.startswith(
            "https://api.github.com/repos/futuroptimist/flywheel/commits?sha=main&per_page=20"
        ):
            return DummyResp([_commit("new"), _commit("old")])
        assert url == (
            "https://api.github.com/repos/futuroptimist/flywheel/actions/runs?"
            "per_page=100&status=completed&branch=main"
        )
        return DummyResp(
            {
                "workflow_runs": [
                    {
                        "conclusion": "failure",
                        "created_at": "2026-06-08T00:00:00Z",
                        "head_branch": "main",
                        "head_sha": "old",
                        "html_url": "https://github.com/futuroptimist/flywheel/actions/runs/27123196602",
                        "name": "Update Repo Statuses",
                        "run_attempt": 1,
                        "run_number": 14,
                        "updated_at": "2026-06-08T00:01:00Z",
                        "workflow_id": 123,
                    },
                    {
                        "conclusion": "success",
                        "created_at": "2026-06-09T00:00:00Z",
                        "head_branch": "main",
                        "head_sha": "new",
                        "html_url": "https://github.com/futuroptimist/flywheel/actions/runs/27199999999",
                        "name": "Update Repo Statuses",
                        "run_attempt": 1,
                        "run_number": 15,
                        "updated_at": "2026-06-09T00:01:00Z",
                        "workflow_id": 123,
                    },
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)
    from datetime import datetime

    repo_status.update_readme(readme, now=datetime(2026, 6, 9, 1, 2, tzinfo=UTC))

    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2026-06-09 01:02 UTC; checks hourly_",
        "- ✅ ⭐ 2 **[flywheel](https://github.com/futuroptimist/flywheel)** - template",
    ]


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
            fake_status(repo, token, branch),
            stars={"user/repo": 2, "other/repo": 1}.get(repo),
        ),
    )
    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)

    lines = readme.read_text().splitlines()
    assert lines[3] == "_Last updated: 2020-01-02 03:04 UTC; checks hourly_"
    assert lines[4] == "- ✅ ⭐ 2 https://github.com/user/repo"


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
        "- ✅ ⭐ ? https://github.com/user/repo (failing runs: https://old.example/run)\n"
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
        "<!-- repo-status:failure-links --> ⭐ ? https://github.com/user/repo\n"
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
        "<!-- repo-status:failure-links --> ⭐ ? https://github.com/user/repo\n"
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
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "✅",
            stars={"user/repo": 3, "user/docs-repo": 2, "user/debug-repo": 1}[repo],
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
        "- ✅ ⭐ 3 (archived) **[repo](https://github.com/user/repo)** - desc",
        "- ✅ ⭐ 2 ([docs](https://example.com)) "
        "**[docs-repo](https://github.com/user/docs-repo)** - desc",
        "- ✅ ⭐ 1 ([debug run](https://github.com/user/debug-repo/actions/runs/123)) "
        "**[debug-repo](https://github.com/user/debug-repo)** - desc",
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
    assert "⭐ shows GitHub stars" in section
    assert "Projects sort by stars descending" in section
    assert readme.count("docs/repository-guide.md") == 1

    project_lines = [line for line in section.splitlines() if line.startswith("- ")]
    assert project_lines
    assert all(repo_status.GITHUB_RE.search(line) for line in project_lines)
    assert all("⭐" in line for line in project_lines)


def test_fetch_repo_status_details_includes_star_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main", "stargazers_count": 42})
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
                    {"conclusion": "success", "head_sha": "abc", "name": "tests"}
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    assert repo_status.fetch_repo_status_details(
        "user/repo", attempts=1
    ) == repo_status.RepoStatus("✅", stars=42)


def test_format_star_count_handles_unknowns() -> None:
    assert repo_status.format_star_count(42) == "⭐ 42"
    assert repo_status.format_star_count(None) == "⭐ ?"


def test_fetch_repo_metadata_invalid_star_count_is_unknown(
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


def test_update_readme_sorts_by_stars_then_name_and_unknowns_last(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- **[Zero](https://github.com/user/zero)** - zero stars\n"
        "- **[Beta](https://github.com/user/beta)** - same stars\n"
        "- **[alpha](https://github.com/user/alpha)** - same stars\n"
        "- **[Unknown](https://github.com/user/unknown)** - unknown stars\n"
    )

    stars = {"user/zero": 0, "user/beta": 5, "user/alpha": 5, "user/unknown": None}
    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "✅", stars=stars[repo]
        ),
    )
    from datetime import datetime

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert readme.read_text().splitlines()[2:] == [
        "- ✅ ⭐ 5 **[alpha](https://github.com/user/alpha)** - same stars",
        "- ✅ ⭐ 5 **[Beta](https://github.com/user/beta)** - same stars",
        "- ✅ ⭐ 0 **[Zero](https://github.com/user/zero)** - zero stars",
        "- ✅ ⭐ ? **[Unknown](https://github.com/user/unknown)** - unknown stars",
    ]


def test_update_readme_star_and_failure_prefix_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ❌ ([old tests](https://github.com/user/repo/actions/runs/0)) "
        "<!-- repo-status:failure-links --> ⭐ 1 ⭐ 999 "
        "**[repo](https://github.com/user/repo)** - desc\n"
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
            stars=7,
        ),
    )
    from datetime import datetime

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))
    first = readme.read_text()
    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert readme.read_text() == first
    assert readme.read_text().splitlines()[2] == (
        "- ❌ ([tests](https://github.com/user/repo/actions/runs/1)) "
        "<!-- repo-status:failure-links --> ⭐ 7 "
        "**[repo](https://github.com/user/repo)** - desc"
    )


def test_update_readme_preserves_multiline_and_external_display_links(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "Intro stays put.\n"
        "- **[token.place](https://token.place)** - external first "
        "([repo](https://github.com/futuroptimist/token.place))\n"
        "  continuation stays with token.place\n"
        "- **[futuroptimist](https://github.com/futuroptimist/futuroptimist)** - hub\n"
    )

    stars = {"futuroptimist/token.place": 10, "futuroptimist/futuroptimist": 1}
    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "✅", stars=stars[repo]
        ),
    )
    from datetime import datetime

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        "Intro stays put.",
        "- ✅ ⭐ 10 **[token.place](https://token.place)** - external first "
        "([repo](https://github.com/futuroptimist/token.place))",
        "  continuation stays with token.place",
        "- ✅ ⭐ 1 **[futuroptimist](https://github.com/futuroptimist/futuroptimist)** - hub",
    ]


def test_update_readme_uses_repo_link_from_continuation_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- **[external](https://example.com)** - homepage first\n"
        "  ([repo](https://github.com/user/external/tree/main))\n"
        "- **[local](https://github.com/user/local)** - repo first\n"
    )
    calls: list[tuple[str, str | None]] = []

    def fake_status(repo: str, token=None, branch=None):
        calls.append((repo, branch))
        return repo_status.RepoStatus(
            "✅", stars={"user/external": 10, "user/local": 1}[repo]
        )

    monkeypatch.setattr(repo_status, "fetch_repo_status_details", fake_status)
    from datetime import datetime

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert calls == [("user/external", "main"), ("user/local", None)]
    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        "- ✅ ⭐ 10 **[external](https://example.com)** - homepage first",
        "  ([repo](https://github.com/user/external/tree/main))",
        "- ✅ ⭐ 1 **[local](https://github.com/user/local)** - repo first",
    ]


def test_update_readme_ignores_issue_action_and_note_links_before_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ([note](https://github.com/user/notes)) "
        "([issue](https://github.com/user/issue-tracker/issues/7)) "
        "([run](https://github.com/user/automation/actions/runs/99)) "
        "**[Site](https://example.com)** - external display "
        "([repo](https://github.com/user/site))\n"
    )
    calls: list[tuple[str, str | None]] = []

    def fake_status(repo: str, token=None, branch=None):
        calls.append((repo, branch))
        return repo_status.RepoStatus("✅", stars=9)

    monkeypatch.setattr(repo_status, "fetch_repo_status_details", fake_status)
    from datetime import datetime

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert calls == [("user/site", None)]
    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        "- ✅ ⭐ 9 ([note](https://github.com/user/notes)) "
        "([issue](https://github.com/user/issue-tracker/issues/7)) "
        "([run](https://github.com/user/automation/actions/runs/99)) "
        "**[Site](https://example.com)** - external display "
        "([repo](https://github.com/user/site))",
    ]


def test_update_readme_strips_arbitrary_label_legacy_failure_link_before_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ❌ ([Production](https://github.com/user/repo/actions/runs/0)) "
        "**[repo](https://github.com/user/repo)** - desc\n"
    )

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Production", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
            stars=4,
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
        "- ❌ ([Production](https://github.com/user/repo/actions/runs/1)) "
        "<!-- repo-status:failure-links --> ⭐ 4 "
        "**[repo](https://github.com/user/repo)** - desc",
    ]


def test_update_readme_strips_legacy_deploy_failure_link_before_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ❌ ([Deploy](https://github.com/user/repo/actions/runs/0)) "
        "**[repo](https://github.com/user/repo)** - desc\n"
    )

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Deploy", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        ),
    )
    from datetime import datetime

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))
    first = readme.read_text()
    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert readme.read_text() == first
    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        "- ❌ ([Deploy](https://github.com/user/repo/actions/runs/1)) "
        "<!-- repo-status:failure-links --> ⭐ ? "
        "**[repo](https://github.com/user/repo)** - desc",
    ]


def test_update_readme_branch_url_uses_branch_for_status_and_repo_for_stars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- **[DSPACE](https://democratized.space)** "
        "([repo](https://github.com/democratizedspace/dspace/tree/main))\n"
    )
    calls: list[tuple[str, str | None]] = []

    def fake_status(repo: str, token=None, branch=None):
        calls.append((repo, branch))
        return repo_status.RepoStatus("✅", stars=12)

    monkeypatch.setattr(repo_status, "fetch_repo_status_details", fake_status)
    from datetime import datetime

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert calls == [("democratizedspace/dspace", "main")]
    assert "- ✅ ⭐ 12 **[DSPACE](https://democratized.space)**" in readme.read_text()
