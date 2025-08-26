import json
import runpy
import sys
from datetime import datetime, timezone
import os
import pathlib
import warnings

import pytest

import src.index_local_media as ilm


def test_scan_directory(tmp_path):
    (tmp_path / "dir").mkdir()
    f1 = tmp_path / "dir" / "a.jpg"
    f1.write_text("a")
    f2 = tmp_path / "b.mp4"
    f2.write_text("b")
    result = ilm.scan_directory(tmp_path)
    names = {r["path"] for r in result}
    assert names == {"dir/a.jpg", "b.mp4"}
    sizes = {r["size"] for r in result}
    assert sizes == {1}


def test_scan_directory_excludes_directory(tmp_path):
    skip = tmp_path / "skip"
    skip.mkdir()
    (skip / "ignore.mov").write_text("x")
    keep = tmp_path / "keep.mp4"
    keep.write_text("y")
    result = ilm.scan_directory(tmp_path, exclude=[skip])
    names = {r["path"] for r in result}
    assert names == {"keep.mp4"}


def test_scan_directory_utc_mtime(tmp_path):
    file_path = tmp_path / "clip.mp4"
    file_path.write_text("data")
    result = ilm.scan_directory(tmp_path)
    ts = result[0]["mtime"].replace("Z", "+00:00")
    mtime = datetime.fromisoformat(ts)
    assert mtime.tzinfo == timezone.utc


def test_scan_directory_truncates_microseconds(tmp_path):
    file_path = tmp_path / "clip.mp4"
    file_path.write_text("data")
    os.utime(file_path, (1234567890.654321, 1234567890.654321))
    result = ilm.scan_directory(tmp_path)
    ts = result[0]["mtime"].replace("Z", "+00:00")
    mtime = datetime.fromisoformat(ts)
    assert mtime.microsecond == 0


def test_main(tmp_path, capsys):
    f = tmp_path / "x.txt"
    f.write_text("hi")
    out_file = tmp_path / "index.json"
    ilm.main([str(tmp_path), "-o", str(out_file)])
    captured = capsys.readouterr()
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert data[0]["path"] == "x.txt"
    assert data[0]["size"] == 2
    assert "Wrote" in captured.out


def test_main_invalid_dir(tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(SystemExit):
        ilm.main([str(missing)])


def test_creates_output_parent_dirs(tmp_path):
    f = tmp_path / "clip.mov"
    f.write_text("x")
    nested = tmp_path / "out" / "dir" / "index.json"
    ilm.main([str(tmp_path), "-o", str(nested)])
    assert nested.exists()


def test_main_writes_trailing_newline(tmp_path):
    (tmp_path / "clip.mov").write_text("x")
    out_file = tmp_path / "index.json"
    ilm.main([str(tmp_path), "-o", str(out_file)])
    assert out_file.read_text().endswith("\n")


def test_main_excludes_existing_output(tmp_path):
    f = tmp_path / "clip.mov"
    f.write_text("x")
    out_file = tmp_path / "index.json"
    out_file.write_text("old")
    ilm.main([str(tmp_path), "-o", str(out_file)])
    data = json.loads(out_file.read_text())
    assert all(entry["path"] != "index.json" for entry in data)


def test_main_excludes_directory_via_cli(tmp_path):
    keep = tmp_path / "keep.mov"
    keep.write_text("x")
    skip_dir = tmp_path / "skip"
    skip_dir.mkdir()
    (skip_dir / "ignore.mp4").write_text("y")
    out_file = tmp_path / "index.json"
    ilm.main([str(tmp_path), "--exclude", str(skip_dir), "-o", str(out_file)])
    data = json.loads(out_file.read_text())
    names = {entry["path"] for entry in data}
    assert "keep.mov" in names and all(not name.startswith("skip/") for name in names)


def test_scan_directory_deterministic_order(tmp_path, monkeypatch):
    f1 = tmp_path / "b.txt"
    f2 = tmp_path / "a.txt"
    for f in (f1, f2):
        f.write_text("x")
        os.utime(f, (1234567890, 1234567890))

    def fake_rglob(self, pattern):
        assert self == tmp_path
        return [f1, f2]

    monkeypatch.setattr(pathlib.Path, "rglob", fake_rglob)
    result = ilm.scan_directory(tmp_path)
    assert [r["path"] for r in result] == ["a.txt", "b.txt"]


def test_entrypoint(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["index_local_media.py", str(tmp_path)])
    (tmp_path).mkdir(exist_ok=True)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=".*found in sys.modules.*",
            category=RuntimeWarning,
        )
        runpy.run_module("src.index_local_media", run_name="__main__")
