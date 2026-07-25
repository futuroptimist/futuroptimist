import pathlib
import subprocess
import sys

from src.video_script_format import parse_script
from video_scripts.export_prompter import chapters, export


def document(body):
    return parse_script(
        f"# T\n\n> Draft script for video `draft`\n\n## Script\n\n{body}\n"
    )


def test_visual_grouping_and_cleanup():
    result = chapters(
        document(
            "[NARRATOR]: **Hello** [world](https://example.com) `now`. "
            "<!-- 0 -> 1 -->\n\n[NARRATOR]: Again.\n\n[VISUAL]: Shot.\n\n"
            "[NARRATOR]: Last.\n\n[VISUAL]: End."
        )
    )
    assert result == ["Hello world now. Again.", "Last."]


def test_transcript_fallback():
    assert chapters(document("[NARRATOR]: One.\n\n[NARRATOR]: Two.")) == [
        "One.",
        "Two.",
    ]


def test_placeholder_failure_has_no_partial_file(tmp_path, capsys):
    script = tmp_path / "script.md"
    output = tmp_path / "prompter.txt"
    script.write_text(
        "# T\n\n> Draft script for video `draft`\n\n## Script\n\n[NARRATOR]: <value> and <value>.\n"
    )
    assert export(script, output, allow_placeholders=False) == 1
    assert not output.exists()
    assert capsys.readouterr().err.count("<value>") == 1
    assert export(script, output, allow_placeholders=True) == 0
    assert output.read_text() == "<value> and <value>.\n"


def test_sugarkube_invariant_and_cli(tmp_path):
    script = pathlib.Path("video_scripts/20260901_sugarkube/script.md")
    parsed = parse_script(script.read_text())
    assert len(chapters(parsed)) == 42
    assert sum(s["type"] == "narrator" for s in parsed["segments"]) == 109
    output = tmp_path / "custom.txt"
    command = [
        sys.executable,
        "video_scripts/export_prompter.py",
        "--script",
        str(script),
        "--allow-placeholders",
        "--output",
        str(output),
    ]
    assert subprocess.run(command, check=False).returncode == 0
    first = output.read_text()
    assert first.endswith("\n") and not first.endswith("\n\n")
    assert not any(token in first for token in ("[NARRATOR]", "[VISUAL]", "<!--", "##"))
    assert subprocess.run(command, check=False).returncode == 0
    assert output.read_text() == first
