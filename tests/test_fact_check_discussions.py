"""Tests for the GitHub Discussions fact-check indexer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import requests


class DummyResponse:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> Any:  # pragma: no cover - exercised in tests
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:  # pragma: no branch - deterministic
            raise requests.HTTPError(f"status {self.status_code}")


def _make_discussion(
    *,
    number: int,
    title: str,
    category: str,
    state: str = "open",
    updated_at: str = "2025-01-02T03:04:05Z",
    created_at: str | None = None,
    author: str = "author",
    comments: int = 0,
    url: str | None = None,
    reactions: dict[str, int] | None = None,
) -> dict[str, Any]:
    return {
        "number": number,
        "title": title,
        "category": {"name": category},
        "state": state,
        "updated_at": updated_at,
        "created_at": created_at or "2025-01-01T00:00:00Z",
        "user": {"login": author},
        "comments": comments,
        "html_url": url or f"https://github.com/example/discussions/{number}",
        "reactions": reactions
        or {
            "+1": 0,
            "-1": 0,
            "laugh": 0,
            "confused": 0,
            "heart": 0,
            "hooray": 0,
            "eyes": 0,
            "rocket": 0,
            "total_count": 0,
        },
    }


def test_build_fact_check_index_filters_and_serialises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src import (
        fact_check_discussions,
    )  # imported lazily so module exists when implemented

    payloads = [
        [
            _make_discussion(number=1, title="Not fact-check", category="Ideas"),
            _make_discussion(
                number=2,
                title="Verifier",
                category="Fact Check",
                updated_at="2025-02-01T12:00:00Z",
                comments=3,
                reactions={
                    "+1": 2,
                    "-1": 0,
                    "laugh": 0,
                    "confused": 1,
                    "heart": 0,
                    "hooray": 0,
                    "eyes": 0,
                    "rocket": 0,
                    "total_count": 3,
                },
            ),
        ],
        [
            _make_discussion(
                number=3,
                title="Second wave",
                category="Fact Check",
                updated_at="2025-02-02T00:00:00Z",
                comments=1,
            )
        ],
        [],
    ]
    calls: list[dict[str, Any]] = []

    def fake_get(
        url: str, *, headers: dict[str, str], params: dict[str, Any], timeout: int
    ) -> DummyResponse:
        calls.append(
            {"url": url, "headers": headers, "params": params, "timeout": timeout}
        )
        assert (
            url
            == "https://api.github.com/repos/futuroptimist/futuroptimist/discussions"
        )
        assert headers["Accept"] == "application/vnd.github+json"
        assert headers["Authorization"] == "Bearer TOKEN"
        page = params["page"] - 1
        return DummyResponse(payloads[page])

    monkeypatch.setattr("requests.get", fake_get)

    output_path = tmp_path / "fact-checks.json"
    records = fact_check_discussions.build_fact_check_index(
        repo="futuroptimist/futuroptimist",
        token="TOKEN",
        per_page=2,
        max_pages=3,
        output_path=output_path,
    )

    assert [call["params"]["page"] for call in calls] == [1, 2]
    assert len(records) == 2
    assert [r["number"] for r in records] == [3, 2]

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved == records
    for entry in saved:
        assert entry["category"] == "Fact Check"
        assert entry["state"] == "open"
        assert "updated_at" in entry


def test_build_fact_check_index_includes_closed_when_requested(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src import fact_check_discussions

    payloads = [
        [
            _make_discussion(
                number=10, title="Closed", category="Fact Check", state="closed"
            ),
            _make_discussion(number=11, title="Open", category="Fact Check"),
        ],
        [],
    ]

    def fake_get(
        url: str, *, headers: dict[str, str], params: dict[str, Any], timeout: int
    ) -> DummyResponse:
        return DummyResponse(payloads[params["page"] - 1])

    monkeypatch.setattr("requests.get", fake_get)

    records = fact_check_discussions.build_fact_check_index(
        repo="futuroptimist/futuroptimist",
        token=None,
        per_page=2,
        max_pages=2,
        include_closed=True,
        output_path=tmp_path / "out.json",
    )

    numbers = {r["number"] for r in records}
    assert numbers == {10, 11}


def test_fetch_discussions_raises_for_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src import fact_check_discussions

    def fake_get(*args: Any, **kwargs: Any) -> DummyResponse:
        return DummyResponse({}, status_code=500)

    monkeypatch.setattr("requests.get", fake_get)

    with pytest.raises(requests.HTTPError):
        list(
            fact_check_discussions.fetch_discussions(
                repo="futuroptimist/futuroptimist",
                token=None,
                per_page=1,
                max_pages=1,
            )
        )
