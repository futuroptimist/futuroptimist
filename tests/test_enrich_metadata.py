import json
from pathlib import Path

import pytest

import src.enrich_metadata as em


@pytest.fixture
def sample_metadata(tmp_path: Path) -> Path:
    video_root = tmp_path / "video_scripts" / "20240101_demo"
    video_root.mkdir(parents=True)
    meta = video_root / "metadata.json"
    meta.write_text(
        json.dumps(
            {
                "youtube_id": "abc123",
                "title": "Placeholder",
                "publish_date": "2024-01-01",
                "duration_seconds": 0,
                "status": "draft",
                "description": "",
            }
        )
        + "\n"
    )
    return meta


def test_apply_updates_writes_changes(sample_metadata: Path) -> None:
    info = em.VideoInfo(
        title="Updated Title",
        publish_date="2024-01-02",
        duration_seconds=321,
    )
    updated = em.apply_updates([sample_metadata], {"abc123": info}, dry_run=False)
    assert updated == [sample_metadata]
    data = json.loads(sample_metadata.read_text())
    assert data["title"] == "Updated Title"
    assert data["publish_date"] == "2024-01-02"
    assert data["duration_seconds"] == 321
    assert sample_metadata.read_bytes().endswith(b"\n")


def test_apply_updates_dry_run(sample_metadata: Path) -> None:
    info = em.VideoInfo(
        title="Another Title",
        publish_date="2024-02-10",
        duration_seconds=111,
    )
    updated = em.apply_updates([sample_metadata], {"abc123": info}, dry_run=True)
    assert updated == [sample_metadata]
    data = json.loads(sample_metadata.read_text())
    # No changes because dry-run
    assert data["title"] == "Placeholder"
    assert data["publish_date"] == "2024-01-01"
    assert data["duration_seconds"] == 0


def test_main_dry_run(monkeypatch: pytest.MonkeyPatch, sample_metadata: Path) -> None:
    video_root = sample_metadata.parent.parent
    seen: list[tuple[str, ...]] = []

    def fake_fetch(ids, youtube_key: str):
        seen.append(tuple(ids))
        assert youtube_key == "TOKEN"
        return {
            "abc123": em.VideoInfo(
                title="CLI Title",
                publish_date="2024-03-04",
                duration_seconds=222,
            )
        }

    monkeypatch.setenv("YOUTUBE_API_KEY", "TOKEN")
    monkeypatch.setattr(em, "fetch_video_metadata", fake_fetch)
    exit_code = em.main(["--video-root", str(video_root), "--dry-run"])
    assert exit_code == 0
    assert seen == [("abc123",)]
    # Original file remains unchanged because dry-run
    data = json.loads(sample_metadata.read_text())
    assert data["title"] == "Placeholder"


@pytest.mark.parametrize(
    "duration,expected",
    [
        ("PT5M33S", 5 * 60 + 33),
        ("PT1H2M3S", 3723),
        ("PT0S", 0),
        ("P1DT1H", 24 * 3600 + 3600),
        ("P1W", 7 * 24 * 3600),
    ],
)
def test_parse_duration(duration: str, expected: int) -> None:
    assert em.parse_duration(duration) == expected
