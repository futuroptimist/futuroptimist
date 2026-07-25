import subprocess
import sys
from pathlib import Path

from src.video_script_format import parse_script
from video_scripts.export_prompter import build_chapters, plain_text


def test_cleanup_and_visual_grouping():
    text = """# T

> Draft script for video `draft`

## Script

[NARRATOR]: **Hello** [world](https://example.test). <!-- time -->

[NARRATOR]: `Code`.

[VISUAL]: Cue.
"""
    chapters, count = build_chapters(parse_script(text).data)
    assert chapters == ["Hello world. Code."]
    assert count == 2
    assert plain_text("_one_ ~~two~~") == "one two"


def test_transcript_fallback():
    text = (
        "# T\n\n> Transcript for video `id`\n\n## Script\n\n"
        "[NARRATOR]: One.\n\n[NARRATOR]: Two.\n"
    )
    assert build_chapters(parse_script(text).data)[0] == ["One.", "Two."]


def test_cli_placeholders_custom_paths_and_no_partial_output(tmp_path):
    script = tmp_path / "script.md"
    output = tmp_path / "out.txt"
    script.write_text(
        "# T\n\n> Draft script for video `draft`\n\n## Script\n\n[NARRATOR]: Say <name>.\n"
    )
    cmd = [
        sys.executable,
        "video_scripts/export_prompter.py",
        "--script",
        str(script),
        "--output",
        str(output),
    ]
    failed = subprocess.run(cmd, capture_output=True, text=True)
    assert failed.returncode and "<name>" in failed.stderr and not output.exists()
    assert not subprocess.run([*cmd, "--allow-placeholders"]).returncode
    assert output.read_text() == "Say <name>.\n"


def test_sugarkube_invariant():
    path = Path("video_scripts/20260901_sugarkube/script.md")
    chapters, count = build_chapters(parse_script(path.read_text()).data)
    assert (len(chapters), count) == (42, 109)
    output = "\n\n".join(chapters) + "\n"
    assert all(
        marker not in output for marker in ("[NARRATOR]", "[VISUAL]", "<!--", "## ")
    )
