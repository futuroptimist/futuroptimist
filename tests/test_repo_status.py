from datetime import UTC, datetime
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
    assert status_to_emoji("neutral") == "✅"
    assert status_to_emoji("skipped") == "✅"


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


def test_status_to_emoji_unrecognized_status_is_unknown() -> None:
    assert status_to_emoji("queued") == "❓"
    assert status_to_emoji("mysterious") == "❓"


def test_workflow_identity_order_and_unknown_fallback() -> None:
    assert repo_status._workflow_identity(
        {
            "workflow_id": 7,
            "path": ".github/workflows/ci.yml",
            "workflow_name": "Deploy",
            "name": "CI",
            "display_title": "Fallback",
        }
    ) == ("workflow_id", "7")
    assert repo_status._workflow_identity(
        {
            "path": " .github/workflows/ci.yml ",
            "workflow_name": "Deploy",
            "name": "CI",
            "display_title": "Fallback",
        }
    ) == ("path", ".github/workflows/ci.yml")
    assert repo_status._workflow_identity(
        {"workflow_name": " Deploy  Checks ", "name": "CI"}
    ) == ("workflow_name", "deploy checks")
    assert repo_status._workflow_identity({"name": " CI  Checks "}) == (
        "name",
        "ci checks",
    )
    assert repo_status._workflow_identity({"display_title": " CI  Checks "}) == (
        "name",
        "ci checks",
    )
    assert repo_status._workflow_identity({"id": 123}) == ("run_id", "123")
    assert repo_status._workflow_identity({}) is None


def test_version_ref_detection_accepts_only_concrete_release_refs() -> None:
    release_refs = (
        "desktop-v0.1.0",
        "v0.1.0",
        "cli-v1.2.3",
        "refs/tags/desktop-v0.1.0",
    )
    for ref in release_refs:
        assert repo_status._is_version_ref(ref), ref

    ordinary_branches = (
        "feature/v1.2.3",
        "feature/desktop-v0.1.0",
        "dependabot/npm/foo-1.2.3",
        "codex/fix-v1.2.3-build",
    )
    for ref in ordinary_branches:
        assert not repo_status._is_version_ref(ref), ref


def test_release_like_workflow_ignores_title_only_build_text() -> None:
    assert (
        repo_status._is_release_like_workflow(
            {
                "name": "Quality",
                "path": ".github/workflows/quality.yml",
                "display_title": "fix build docs",
            }
        )
        is False
    )
    assert (
        repo_status._is_release_like_workflow(
            {"name": "Build", "path": ".github/workflows/build.yml"}
        )
        is True
    )


def test_run_dashboard_scope_requires_concrete_release_refs() -> None:
    for branch in (
        "desktop-v0.1.0",
        "v0.1.0",
        "cli-v1.2.3",
        "refs/tags/desktop-v0.1.0",
    ):
        run = _workflow_run(
            "success",
            name="Package CLI",
            path=".github/workflows/package.yml",
            branch=branch,
        )
        assert repo_status._run_dashboard_scope(run, "main") == "release-version"

    for branch in (
        "feature/v1.2.3",
        "feature/desktop-v0.1.0",
        "dependabot/npm/foo-1.2.3",
        "codex/fix-v1.2.3-build",
    ):
        run = _workflow_run(
            "success",
            name="Package CLI",
            path=".github/workflows/package.yml",
            branch=branch,
        )
        assert repo_status._run_dashboard_scope(run, "main") == "ignored"


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


def _human_commit(sha: str, message: str = "feat: update") -> dict:
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


def _workflow_run(
    conclusion: str,
    *,
    sha: str = "abc",
    name: str = "Test Suite",
    workflow_id: int | str | None = 123,
    path: str | None = ".github/workflows/tests.yml",
    workflow_name: str | None = None,
    display_title: str | None = None,
    event: str = "push",
    status: str = "completed",
    run_number: int = 1,
    run_attempt: int = 1,
    created_at: str = "2025-09-25T12:00:00Z",
    updated_at: str | None = None,
    run_id: int | None = None,
    branch: str = "main",
) -> dict:
    run: dict = {
        "conclusion": conclusion,
        "head_sha": sha,
        "head_branch": branch,
        "name": name,
        "event": event,
        "status": status,
        "run_number": run_number,
        "run_attempt": run_attempt,
        "created_at": created_at,
        "html_url": f"https://github.com/user/repo/actions/runs/{run_id or run_number}",
    }
    if workflow_id is not None:
        run["workflow_id"] = workflow_id
    if path is not None:
        run["path"] = path
    if workflow_name is not None:
        run["workflow_name"] = workflow_name
    if display_title is not None:
        run["display_title"] = display_title
    if updated_at is not None:
        run["updated_at"] = updated_at
    if run_id is not None:
        run["id"] = run_id
    return run


