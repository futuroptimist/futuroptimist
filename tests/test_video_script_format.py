import json
import pathlib
import subprocess
import sys

import pytest

from src.video_script_format import ScriptFormatError, format_script, parse_script, run

BASE = (
    "# Title\n\n> Draft script for video `draft`\n\n## Script\n\n[NARRATOR]: Hello.\n"
)


def test_valid_variants_and_idempotence():
    text = (
        "# Title\n\n> Transcript for video `abc`\n\n## Outline\n\n- Hook\n\n"
        "## Script\n\n### Intro\n\n"
        "[NARRATOR]: *Hello.*  <!-- 00:00 -> 00:01 -->\n"
    )
    document = parse_script(text)
    assert document["outline"] == ["Hook"]
    assert document["segments"][-1]["timing"] == {"start": "00:00", "end": "00:01"}
    assert format_script(document) == text
    assert parse_script(BASE)["segments"][0]["type"] == "narrator"


@pytest.mark.parametrize(
    "text,message",
    [
        ("", "H1"),
        ("# Title\n\n## Script\n", "source"),
        ("# Title\n\n> Draft script for video `draft`\n", "## Script"),
        (BASE.replace("Hello.", ""), "empty narrator"),
        (BASE.replace("[NARRATOR]", "[SPEAKER]"), "script body"),
        (BASE.replace("[NARRATOR]: Hello.", "plain prose"), "script body"),
    ],
)
def test_invalid_documents(text, message):
    with pytest.raises(ScriptFormatError, match=message):
        parse_script(text)


def test_schema_rejection(monkeypatch):
    import src.video_script_format as module

    monkeypatch.setattr(module, "SCHEMA_PATH", pathlib.Path("/dev/null"))
    with pytest.raises(json.JSONDecodeError):
        parse_script(BASE)


def test_legacy_migration_and_recursive_discovery(tmp_path):
    path = tmp_path / "drafts" / "one" / "script.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "# Title\n> YouTube ID: draft\n\n## Script\n[NARRATOR]: Hello.\n[VISUAL]: Shot.\n"
    )
    assert run(tmp_path, write=False) == 1
    assert run(tmp_path, write=True) == 0
    expected = (
        "# Title\n\n> Draft script for video `draft`\n\n## Script\n\n"
        "[NARRATOR]: Hello.\n\n[VISUAL]: Shot.\n"
    )
    assert path.read_text() == expected
    assert run(tmp_path, write=False) == 0


def test_metadata_mismatch(tmp_path):
    path = tmp_path / "script.md"
    path.write_text(BASE.replace("`draft`", "`wrong`"))
    path.with_name("metadata.json").write_text('{"youtube_id":"right"}')
    assert run(path, write=False) == 1


def test_all_committed_scripts_are_canonical():
    assert run(pathlib.Path("video_scripts"), write=False) == 0


def test_cli_check_is_read_only(tmp_path):
    path = tmp_path / "script.md"
    path.write_text(BASE.replace("\n\n[NARRATOR]", "\n[NARRATOR]"))
    before = path.read_text()
    result = subprocess.run(
        [sys.executable, "src/video_script_format.py", "--check", str(path)],
        check=False,
    )
    assert result.returncode == 1
    assert path.read_text() == before
