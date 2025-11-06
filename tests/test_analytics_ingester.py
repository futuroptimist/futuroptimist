from __future__ import annotations

import io
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import src.analytics_ingester as ai


class DummyResponse(io.BytesIO):
    def __init__(self, payload: dict[str, Any]):
        data = json.dumps(payload).encode("utf-8")
        super().__init__(data)

    def __enter__(self) -> DummyResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return False


def _write_metadata(base: Path, slug: str, youtube_id: str) -> Path:
    video_dir = base / "video_scripts" / slug
    video_dir.mkdir(parents=True)
    metadata = {
        "youtube_id": youtube_id,
        "title": slug.replace("_", " ").title(),
        "status": "live",
    }
    path = video_dir / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2))
    return path


def _sample_payload() -> dict[str, Any]:
    return {
        "kind": "youtubeAnalytics#resultTable",
        "columnHeaders": [
            {"name": "views", "columnType": "METRIC", "dataType": "INTEGER"},
            {
                "name": "estimatedMinutesWatched",
                "columnType": "METRIC",
                "dataType": "FLOAT",
            },
            {
                "name": "averageViewDuration",
                "columnType": "METRIC",
                "dataType": "FLOAT",
            },
            {"name": "impressions", "columnType": "METRIC", "dataType": "INTEGER"},
            {
                "name": "impressionsClickThroughRate",
                "columnType": "METRIC",
                "dataType": "FLOAT",
            },
        ],
        "rows": [[1234, 456.0, 210.5, 9876, 0.083]],
    }


def test_fetch_video_metrics_maps_known_columns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = "dummy"
    video_id = "abc123"
    payload = _sample_payload()

    def fake_urlopen(request: Any) -> DummyResponse:
        assert video_id in request.full_url
        assert request.headers["Authorization"] == f"Bearer {token}"
        return DummyResponse(payload)

    monkeypatch.setattr(ai.urllib.request, "urlopen", fake_urlopen)

    metrics = ai.fetch_video_metrics(
        video_id=video_id,
        token=token,
        start_date="2025-01-01",
        end_date="2025-12-31",
    )

    assert metrics == {
        "views": 1234,
        "watch_time_minutes": pytest.approx(456.0),
        "average_view_duration_seconds": pytest.approx(210.5),
        "impressions": 9876,
        "impressions_click_through_rate": pytest.approx(0.083),
    }


def test_ingest_updates_metadata_and_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path
    metadata_path = _write_metadata(repo, "20250101_demo", "abc123")
    payload = _sample_payload()

    calls: list[str] = []

    def fake_urlopen(request: Any) -> DummyResponse:
        calls.append(request.full_url)
        return DummyResponse(payload)

    monkeypatch.setattr(ai.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("YOUTUBE_ANALYTICS_TOKEN", "secret-token")
    summary = ai.ingest(
        video_root=repo / "video_scripts",
        start_date="2025-01-01",
        end_date="2025-12-31",
    )

    assert calls, "Expected the analytics API to be queried"
    data = json.loads(metadata_path.read_text())
    analytics = data.get("analytics")
    assert analytics
    assert analytics["views"] == 1234
    assert analytics["impressions"] == 9876
    assert analytics["watch_time_minutes"] == pytest.approx(456.0)
    assert analytics["impressions_click_through_rate"] == pytest.approx(0.083)
    # updated_at should be an ISO timestamp without microseconds
    updated_at = datetime.fromisoformat(analytics["updated_at"].replace("Z", "+00:00"))
    assert updated_at.tzinfo == UTC
    assert updated_at.microsecond == 0

    assert summary == [
        {
            "slug": "20250101_demo",
            "youtube_id": "abc123",
            "views": 1234,
            "watch_time_minutes": pytest.approx(456.0),
            "average_view_duration_seconds": pytest.approx(210.5),
            "impressions": 9876,
            "impressions_click_through_rate": pytest.approx(0.083),
        }
    ]


def test_main_writes_summary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path
    _write_metadata(repo, "20250101_demo", "abc123")
    payload = _sample_payload()

    def fake_urlopen(request: Any) -> DummyResponse:
        return DummyResponse(payload)

    monkeypatch.setattr(ai.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("YOUTUBE_ANALYTICS_TOKEN", "tkn")

    out = repo / "analytics" / "report.json"
    ai.main(
        [
            "--start-date",
            "2025-01-01",
            "--end-date",
            "2025-12-31",
            "--output",
            str(out),
        ]
    )

    assert out.exists()
    content = json.loads(out.read_text())
    assert content[0]["slug"] == "20250101_demo"
