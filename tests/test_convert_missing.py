from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

import src.convert_missing as cm


def _write_report(path: Path, missing: list[Path]) -> None:
    errors = [f"Missing converted for {item}" for item in missing]
    payload = {"errors": errors, "count": len(errors)}
    path.write_text(json.dumps(payload, indent=2))


def test_convert_missing_only_processes_reported_files(tmp_path: Path) -> None:
    footage_root = tmp_path / "footage" / "20250101_demo"
    originals = footage_root / "originals"
    converted = footage_root / "converted"
    originals.mkdir(parents=True)
    converted.mkdir(parents=True)

    missing_src = originals / "missing.webp"
    other_src = originals / "other.webp"
    Image.new("RGB", (32, 32), color="red").save(missing_src)
    Image.new("RGB", (32, 32), color="blue").save(other_src)

    report = tmp_path / "verify_report.json"
    _write_report(report, [missing_src])

    exit_code = cm.main(["--report", str(report)])
    assert exit_code == 0

    expected_missing = converted / "missing.png"
    unexpected_other = converted / "other.png"

    assert expected_missing.exists(), "reported asset should be converted"
    assert not unexpected_other.exists(), "unreported assets must be left untouched"


def test_convert_missing_sets_video_flag(monkeypatch, tmp_path: Path) -> None:
    footage_root = tmp_path / "footage" / "20250101_demo"
    originals = footage_root / "originals"
    originals.mkdir(parents=True)
    missing_video = originals / "clip.MOV"
    missing_video.write_bytes(b"stub")

    report = tmp_path / "verify_report.json"
    _write_report(report, [missing_video])

    captured: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        captured.append(argv)
        return 0

    monkeypatch.setattr(cm.convert_assets, "main", fake_main)

    exit_code = cm.main(["--report", str(report)])
    assert exit_code == 0

    assert captured, "convert_assets.main should be invoked"
    args = captured[0]
    assert "--include-video" in args
    assert any(str(missing_video) in value for value in args)
