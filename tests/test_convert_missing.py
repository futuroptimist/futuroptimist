import json
import sys

import src.convert_missing as cm


def test_convert_missing_invokes_convert_assets(monkeypatch, tmp_path):
    report = tmp_path / "verify_report.json"
    report.write_text(
        json.dumps(
            {
                "errors": [
                    "Missing converted for footage/20250101_demo/originals/a.heic",
                    "Missing converted for footage/20250101_demo/originals/b.mov",
                    "Missing converted for 20250102_other/originals/c.dng",
                    "Likely grayscale: footage/20250101_demo/converted/a.png",
                ]
            }
        )
    )

    calls: list[list[str]] = []

    class Result:
        returncode = 0

    def fake_run(cmd):
        calls.append(cmd)
        return Result()

    monkeypatch.setattr(cm.subprocess, "run", fake_run)
    exit_code = cm.main(["--report", str(report)])
    assert exit_code == 0
    assert len(calls) == 1
    cmd = calls[0]
    assert cmd[0] == sys.executable
    assert cmd[1] == "src/convert_assets.py"
    assert "--force" not in cmd
    assert cmd.count("--include-video") == 1
    # Sources should be restricted to the missing originals
    sources = [cmd[i + 1] for i, token in enumerate(cmd) if token == "--source"]
    assert sources == [
        "20250101_demo/originals/a.heic",
        "20250101_demo/originals/b.mov",
        "20250102_other/originals/c.dng",
    ]
    # Slugs should be limited to the missing entries
    slugs = [cmd[i + 1] for i, token in enumerate(cmd) if token == "--slug"]
    assert slugs == ["20250101_demo", "20250102_other"]


def test_convert_missing_no_missing(tmp_path, capsys):
    report = tmp_path / "verify_report.json"
    report.write_text(json.dumps({"errors": ["Likely grayscale: foo"]}))

    exit_code = cm.main(["--report", str(report)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "No missing items" in captured.out