def _mock_repo_status_requests(
    monkeypatch: pytest.MonkeyPatch,
    runs: list[dict],
    *,
    all_runs: list[dict] | None = None,
    commits: list[dict] | None = None,
    branch: str = "main",
    stars: int | None = None,
    merged_prs: int | None = None,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            data: dict = {}
            if merged_prs is not None:
                data["total_count"] = merged_prs
            return DummyResp(data)
        if url == "https://api.github.com/repos/user/repo":
            data = {"default_branch": branch}
            if stars is not None:
                data["stargazers_count"] = stars
            return DummyResp(data)
        if url.startswith(
            f"https://api.github.com/repos/user/repo/commits?sha={branch}&per_page=20"
        ):
            return DummyResp(commits or [_human_commit("abc")])
        if (
            url
            == "https://api.github.com/repos/user/repo/actions/runs?per_page=100&status=completed"
        ):
            return DummyResp(
                {"workflow_runs": all_runs if all_runs is not None else runs}
            )
        assert url == (
            "https://api.github.com/repos/user/repo/actions/runs?"
            f"per_page=100&status=completed&branch={branch}"
        )
        return DummyResp({"workflow_runs": runs})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)


def test_fetch_repo_status_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append(url)
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1",
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1",
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1",
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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


def test_fetch_repo_status_newer_success_overrides_failed_workflow_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                workflow_id=7,
                run_number=10,
                created_at="2025-09-25T12:00:00Z",
                run_id=10,
            ),
            _workflow_run(
                "success",
                sha="new",
                workflow_id=7,
                run_number=11,
                created_at="2025-09-25T13:00:00Z",
                run_id=11,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_token_place_release_success_supersedes_stale_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failed = _workflow_run(
        "failure",
        sha="d99cb50d62672bff35d9642951679e90059ddadc",
        name="Build Desktop App",
        workflow_id=176183450,
        path=".github/workflows/desktop-build.yml",
        display_title="Merge pull request #1168 from futuroptimist/codex/add-visible-run_all…",
        run_number=625,
        created_at="2026-06-09T07:36:39Z",
        updated_at="2026-06-09T07:45:55Z",
        run_id=27191220631,
        branch="main",
    )
    fixed = _workflow_run(
        "success",
        sha="d99cb50d62672bff35d9642951679e90059ddadc",
        name="Build Desktop App",
        workflow_id=176183450,
        path=".github/workflows/desktop-build.yml",
        display_title="Merge pull request #1168 from futuroptimist/codex/add-visible-run_all…",
        run_number=626,
        created_at="2026-06-09T08:02:14Z",
        updated_at="2026-06-09T08:15:32Z",
        run_id=27192437756,
        branch="desktop-v0.1.0",
    )
    _mock_repo_status_requests(
        monkeypatch,
        [failed],
        all_runs=[failed, fixed],
        commits=[_human_commit("d99cb50d62672bff35d9642951679e90059ddadc")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_version_release_success_supersedes_selected_branch_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failed = _workflow_run(
        "failure",
        sha="abc",
        name="Package CLI",
        workflow_id=77,
        path=".github/workflows/package.yml",
        run_number=1,
        run_id=1,
    )
    fixed = _workflow_run(
        "success",
        sha="abc",
        name="Package CLI",
        workflow_id=77,
        path=".github/workflows/package.yml",
        display_title="Release cli-v1.2.3",
        run_number=2,
        created_at="2025-09-25T13:00:00Z",
        run_id=2,
        branch="cli-v1.2.3",
    )
    _mock_repo_status_requests(monkeypatch, [failed], all_runs=[failed, fixed])

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_generic_build_tag_success_supersedes_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failed = _workflow_run(
        "failure",
        sha="abc",
        name="Build",
        workflow_id=77,
        path=".github/workflows/build.yml",
        run_number=1,
        run_id=1,
    )
    fixed = _workflow_run(
        "success",
        sha="abc",
        name="Build",
        workflow_id=77,
        path=".github/workflows/build.yml",
        run_number=2,
        created_at="2025-09-25T13:00:00Z",
        run_id=2,
        branch="v1.2.3",
    )
    _mock_repo_status_requests(monkeypatch, [failed], all_runs=[failed, fixed])

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_preserves_release_workflows_with_test_workflows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tests_passed = _workflow_run(
        "success",
        sha="abc",
        name="Test Suite",
        workflow_id=100,
        path=".github/workflows/tests.yml",
        run_number=5,
        run_id=5,
    )
    package_failed = _workflow_run(
        "failure",
        sha="abc",
        name="Package CLI",
        workflow_id=77,
        path=".github/workflows/package.yml",
        run_number=1,
        run_id=1,
    )
    package_fixed = _workflow_run(
        "success",
        sha="abc",
        name="Package CLI",
        workflow_id=77,
        path=".github/workflows/package.yml",
        run_number=2,
        created_at="2025-09-25T13:00:00Z",
        run_id=2,
        branch="cli-v1.2.3",
    )
    _mock_repo_status_requests(
        monkeypatch,
        [tests_passed, package_failed],
        all_runs=[tests_passed, package_failed, package_fixed],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_release_success_missing_sha_does_not_hide_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failed = _workflow_run(
        "failure",
        sha="abc",
        name="Package Desktop",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=1,
        run_id=1,
    )
    release_without_sha = _workflow_run(
        "success",
        sha="abc",
        name="Package Desktop",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=2,
        created_at="2025-09-25T13:00:00Z",
        run_id=2,
        branch="desktop-v1.2.3",
    )
    release_without_sha.pop("head_sha")
    _mock_repo_status_requests(
        monkeypatch,
        [failed],
        all_runs=[failed, release_without_sha],
        commits=[_human_commit("abc")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Package Desktop", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        )
    )


def test_fetch_repo_status_keeps_non_keyword_failure_with_title_only_build_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    title_only_build_success = _workflow_run(
        "success",
        sha="abc",
        name="Quality",
        workflow_id=77,
        path=".github/workflows/quality.yml",
        display_title="fix build docs",
        run_id=1,
    )
    docs_failed = _workflow_run(
        "failure",
        sha="abc",
        name="Docs",
        workflow_id=88,
        path=".github/workflows/docs.yml",
        run_id=2,
    )
    _mock_repo_status_requests(
        monkeypatch,
        [title_only_build_success, docs_failed],
        all_runs=[title_only_build_success, docs_failed],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Docs", "https://github.com/user/repo/actions/runs/2"
                ),
            ),
        )
    )


def test_fetch_repo_status_feature_branch_success_does_not_supersede_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failed = _workflow_run(
        "failure",
        sha="abc",
        name="Build Desktop App",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=1,
        run_id=1,
    )
    feature = _workflow_run(
        "success",
        sha="abc",
        name="Build Desktop App",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=2,
        created_at="2025-09-25T13:00:00Z",
        run_id=2,
        branch="feature/build-fix",
    )
    _mock_repo_status_requests(monkeypatch, [failed], all_runs=[failed, feature])

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Build Desktop App", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        )
    )


def test_fetch_repo_status_release_success_different_sha_does_not_hide_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failed = _workflow_run(
        "failure",
        sha="abc",
        name="Package Desktop",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=1,
        run_id=1,
    )
    unrelated_release = _workflow_run(
        "success",
        sha="def",
        name="Package Desktop",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=2,
        created_at="2025-09-25T13:00:00Z",
        run_id=2,
        branch="desktop-v1.2.3",
    )
    _mock_repo_status_requests(
        monkeypatch,
        [failed],
        all_runs=[failed, unrelated_release],
        commits=[_human_commit("abc")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Package Desktop", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        )
    )


@pytest.mark.parametrize("branch", ["feature/v1.2.3", "feature/desktop-v0.1.0"])
def test_fetch_repo_status_feature_semver_branch_does_not_supersede_failure(
    monkeypatch: pytest.MonkeyPatch, branch: str
) -> None:
    failed = _workflow_run(
        "failure",
        sha="abc",
        name="Package Desktop",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=1,
        run_id=1,
    )
    feature = _workflow_run(
        "success",
        sha="abc",
        name="Package Desktop",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=2,
        created_at="2025-09-25T13:00:00Z",
        run_id=2,
        branch=branch,
    )
    _mock_repo_status_requests(monkeypatch, [failed], all_runs=[failed, feature])

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1).emoji == "❌"


def test_fetch_repo_status_paginates_release_runs_beyond_page_ten(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failed = _workflow_run(
        "failure",
        sha="abc",
        name="Package Desktop",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=1,
        run_id=1,
    )
    fixed = _workflow_run(
        "success",
        sha="abc",
        name="Package Desktop",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=2,
        created_at="2025-09-25T13:00:00Z",
        run_id=2,
        branch="desktop-v1.2.3",
    )
    filler_pages = [
        [
            _workflow_run(
                "success",
                sha=f"filler-{page}-{index}",
                name="Test Suite",
                workflow_id=100_000 + (page * 100) + index,
                run_id=100_000 + (page * 100) + index,
                branch="main",
            )
            for index in range(100)
        ]
        for page in range(1, 11)
    ]
    calls: list[str] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append(url)
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
        if url == "https://api.github.com/repos/user/repo":
            return DummyResp({"default_branch": "main"})
        if url.startswith(
            "https://api.github.com/repos/user/repo/commits?sha=main&per_page=20"
        ):
            return DummyResp([_human_commit("abc")])
        if url == (
            "https://api.github.com/repos/user/repo/actions/runs?"
            "per_page=100&status=completed&branch=main"
        ):
            return DummyResp({"workflow_runs": [failed]})
        base_url = (
            "https://api.github.com/repos/user/repo/actions/runs?"
            "per_page=100&status=completed"
        )
        if url == base_url:
            return DummyResp({"workflow_runs": filler_pages[0]})
        for page in range(2, 11):
            if url == f"{base_url}&page={page}":
                return DummyResp({"workflow_runs": filler_pages[page - 1]})
        assert url == f"{base_url}&page=11"
        return DummyResp({"workflow_runs": [fixed]})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1).emoji == "✅"
    assert calls[-1].endswith("&page=11")


def test_fetch_repo_status_run_number_outranks_updated_at_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    older_retried_failure = _workflow_run(
        "failure",
        sha="abc",
        workflow_id=77,
        run_number=1,
        run_id=1,
        created_at="2025-09-25T12:00:00Z",
        updated_at="2025-09-25T14:00:00Z",
    )
    newer_success = _workflow_run(
        "success",
        sha="abc",
        workflow_id=77,
        run_number=2,
        run_id=2,
        created_at="2025-09-25T13:00:00Z",
        updated_at="2025-09-25T13:05:00Z",
    )
    _mock_repo_status_requests(
        monkeypatch,
        [older_retried_failure, newer_success],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1).emoji == "✅"


def test_fetch_repo_status_release_success_different_workflow_does_not_hide_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failed = _workflow_run(
        "failure",
        sha="abc",
        name="Build Desktop App",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=1,
        run_id=1,
    )
    other = _workflow_run(
        "success",
        sha="abc",
        name="Build Desktop App",
        workflow_id=88,
        path=".github/workflows/desktop-build.yml",
        run_number=2,
        created_at="2025-09-25T13:00:00Z",
        run_id=2,
        branch="v1.2.3",
    )
    _mock_repo_status_requests(monkeypatch, [failed], all_runs=[failed, other])

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1).emoji == "❌"


