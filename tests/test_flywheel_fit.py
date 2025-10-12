from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

import flywheel.fit as fit


def test_verify_fit_skips_when_cad_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = fit.verify_fit(cad_dir=tmp_path / "cad", stl_dir=tmp_path / "stl")
    assert result is True
    captured = capsys.readouterr()
    assert "Skipping fit check" in captured.out


def test_verify_fit_requires_matching_stl(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    stl = tmp_path / "stl"
    cad.mkdir()
    stl.mkdir()
    (cad / "wheel.scad").write_text("module wheel(){}\n", encoding="utf-8")
    (stl / "wheel.obj").write_text("solid wheel\n", encoding="utf-8")

    with pytest.raises(AssertionError) as exc:
        fit.verify_fit(cad_dir=cad, stl_dir=stl)

    assert "Missing STL" in str(exc.value)


def test_verify_fit_detects_stale_export(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    stl = tmp_path / "stl"
    cad.mkdir()
    stl.mkdir()
    scad = cad / "shaft.scad"
    stl_file = stl / "shaft.stl"
    obj_file = stl / "shaft.obj"
    scad.write_text("module shaft(){}\n", encoding="utf-8")
    stl_file.write_text("solid shaft\n", encoding="utf-8")
    obj_file.write_text("solid shaft obj\n", encoding="utf-8")

    now = time.time()
    os.utime(scad, (now, now))
    os.utime(stl_file, (now - 60, now - 60))
    os.utime(obj_file, (now, now))

    with pytest.raises(AssertionError) as exc:
        fit.verify_fit(cad_dir=cad, stl_dir=stl, time_tolerance=0.5)

    assert "stale export" in str(exc.value)


def test_verify_fit_detects_stale_obj(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    stl = tmp_path / "stl"
    cad.mkdir()
    stl.mkdir()
    scad = cad / "gear.scad"
    stl_file = stl / "gear.stl"
    obj_file = stl / "gear.obj"
    scad.write_text("module gear(){}\n", encoding="utf-8")
    stl_file.write_text("solid gear stl\n", encoding="utf-8")
    obj_file.write_text("solid gear obj\n", encoding="utf-8")

    now = time.time()
    os.utime(scad, (now, now))
    os.utime(stl_file, (now, now))
    os.utime(obj_file, (now - 120, now - 120))

    with pytest.raises(AssertionError) as exc:
        fit.verify_fit(cad_dir=cad, stl_dir=stl, time_tolerance=1.0)

    assert "gear.obj" in str(exc.value)


def test_verify_fit_passes_when_up_to_date(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    stl = tmp_path / "stl"
    cad.mkdir()
    stl.mkdir()
    scad = cad / "adapter.scad"
    stl_file = stl / "adapter.stl"
    obj_file = stl / "adapter.obj"
    scad.write_text("module adapter(){}\n", encoding="utf-8")
    stl_file.write_text("solid adapter\n", encoding="utf-8")
    obj_file.write_text("solid adapter obj\n", encoding="utf-8")

    now = time.time()
    os.utime(scad, (now - 10, now - 10))
    os.utime(stl_file, (now, now))
    os.utime(obj_file, (now, now))

    assert fit.verify_fit(cad_dir=cad, stl_dir=stl)


def test_main_reports_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cad = tmp_path / "cad"
    stl = tmp_path / "stl"
    cad.mkdir()
    stl.mkdir()
    scad = cad / "ring.scad"
    stl_file = stl / "ring.stl"
    obj_file = stl / "ring.obj"
    scad.write_text("module ring(){}\n", encoding="utf-8")
    stl_file.write_text("solid ring\n", encoding="utf-8")
    obj_file.write_text("solid ring obj\n", encoding="utf-8")

    now = time.time()
    os.utime(scad, (now - 5, now - 5))
    os.utime(stl_file, (now, now))
    os.utime(obj_file, (now, now))

    monkeypatch.chdir(tmp_path)
    exit_code = fit.main([])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "All parts up to date" in captured.out


def test_main_handles_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cad = tmp_path / "cad"
    stl = tmp_path / "stl"
    cad.mkdir()
    stl.mkdir()
    (cad / "body.scad").write_text("module body(){}\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    exit_code = fit.main([])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Missing STL" in captured.err


def test_verify_fit_requires_matching_obj(tmp_path: Path) -> None:
    cad = tmp_path / "cad"
    stl = tmp_path / "stl"
    cad.mkdir()
    stl.mkdir()
    (cad / "brace.scad").write_text("module brace(){}\n", encoding="utf-8")
    (stl / "brace.stl").write_text("solid brace\n", encoding="utf-8")

    with pytest.raises(AssertionError) as exc:
        fit.verify_fit(cad_dir=cad, stl_dir=stl)

    assert "Missing OBJ" in str(exc.value)
