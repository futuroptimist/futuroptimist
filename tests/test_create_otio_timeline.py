import pathlib
from collections.abc import Iterable

import opentimelineio as otio
import pytest

import src.create_otio_timeline as cot


def _touch_files(root: pathlib.Path, names: Iterable[str]) -> None:
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"clip")


def test_create_timeline_writes_otio_with_relative_metadata(
    tmp_path: pathlib.Path,
) -> None:
    slug = "20251105_test"
    footage_root = tmp_path / "footage"
    converted = footage_root / slug / "converted"
    _touch_files(
        converted,
        ["b.mp4", "a.mp4", "nested/c.mp4", "ignore.txt", "audio/track.wav"],
    )

    output_dir = tmp_path / "timelines"
    result = cot.create_timeline(
        slug,
        footage_root=footage_root,
        output_dir=output_dir,
        frame_rate=30,
        default_duration=1.5,
    )

    assert result == output_dir / f"{slug}.otio"
    assert result.exists()

    timeline = otio.adapters.read_from_file(str(result))
    assert timeline.name == slug
    metadata = timeline.metadata.get("futuroptimist", {})
    assert metadata["slug"] == slug
    assert metadata["frame_rate"] == 30
    assert metadata["default_duration_seconds"] == pytest.approx(1.5)
    assert metadata["clip_count"] == 3

    tracks = list(timeline.tracks)
    assert len(tracks) == 1
    track = tracks[0]
    assert [clip.name for clip in track] == [
        "converted/a.mp4",
        "converted/b.mp4",
        "converted/nested/c.mp4",
    ]

    first = track[0]
    assert first.source_range.duration.rate == 30
    assert first.source_range.duration.value == 45

    rel_path = f"footage/{slug}/converted/a.mp4"
    assert first.metadata["futuroptimist"]["relative_path"] == rel_path
    assert first.media_reference.target_url == (converted / "a.mp4").resolve().as_uri()


def test_create_timeline_raises_when_no_video(tmp_path: pathlib.Path) -> None:
    slug = "20251201_empty"
    footage_root = tmp_path / "footage"
    (footage_root / slug / "converted").mkdir(parents=True)

    with pytest.raises(ValueError):
        cot.create_timeline(
            slug, footage_root=footage_root, output_dir=tmp_path / "out"
        )


def test_main_writes_timeline_and_prints_path(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    slug = "20251111_cli"
    footage_root = tmp_path / "footage"
    converted = footage_root / slug / "converted"
    _touch_files(converted, ["clip.mp4"])

    monkeypatch.chdir(tmp_path)
    exit_code = cot.main(
        [
            "--slug",
            slug,
            "--footage-root",
            str(footage_root),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    assert exit_code == 0
    timeline_path = tmp_path / "out" / f"{slug}.otio"
    assert timeline_path.exists()
    captured = capsys.readouterr()
    assert str(timeline_path) in captured.out