def test_fetch_repo_status_release_success_does_not_hide_test_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    build_failed = _workflow_run(
        "failure",
        sha="abc",
        name="Build Desktop App",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=1,
        run_id=1,
    )
    tests_failed = _workflow_run(
        "failure",
        sha="abc",
        name="Test Suite",
        workflow_id=99,
        path=".github/workflows/tests.yml",
        run_number=1,
        run_id=3,
    )
    build_fixed = _workflow_run(
        "success",
        sha="abc",
        name="Build Desktop App",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=2,
        created_at="2025-09-25T13:00:00Z",
        run_id=2,
        branch="v1.2.3",
    )
    _mock_repo_status_requests(
        monkeypatch,
        [build_failed, tests_failed],
        all_runs=[build_failed, tests_failed, build_fixed],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Test Suite", "https://github.com/user/repo/actions/runs/3"
                ),
            ),
        )
    )


def test_fetch_repo_status_latest_release_failure_links_latest_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_success = _workflow_run(
        "success",
        sha="abc",
        name="Package Desktop",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=1,
        run_id=1,
    )
    release_failure = _workflow_run(
        "failure",
        sha="abc",
        name="Package Desktop",
        workflow_id=77,
        path=".github/workflows/desktop-build.yml",
        run_number=2,
        created_at="2025-09-25T13:00:00Z",
        run_id=2,
        branch="desktop-v1.2.3",
    )
    _mock_repo_status_requests(
        monkeypatch,
        [branch_success],
        all_runs=[branch_success, release_failure],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Package Desktop", "https://github.com/user/repo/actions/runs/2"
                ),
            ),
        )
    )


