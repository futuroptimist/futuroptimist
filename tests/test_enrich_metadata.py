"""Regression tests for :mod:`src.enrich_metadata`."""

from __future__ import annotations

import io
import json
from collections.abc import Iterator
from pathlib import Path

import pytest

import src.enrich_metadata as em


class DummyResponse(io.BytesIO):
    """Simple context manager wrapper for urlopen stubs."""

    def __enter__(self) -> DummyResponse:
        return self

    def __exit__(self, *exc_info) -> bool:
        return False


def _build_api_payload(video_ids: Iterator[str]) -> bytes:
    items = []
    for idx, video_id in enumerate(video_ids, start=1):
        items.append(
            {
                "id": video_id,
                "snippet": {
                    "title": f"Title {idx}",
                    "publishedAt": "2025-02-03T04:05:06Z",
                    "thumbnails": {
                        "maxres": {
                            "url": f"https://img.youtube.com/{video_id}/maxres.jpg"
                        },
                        "high": {"url": f"https://img.youtube.com/{video_id}/high.jpg"},
                    },
                },
                "contentDetails": {"duration": "PT1H2M3S"},
                "statistics": {"viewCount": str(idx * 1000)},
            }
        )
    return json.dumps({"items": items}).encode()


def test_parse_duration_handles_mixed_components() -> None:
    assert em.parse_duration("P1DT2H3M4S") == 86400 + 7200 + 180 + 4
    assert em.parse_duration("PT15M") == 900
    assert em.parse_duration("") == 0


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("PT5M33S", 5 * 60 + 33),
        ("PT1H2M3S", 3723),
        ("PT0S", 0),
        ("P1DT1H", 24 * 3600 + 3600),
        ("P1W", 7 * 24 * 3600),
    ],
)
def test_parse_duration_various_cases(value: str, expected: int) -> None:
    assert em.parse_duration(value) == expected


def test_fetch_video_metadata_batches_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_urlopen(url: str):
        calls.append(url)
        query = dict(part.split("=", 1) for part in url.split("?")[1].split("&"))
        assert query["part"] == ",".join(em.API_PARTS)
        ids = query["id"].split(",")
        return DummyResponse(_build_api_payload(ids))

    monkeypatch.setattr(em.urllib.request, "urlopen", fake_urlopen)
    ids = [f"vid{i}" for i in range(55)]  # force two batches (50 + 5)
    info_map = em.fetch_video_metadata(ids, "token")

    assert len(calls) == 2
    assert set(info_map.keys()) == set(ids)
    sample = info_map["vid0"]
    assert sample.title == "Title 1"
    assert sample.publish_date == "2025-02-03"
    assert sample.duration_seconds == 3723
    assert sample.thumbnail == "https://img.youtube.com/vid0/maxres.jpg"
    assert sample.view_count == 1000


def test_apply_updates_respects_dry_run(tmp_path: Path) -> None:
    meta = tmp_path / "metadata.json"
    meta.write_text(
        json.dumps(
            {
                "youtube_id": "abc",
                "title": "Old",
                "publish_date": "2024-01-01",
                "duration_seconds": 10,
                "thumbnail": "https://img.youtube.com/abc/high.jpg",
                "view_count": 5,
            }
        )
        + "\n"
    )
    info = {
        "abc": em.VideoInfo(
            title="New",
            publish_date="2025-02-02",
            duration_seconds=20,
            thumbnail="https://img.youtube.com/abc/maxres.jpg",
            view_count=1234,
        )
    }

    updated = em.apply_updates([meta], info, dry_run=True)
    assert updated == [meta]
    data = json.loads(meta.read_text())
    assert data["title"] == "Old"
    assert data["duration_seconds"] == 10
    assert data["thumbnail"] == "https://img.youtube.com/abc/high.jpg"
    assert data["view_count"] == 5

    updated = em.apply_updates([meta], info, dry_run=False)
    assert updated == [meta]
    data = json.loads(meta.read_text())
    assert data["title"] == "New"
    assert data["publish_date"] == "2025-02-02"
    assert data["duration_seconds"] == 20
    assert data["thumbnail"] == "https://img.youtube.com/abc/maxres.jpg"
    assert data["view_count"] == 1234


def test_main_dry_run_and_update(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = tmp_path
    scripts = repo / "video_scripts" / "slug"
    scripts.mkdir(parents=True)
    meta_path = scripts / "metadata.json"
    meta_path.write_text(
        json.dumps(
            {
                "youtube_id": "abc",
                "title": "Old",
                "publish_date": "",
                "duration_seconds": 0,
            }
        )
        + "\n"
    )

    monkeypatch.setenv(em.ENV_VAR, "token")
    monkeypatch.setattr(em, "VIDEO_ROOT", repo / "video_scripts")

    def fake_fetch(ids: list[str], youtube_key: str):
        assert youtube_key == "token"
        assert ids == ["abc"]
        return {
            "abc": em.VideoInfo(
                title="Fresh",
                publish_date="2025-02-02",
                duration_seconds=90,
                thumbnail="https://img.youtube.com/abc/maxres.jpg",
                view_count=321,
            )
        }

    monkeypatch.setattr(em, "fetch_video_metadata", fake_fetch)

    exit_code = em.main(["--dry-run"])
    assert exit_code == 0
    assert json.loads(meta_path.read_text())["title"] == "Old"
    dry_output = capsys.readouterr().out
    assert "Would update" in dry_output
    assert str(meta_path) in dry_output

    capsys.readouterr()
    exit_code = em.main([])
    assert exit_code == 0
    data = json.loads(meta_path.read_text())
    assert data["title"] == "Fresh"
    assert data["publish_date"] == "2025-02-02"
    assert data["duration_seconds"] == 90
    assert data["thumbnail"] == "https://img.youtube.com/abc/maxres.jpg"
    assert data["view_count"] == 321
    full_output = capsys.readouterr().out
    assert "Updated" in full_output
