from __future__ import annotations

import json
import pathlib
import runpy
import sys
import warnings

import pytest

import src.index_script_hooks as ish


def _write_script(folder: pathlib.Path, body: str) -> None:
    (folder / "script.md").write_text(body, encoding="utf-8")


def _write_metadata(folder: pathlib.Path, data: dict) -> None:
    (folder / "metadata.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_build_hooks_index_extracts_first_narrator(tmp_path: pathlib.Path) -> None:
    video_root = tmp_path / "video_scripts"
    slug = "20240101_demo"
    script_dir = video_root / slug
    script_dir.mkdir(parents=True)

    comment = "<!-- 00:00:00,000 -> 00:00:02,000 -->"
    _write_script(
        script_dir,
        (
            """# Title\n\n> Draft script\n\n## Script\n\n[NARRATOR]: First hook  """
            f"{comment}\n\n[NARRATOR]: Second line\n"
        ),
    )
    _write_metadata(
        script_dir,
        {
            "youtube_id": "abc123",
            "title": "Demo",
            "publish_date": "2024-01-01",
        },
    )

    records = ish.build_hooks_index(
        video_root=video_root, output_path=tmp_path / "hooks.json"
    )
    assert records == [
        {
            "slug": slug,
            "youtube_id": "abc123",
            "title": "Demo",
            "publish_date": "2024-01-01",
            "text": "First hook",
            "start": "00:00:00,000",
            "end": "00:00:02,000",
        }
    ]

    output = json.loads((tmp_path / "hooks.json").read_text())
    assert output == records


def test_build_hooks_index_skips_missing_or_empty(tmp_path: pathlib.Path) -> None:
    video_root = tmp_path / "video_scripts"
    empty = video_root / "20240202_empty"
    empty.mkdir(parents=True)
    _write_metadata(empty, {"youtube_id": "nope"})
    _write_script(empty, "[VISUAL]: placeholder")

    missing_script = video_root / "20240303_missing"
    missing_script.mkdir()
    _write_metadata(missing_script, {"youtube_id": "skip"})

    records = ish.build_hooks_index(
        video_root=video_root, output_path=tmp_path / "hooks.json"
    )
    assert records == []


def test_entrypoint_runs(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    video_root = tmp_path / "video_scripts"
    script_dir = video_root / "20240404_entry"
    script_dir.mkdir(parents=True)
    _write_script(script_dir, "[NARRATOR]: Hook line")
    _write_metadata(script_dir, {"youtube_id": "entry"})

    out_path = tmp_path / "data" / "hooks.json"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["index_script_hooks.py", "--output", str(out_path)],
    )
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        with pytest.raises(SystemExit) as exc:
            runpy.run_module("src.index_script_hooks", run_name="__main__")
    assert exc.value.code == 0

    assert out_path.exists()
    data = json.loads(out_path.read_text())
    assert data[0]["text"] == "Hook line"
