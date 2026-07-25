import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.video_script_format import ScriptFormatError, format_script, parse_script

BASE = """# Title

> Draft script for video `draft`

## Script

[NARRATOR]: Hello. <!-- 00:00 -> 00:01 -->

[VISUAL]: Wave.
"""


def test_valid_variants_and_round_trip():
    parsed = parse_script(BASE)
    assert parsed.data["segments"][0]["timing"] == "00:00 -> 00:01"
    assert format_script(parsed) == BASE
    transcript = BASE.replace("Draft script", "Transcript").replace(
        "\n[VISUAL]: Wave.\n", "\n"
    )
    assert parse_script(transcript).data["document_kind"] == "transcript"
    outlined = BASE.replace(
        "## Script", "## Outline\n\n- Hook\n\n## Script\n\n### Opening"
    )
    assert parse_script(outlined).data["outline"] == ["Hook"]


@pytest.mark.parametrize(
    "text",
    [
        "",
        "# Title\n\n## Script\n\n[NARRATOR]: Hi.\n",
        "# Title\n\n> Draft script for video `draft`\n",
        BASE.replace("[NARRATOR]: Hello. <!-- 00:00 -> 00:01 -->", "[NARRATOR]:"),
        BASE.replace("[NARRATOR]", "[SPEAKER]"),
        BASE.replace("[VISUAL]: Wave.", "plain prose"),
    ],
)
def test_invalid_documents(text):
    with pytest.raises(ScriptFormatError):
        parse_script(text)


def test_legacy_migration_is_idempotent_and_preserves_text():
    legacy = (
        "# T\n> YouTube ID: draft\n\n## Script\n> 0:00 Intro\n"
        "[NARRATOR]: Exact *words*.\n[VISUAL]: Exact cue.\n"
    )
    once = format_script(parse_script(legacy, migrate=True))
    assert format_script(parse_script(once, migrate=True)) == once
    assert "Exact *words*." in once and "Exact cue." in once


def test_cli_check_write_recursive_and_metadata_mismatch(tmp_path):
    script = tmp_path / "drafts" / "x" / "script.md"
    script.parent.mkdir(parents=True)
    script.write_text("# T\n> YouTube ID: draft\n## Script\n[NARRATOR]: Hi.\n")
    tool = Path("src/video_script_format.py")
    assert subprocess.run([sys.executable, tool, "--check", tmp_path]).returncode
    assert not subprocess.run([sys.executable, tool, "--write", tmp_path]).returncode
    assert not subprocess.run([sys.executable, tool, "--check", tmp_path]).returncode
    script.with_name("metadata.json").write_text(json.dumps({"youtube_id": "real"}))
    script.write_text(script.read_text().replace("`draft`", "`wrong`"))
    assert subprocess.run([sys.executable, tool, "--check", tmp_path]).returncode


def test_all_repository_scripts_are_canonical():
    for path in Path("video_scripts").rglob("script.md"):
        assert format_script(parse_script(path.read_text())) == path.read_text()
