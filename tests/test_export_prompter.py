from pathlib import Path

import pytest

from video_scripts import export_prompter


def _write(path: Path, body: str) -> None:
    path.write_text("# T\n\n> Draft script for video `draft`\n\n## Script\n\n" + body)


def test_visual_grouping_and_markdown_cleanup(tmp_path: Path) -> None:
    script = tmp_path / "script.md"
    body = """[NARRATOR]: **Hello** [site](https://x) `code`. <!-- 0 -> 1 -->

[NARRATOR]: Next.

[VISUAL]: Shot.

[NARRATOR]: End.

[VISUAL]: End shot.
"""
    _write(script, body)
    output = tmp_path / "out.txt"
    assert export_prompter.export(script, output) == (2, 3)
    assert output.read_text() == "Hello site code. Next.\n\nEnd.\n"


def test_markdown_cleanup_preserves_identifier_underscores() -> None:
    assert export_prompter.plain_text("Use `foo_bar` and foo_bar, not _italics_.") == (
        "Use foo_bar and foo_bar, not italics."
    )


def test_transcript_fallback_has_one_chapter_per_segment(tmp_path: Path) -> None:
    script = tmp_path / "script.md"
    _write(script, "[NARRATOR]: One.\n\n[NARRATOR]: Two.\n")
    output = tmp_path / "out.txt"
    assert export_prompter.export(script, output) == (2, 2)
    assert output.read_text() == "One.\n\nTwo.\n"


def test_placeholder_failure_leaves_existing_output_untouched(
    tmp_path: Path, capsys
) -> None:
    script = tmp_path / "script.md"
    _write(script, "[NARRATOR]: Values <watts> and <watts>.\n")
    output = tmp_path / "prompter.txt"
    output.write_text("old\n")
    assert export_prompter.main(["--script", str(script), "--output", str(output)]) == 1
    assert output.read_text() == "old\n"
    assert "<watts>" in capsys.readouterr().err
    assert (
        export_prompter.main(
            ["--script", str(script), "--output", str(output), "--allow-placeholders"]
        )
        == 0
    )


def test_empty_cleaned_narration_requires_rehearsal_mode(tmp_path: Path) -> None:
    script = tmp_path / "script.md"
    _write(script, "[NARRATOR]: <!-- narrator lines here -->\n")
    output = tmp_path / "prompter.txt"
    output.write_text("old\n")

    with pytest.raises(ValueError, match="narration is empty"):
        export_prompter.export(script, output)
    assert output.read_text() == "old\n"
    assert export_prompter.export(script, output, allow_placeholders=True) == (1, 1)


def test_sugarkube_invariant(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "prompter.txt"
    result = export_prompter.export(
        root / "video_scripts/20260901_sugarkube/script.md",
        output,
        allow_placeholders=True,
    )
    assert result == (42, 109)
    text = output.read_text()
    assert all(
        marker not in text for marker in ("[NARRATOR]", "[VISUAL]", "<!--", "##")
    )
    assert text.endswith("\n") and not text.endswith("\n\n")
