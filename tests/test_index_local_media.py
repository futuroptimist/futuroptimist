import json
import runpy
import sys
from datetime import datetime, timezone

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


def test_scan_directory_utc_mtime(tmp_path):
    file_path = tmp_path / "clip.mp4"
    file_path.write_text("data")
    result = ilm.scan_directory(tmp_path)
    ts = result[0]["mtime"].replace("Z", "+00:00")
    mtime = datetime.fromisoformat(ts)
    assert mtime.tzinfo == timezone.utc


def test_main(tmp_path, capsys):
    f = tmp_path / "x.txt"
    f.write_text("hi")
    out_file = tmp_path / "index.json"
    ilm.main([str(tmp_path), "-o", str(out_file)])
    captured = capsys.readouterr()
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert data[0]["path"] == "x.txt"
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


def test_entrypoint(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["index_local_media.py", str(tmp_path)])
    (tmp_path).mkdir(exist_ok=True)

    runpy.run_module("src.index_local_media", run_name="__main__")