def test_fetch_repo_status_preserves_id_only_failed_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            {
                "conclusion": "failure",
                "head_sha": "abc",
                "head_branch": "main",
                "id": 99,
                "html_url": "https://github.com/user/repo/actions/runs/99",
            }
        ],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "workflow run", "https://github.com/user/repo/actions/runs/99"
                ),
            ),
        )
    )


def test_fetch_repo_status_mixed_workflow_id_types_share_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                workflow_id=7,
                run_number=10,
                created_at="2025-09-25T12:00:00Z",
                run_id=10,
            ),
            _workflow_run(
                "success",
                sha="new",
                workflow_id="7",
                run_number=11,
                created_at="2025-09-25T13:00:00Z",
                run_id=11,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_later_run_number_beats_updated_at(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                workflow_id=7,
                run_number=10,
                created_at="2025-09-25T12:00:00Z",
                updated_at="2025-09-25T14:00:00Z",
                run_id=10,
            ),
            _workflow_run(
                "success",
                sha="new",
                workflow_id=7,
                run_number=11,
                created_at="2025-09-25T13:00:00Z",
                updated_at="2025-09-25T13:05:00Z",
                run_id=11,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_parse_github_timestamp_treats_naive_iso_as_utc() -> None:
    assert repo_status._parse_github_timestamp("2025-09-25T12:00:00") == (
        1,
        "2025-09-25T12:00:00+00:00",
    )


def test_fetch_repo_status_newer_success_overrides_failed_workflow_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                workflow_id=None,
                path=".github/workflows/ci.yml",
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
            ),
            _workflow_run(
                "success",
                sha="new",
                workflow_id=None,
                path=".github/workflows/ci.yml",
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_newer_success_overrides_failed_normalized_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                name=" Test   Suite ",
                workflow_id=None,
                path=None,
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
            ),
            _workflow_run(
                "success",
                sha="new",
                name="test suite",
                workflow_id=None,
                path=None,
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_newer_success_overrides_failed_workflow_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                name="run title changed",
                workflow_id=None,
                path=None,
                workflow_name=" CI   Checks ",
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
            ),
            _workflow_run(
                "success",
                sha="new",
                name="different run title",
                workflow_id=None,
                path=None,
                workflow_name="ci checks",
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_mixed_workflow_name_and_name_share_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                name="CI",
                workflow_id=None,
                path=None,
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
            ),
            _workflow_run(
                "success",
                sha="new",
                name="CI",
                workflow_id=None,
                path=None,
                workflow_name="CI",
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_workflow_name_does_not_merge_unrelated_run_title(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                name="Test Suite",
                workflow_id=None,
                path=None,
                workflow_name="Deploy",
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
            ),
            _workflow_run(
                "success",
                sha="new",
                name="Deploy",
                workflow_id=None,
                path=None,
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Test Suite", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        )
    )


def test_fetch_repo_status_workflow_name_and_name_do_not_weak_merge_newer_title_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                name="CI",
                workflow_id=None,
                path=None,
                workflow_name="CI",
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
            ),
            _workflow_run(
                "success",
                sha="new",
                name="CI",
                workflow_id=None,
                path=None,
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "CI", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        )
    )


