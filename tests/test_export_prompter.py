import pathlib

import pytest

from video_scripts.export_prompter import build_chapters, export_prompter, plain_text


def test_visual_aligned_chapters_and_transcript_fallback():
    segments = [
        {"type": "narrator", "text": "One."},
        {"type": "narrator", "text": "Two."},
        {"type": "visual", "text": "Picture"},
        {"type": "narrator", "text": "Three."},
        {"type": "visual", "text": "Picture"},
    ]
    assert build_chapters(segments) == (["One. Two.", "Three."], 3)
    assert build_chapters([item for item in segments if item["type"] != "visual"]) == (
        ["One.", "Two.", "Three."],
        3,
    )


def test_plain_text_markdown_cleanup():
    value = "**Bold** *words*, `code`, [a link](https://example.com). <!-- timing -->"
    assert plain_text(value) == "Bold words, code, a link."


def test_placeholder_failure_leaves_no_output_and_allow_is_deterministic(tmp_path):
    script = tmp_path / "script.md"
    output = tmp_path / "nested" / "prompter.txt"
    script.write_text(
        "# Test\n\n> Draft script for video `draft`\n\n## Script\n\n[NARRATOR]: Use <value>.\n"
    )
    with pytest.raises(ValueError, match=r"<value>"):
        export_prompter(script, output)
    assert not output.exists()
    assert export_prompter(script, output, allow_placeholders=True) == (1, 1)
    first = output.read_bytes()
    assert first == b"Use <value>.\n"
    export_prompter(script, output, allow_placeholders=True)
    assert output.read_bytes() == first


def test_sugarkube_invariant(tmp_path):
    root = pathlib.Path(__file__).resolve().parents[1]
    script = root / "video_scripts" / "20260901_sugarkube" / "script.md"
    output = tmp_path / "prompter.txt"
    assert export_prompter(script, output, allow_placeholders=True) == (42, 109)
    text = output.read_text()
    assert text.endswith("\n") and not text.endswith("\n\n")
    assert len(text.rstrip("\n").split("\n\n")) == 42
    for forbidden in ("[NARRATOR]", "[VISUAL]", "<!--", "## ", "**", "`"):
        assert forbidden not in text