def test_fetch_repo_status_workflow_id_does_not_bridge_to_weak_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                name="CI",
                workflow_id=None,
                path=None,
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
            ),
            _workflow_run(
                "success",
                sha="new",
                name="CI",
                workflow_id=7,
                path=None,
                workflow_name="CI",
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "CI", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        )
    )


def test_fetch_repo_status_workflow_name_precedes_run_name_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                name="Test Suite",
                workflow_id=None,
                path=None,
                workflow_name="CI",
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
            ),
            _workflow_run(
                "success",
                sha="new",
                name="Test Suite",
                workflow_id=None,
                path=None,
                workflow_name="Deploy",
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Test Suite", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        )
    )


def test_fetch_repo_status_bot_success_overrides_older_same_workflow_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                workflow_id=7,
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
            ),
            _workflow_run(
                "success",
                sha="bot",
                workflow_id=7,
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
            ),
        ],
        commits=[
            {
                "sha": "bot",
                "commit": {
                    "message": "chore: automated update",
                    "author": {"name": "github-actions[bot]"},
                    "committer": {"name": "github-actions[bot]"},
                },
                "author": {"login": "github-actions[bot]"},
                "committer": {"login": "github-actions[bot]"},
            },
            _human_commit("old"),
        ],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_neutral_and_skipped_are_passing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "neutral",
                sha="abc",
                workflow_id=7,
                run_number=1,
                run_id=1,
            ),
            _workflow_run(
                "skipped",
                sha="abc",
                name="Lint Suite",
                workflow_id=8,
                path=".github/workflows/lint.yml",
                run_number=1,
                run_id=2,
            ),
        ],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus("✅")
    )


def test_fetch_repo_status_unrelated_names_do_not_override_each_other(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                name="Test Suite",
                workflow_id=None,
                path=None,
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
            ),
            _workflow_run(
                "success",
                sha="new",
                name="Lint Suite",
                workflow_id=None,
                path=None,
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Test Suite", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        )
    )


def test_fetch_repo_status_newer_different_workflow_success_keeps_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                name="Test Suite",
                workflow_id=1,
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
            ),
            _workflow_run(
                "success",
                sha="new",
                name="Lint Suite",
                workflow_id=2,
                path=".github/workflows/lint.yml",
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Test Suite", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        )
    )


def test_fetch_repo_status_different_branch_success_does_not_override_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="main-sha",
                workflow_id=7,
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
                branch="main",
            ),
            _workflow_run(
                "success",
                sha="dev-sha",
                workflow_id=7,
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
                branch="dev",
            ),
        ],
        commits=[_human_commit("main-sha"), _human_commit("dev-sha")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Test Suite", "https://github.com/user/repo/actions/runs/1"
                ),
            ),
        )
    )


def test_fetch_repo_status_latest_failed_run_links_latest_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "success",
                sha="old",
                workflow_id=7,
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
            ),
            _workflow_run(
                "failure",
                sha="new",
                workflow_id=7,
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Test Suite", "https://github.com/user/repo/actions/runs/2"
                ),
            ),
        )
    )


def test_fetch_repo_status_multiple_workflows_link_only_latest_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_repo_status_requests(
        monkeypatch,
        [
            _workflow_run(
                "failure",
                sha="old",
                name="Test Suite",
                workflow_id=1,
                run_number=1,
                created_at="2025-09-25T12:00:00Z",
                run_id=1,
            ),
            _workflow_run(
                "success",
                sha="new",
                name="Test Suite",
                workflow_id=1,
                run_number=2,
                created_at="2025-09-25T13:00:00Z",
                run_id=2,
            ),
            _workflow_run(
                "failure",
                sha="new",
                name="Lint Suite",
                workflow_id=2,
                path=".github/workflows/lint.yml",
                run_number=3,
                created_at="2025-09-25T13:05:00Z",
                run_id=3,
            ),
        ],
        commits=[_human_commit("new"), _human_commit("old")],
    )

    assert repo_status.fetch_repo_status_details("user/repo", attempts=1) == (
        repo_status.RepoStatus(
            "❌",
            (
                repo_status.StatusLink(
                    "Lint Suite", "https://github.com/user/repo/actions/runs/3"
                ),
            ),
        )
    )


def test_fetch_repo_status_skips_bot_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append(url)
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
            fake_status(repo, token, branch),
            stars={"user/repo": 2, "other/repo": 1}.get(repo),
        ),
    )
    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)

    lines = readme.read_text().splitlines()
    assert lines[3] == "_Last updated: 2020-01-02 03:04 UTC; checks hourly_"
    assert lines[4] == "- ✅ ⭐ 2 🔀 ? https://github.com/user/repo"


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
    assert lines[2] == "- ✅ ⭐ ? 🔀 ? https://github.com/user/repo"


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
    assert lines[4] == "- ✅ ⭐ ? 🔀 ? https://github.com/user/repo"


def test_fetch_repo_status_details_includes_failed_run_link(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        "- ✅ ⭐ ? 🔀 ? https://github.com/user/repo (failing runs: https://old.example/run)\n"
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
            "<!-- repo-status:failure-links --> ⭐ ? 🔀 ? https://github.com/user/repo"
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
            "⭐ ? 🔀 ? **[repo](https://github.com/user/repo)** - description"
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
        "<!-- repo-status:failure-links --> ⭐ ? 🔀 ? https://github.com/user/repo"
    ) in readme.read_text().splitlines()


def test_fetch_repo_status_report_returns_url_strings_for_compatibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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
        "<!-- repo-status:failure-links --> ⭐ ? 🔀 ? https://github.com/user/repo\n"
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
        "<!-- repo-status:failure-links --> ⭐ ? 🔀 ? https://github.com/user/repo",
    ]


def test_update_readme_strips_bracketed_failure_label_idempotently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ❌ ([CI [lint\\]](https://github.com/user/repo/actions/runs/0)) "
        "<!-- repo-status:failure-links --> ⭐ ? 🔀 ? https://github.com/user/repo\n"
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
        "<!-- repo-status:failure-links --> ⭐ ? 🔀 ? https://github.com/user/repo",
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
        "<!-- repo-status:failure-links --> ⭐ ? 🔀 ? https://github.com/user/repo",
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
        "- ✅ ⭐ 3 🔀 ? (archived) **[repo](https://github.com/user/repo)** - desc",
        "- ✅ ⭐ 2 🔀 ? ([docs](https://example.com)) "
        "**[docs-repo](https://github.com/user/docs-repo)** - desc",
        "- ✅ ⭐ 1 🔀 ? ([debug run](https://github.com/user/debug-repo/actions/runs/123)) "
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
        "- ✅ ⭐ ? 🔀 ? ([debug run](https://github.com/user/repo/actions/runs/123)) "
        "https://github.com/user/repo - desc",
    ]


def test_update_readme_flywheel_regression_suppresses_stale_failure_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datetime import datetime

    readme = tmp_path / "README.md"
    readme.write_text(
        "# Futuroptimist\n\n"
        "## Related Projects\n"
        "- ❌ [Update Repo Statuses](https://github.com/futuroptimist/flywheel/actions/"
        "runs/27123196602) "
        "<!-- repo-status:failure-links --> ⭐ ? "
        "**[flywheel](https://github.com/futuroptimist/flywheel)** - automate the loop\n",
        encoding="utf-8",
    )

    def fake_get(url: str, headers: dict, timeout: int):
        if url == (
            "https://api.github.com/search/issues?"
            "q=repo:futuroptimist/flywheel+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
        if url == "https://api.github.com/repos/futuroptimist/flywheel":
            return DummyResp({"default_branch": "main", "stargazers_count": 9})
        if url.startswith(
            "https://api.github.com/repos/futuroptimist/flywheel/commits?sha=main&per_page=20"
        ):
            return DummyResp([_human_commit("new"), _human_commit("old")])
        assert url == (
            "https://api.github.com/repos/futuroptimist/flywheel/actions/runs?"
            "per_page=100&status=completed&branch=main"
        )
        return DummyResp(
            {
                "workflow_runs": [
                    {
                        "conclusion": "failure",
                        "head_sha": "old",
                        "head_branch": "main",
                        "name": "Update Repo Statuses",
                        "workflow_id": 99,
                        "run_number": 20,
                        "run_attempt": 1,
                        "created_at": "2025-09-25T12:00:00Z",
                        "html_url": "https://github.com/futuroptimist/flywheel/actions/runs/27123196602",
                    },
                    {
                        "conclusion": "success",
                        "head_sha": "new",
                        "head_branch": "main",
                        "name": "Update Repo Statuses",
                        "workflow_id": 99,
                        "run_number": 21,
                        "run_attempt": 1,
                        "created_at": "2025-09-25T13:00:00Z",
                        "html_url": "https://github.com/futuroptimist/flywheel/actions/runs/27199999999",
                    },
                ]
            }
        )

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    repo_status.update_readme(readme, now=datetime(2025, 9, 25, 14, 0, tzinfo=UTC))

    rendered = readme.read_text(encoding="utf-8")
    assert (
        "- ✅ ⭐ 9 🔀 ? **[flywheel](https://github.com/futuroptimist/flywheel)**"
        in rendered
    )
    assert "automate the loop" in rendered
    assert "27123196602" not in rendered
    assert "repo-status:failure-links" not in rendered


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
    assert "🔀 shows total merged pull requests" in section
    assert "Projects sort by stars descending" in section
    assert readme.count("docs/repository-guide.md") == 1

    project_lines = [line for line in section.splitlines() if line.startswith("- ")]
    assert project_lines
    assert all(repo_status.GITHUB_RE.search(line) for line in project_lines)
    assert all("⭐" in line for line in project_lines)
    assert all("🔀" in line for line in project_lines)


def test_fetch_repo_status_details_includes_star_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({})
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


def test_fetch_merged_pr_count_success_uses_search_endpoint_and_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict, int]] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append((url, headers, timeout))
        return DummyResp({"total_count": 12, "incomplete_results": False})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    assert repo_status.fetch_merged_pr_count("user/repo", token="secret") == 12
    assert calls == [
        (
            "https://api.github.com/search/issues?"
            "q=repo:user/repo+is:pr+is:merged&per_page=1",
            {"Accept": "application/vnd.github+json", "Authorization": "Bearer secret"},
            10,
        )
    ]


def test_fetch_repo_metadata_includes_merged_pr_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict]] = []

    def fake_get(url: str, headers: dict, timeout: int):
        calls.append((url, headers))
        if (
            url
            == "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1"
        ):
            return DummyResp({"total_count": 42})
        assert url == "https://api.github.com/repos/user/repo"
        return DummyResp({"default_branch": "main", "stargazers_count": 6})

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    assert repo_status.fetch_repo_metadata(
        "user/repo", token="secret"
    ) == repo_status.RepoMetadata(default_branch="main", stars=6, merged_prs=42)
    assert calls == [
        (
            "https://api.github.com/search/issues?q=repo:user/repo+is:pr+is:merged&per_page=1",
            {"Accept": "application/vnd.github+json", "Authorization": "Bearer secret"},
        ),
        (
            "https://api.github.com/repos/user/repo",
            {"Accept": "application/vnd.github+json", "Authorization": "Bearer secret"},
        ),
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"total_count": "42"},
        {"total_count": True},
        {"total_count": 42, "incomplete_results": True},
        [],
    ],
)
def test_fetch_merged_pr_count_invalid_payload_is_unknown(
    monkeypatch: pytest.MonkeyPatch, payload: object
) -> None:
    monkeypatch.setattr(
        repo_status.requests, "get", lambda url, headers, timeout: DummyResp(payload)
    )

    assert repo_status.fetch_merged_pr_count("user/repo") is None


def test_fetch_merged_pr_count_request_error_is_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(url: str, headers: dict, timeout: int):
        raise repo_status.requests.exceptions.RequestException("rate limited")

    monkeypatch.setattr(repo_status.requests, "get", fake_get)

    assert repo_status.fetch_merged_pr_count("user/repo") is None


def test_format_merged_pr_count_handles_unknowns() -> None:
    assert repo_status.format_merged_pr_count(42) == "🔀 42"
    assert repo_status.format_merged_pr_count(None) == "🔀 ?"


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


def test_update_readme_preserves_existing_merged_pr_count_when_fetch_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ✅ ⭐ 8 🔀 123 **[repo](https://github.com/user/repo)** - existing count\n"
    )

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "✅", stars=9, merged_prs=None
        ),
    )

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert (
        "- ✅ ⭐ 9 🔀 123 **[repo](https://github.com/user/repo)** - existing count"
        in readme.read_text()
    )


def test_update_readme_replaces_existing_merged_pr_count_when_fetch_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ✅ ⭐ 8 🔀 123 **[repo](https://github.com/user/repo)** - stale count\n"
    )

    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "✅", stars=9, merged_prs=456
        ),
    )

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert (
        "- ✅ ⭐ 9 🔀 456 **[repo](https://github.com/user/repo)** - stale count"
        in readme.read_text()
    )


def test_update_readme_upgrades_and_replaces_merged_pr_prefixes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ✅ ⭐ 1 **[old-star](https://github.com/user/old-star)** - needs PR marker\n"
        "- ✅ ⭐ ? **[old-q](https://github.com/user/old-q)** - needs PR marker\n"
        "- ✅ ⭐ 2 🔀 999 **[stale](https://github.com/user/stale)** - stale count\n"
        "- ✅ ⭐ ? 🔀 888 **[stale-q](https://github.com/user/stale-q)** - stale count\n"
        "- ✅ ⭐ 4 🔀 ? **[unknown-prs](https://github.com/user/unknown-prs)** - known stars\n"
        "- **[unknown-stars](https://github.com/user/unknown-stars)** - known PRs\n"
    )

    details = {
        "user/old-star": repo_status.RepoStatus("✅", stars=1, merged_prs=11),
        "user/old-q": repo_status.RepoStatus("✅", stars=None, merged_prs=12),
        "user/stale": repo_status.RepoStatus("✅", stars=2, merged_prs=22),
        "user/stale-q": repo_status.RepoStatus("✅", stars=None, merged_prs=33),
        "user/unknown-stars": repo_status.RepoStatus("❓", stars=None, merged_prs=44),
        "user/unknown-prs": repo_status.RepoStatus("✅", stars=4, merged_prs=None),
    }
    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: details[repo],
    )
    from datetime import datetime

    now = datetime(2020, 1, 2, 3, 4, tzinfo=UTC)
    repo_status.update_readme(readme, now=now)
    first = readme.read_text()
    repo_status.update_readme(readme, now=now)

    assert readme.read_text() == first
    rendered_lines = readme.read_text().splitlines()[2:]
    assert rendered_lines == [
        "- ✅ ⭐ 4 🔀 ? **[unknown-prs](https://github.com/user/unknown-prs)** - known stars",
        "- ✅ ⭐ 2 🔀 22 **[stale](https://github.com/user/stale)** - stale count",
        "- ✅ ⭐ 1 🔀 11 **[old-star](https://github.com/user/old-star)** - needs PR marker",
        "- ✅ ⭐ ? 🔀 12 **[old-q](https://github.com/user/old-q)** - needs PR marker",
        "- ✅ ⭐ ? 🔀 33 **[stale-q](https://github.com/user/stale-q)** - stale count",
        "- ❓ ⭐ ? 🔀 44 **[unknown-stars](https://github.com/user/unknown-stars)** - known PRs",
    ]
    assert all(
        line.count("⭐") == 1 and line.count("🔀") == 1 for line in rendered_lines
    )
    assert "🔀 888" not in readme.read_text()
    assert "🔀 999" not in readme.read_text()


def test_update_readme_replaces_stale_pr_prefix_after_failure_links_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "## Related Projects\n"
        "- ❌ ([old tests](https://github.com/user/repo/actions/runs/0)) "
        "<!-- repo-status:failure-links --> ⭐ 8 🔀 1 "
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
            stars=9,
            merged_prs=2,
        ),
    )

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))
    rendered = readme.read_text()

    assert rendered.splitlines()[2] == (
        "- ❌ ([tests](https://github.com/user/repo/actions/runs/1)) "
        "<!-- repo-status:failure-links --> ⭐ 9 🔀 2 "
        "**[repo](https://github.com/user/repo)** - desc"
    )
    assert rendered.count("<!-- repo-status:failure-links -->") == 1
    assert "🔀 1" not in rendered


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
        "- ✅ ⭐ 5 🔀 ? **[alpha](https://github.com/user/alpha)** - same stars",
        "- ✅ ⭐ 5 🔀 ? **[Beta](https://github.com/user/beta)** - same stars",
        "- ✅ ⭐ 0 🔀 ? **[Zero](https://github.com/user/zero)** - zero stars",
        "- ✅ ⭐ ? 🔀 ? **[Unknown](https://github.com/user/unknown)** - unknown stars",
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
        "<!-- repo-status:failure-links --> ⭐ 7 🔀 ? "
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

    metadata = {
        "futuroptimist/token.place": (10, 1),
        "futuroptimist/futuroptimist": (1, 99),
    }
    monkeypatch.setattr(
        repo_status,
        "fetch_repo_status_details",
        lambda repo, token=None, branch=None: repo_status.RepoStatus(
            "✅", stars=metadata[repo][0], merged_prs=metadata[repo][1]
        ),
    )
    from datetime import datetime

    repo_status.update_readme(readme, now=datetime(2020, 1, 2, 3, 4, tzinfo=UTC))

    assert readme.read_text().splitlines() == [
        "## Related Projects",
        "_Last updated: 2020-01-02 03:04 UTC; checks hourly_",
        "Intro stays put.",
        "- ✅ ⭐ 10 🔀 1 **[token.place](https://token.place)** - external first "
        "([repo](https://github.com/futuroptimist/token.place))",
        "  continuation stays with token.place",
        "- ✅ ⭐ 1 🔀 99 **[futuroptimist](https://github.com/futuroptimist/futuroptimist)** - hub",
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
        "- ✅ ⭐ 10 🔀 ? **[external](https://example.com)** - homepage first",
        "  ([repo](https://github.com/user/external/tree/main))",
        "- ✅ ⭐ 1 🔀 ? **[local](https://github.com/user/local)** - repo first",
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
        "- ✅ ⭐ 9 🔀 ? ([note](https://github.com/user/notes)) "
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
        "<!-- repo-status:failure-links --> ⭐ 4 🔀 ? "
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
        "<!-- repo-status:failure-links --> ⭐ ? 🔀 ? "
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
    assert (
        "- ✅ ⭐ 12 🔀 ? **[DSPACE](https://democratized.space)**" in readme.read_text()
    )
