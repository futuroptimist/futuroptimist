import json
import pathlib

import jsonschema
import pytest

from src.video_script_format import (
    ScriptFormatError,
    format_script,
    main,
    parse_script,
    validate_script,
)


def canonical(body="[NARRATOR]: Hello.", *, source="Draft script", outline=""):
    outline_block = f"\n\n## Outline\n\n- {outline}" if outline else ""
    return f"# Title\n\n> {source} for video `draft`{outline_block}\n\n## Script\n\n{body}\n"


@pytest.mark.parametrize(
    ("source", "outline", "body"),
    [
        (
            "Draft script",
            "Opening",
            "### Hook\n\n[NARRATOR]: Hello.\n\n[VISUAL]: Rack.",
        ),
        ("Transcript", "", "[NARRATOR]: Hello."),
        ("Transcript", "", "[NARRATOR]: Hello.  <!-- 00:00:01,000 -> 00:00:02,000 -->"),
    ],
)
def test_valid_documents(source, outline, body):
    parsed = parse_script(canonical(body, source=source, outline=outline))
    validate_script(parsed)
    assert format_script(parsed) == canonical(body, source=source, outline=outline)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "# Title\n\n## Script\n\n[NARRATOR]: Hi.\n",
        "# Title\n\n> Draft script for video `draft`\n",
        canonical("[NARRATOR]:"),
        canonical("[SFX]: Bang"),
        canonical("ordinary prose"),
    ],
)
def test_invalid_documents(text):
    with pytest.raises(ScriptFormatError):
        parse_script(text)


def test_schema_rejects_extra_property():
    parsed = parse_script(canonical())
    parsed.data["surprise"] = True
    with pytest.raises(jsonschema.ValidationError):
        validate_script(parsed)


def test_metadata_mismatch(tmp_path):
    path = tmp_path / "script.md"
    path.write_text(canonical(source="Transcript"))
    (tmp_path / "metadata.json").write_text(json.dumps({"youtube_id": "real-id"}))
    parsed = parse_script(path.read_text())
    parsed.data["video_id"] = "different-id"
    with pytest.raises(ScriptFormatError, match="does not match"):
        validate_script(parsed, path)


def test_legacy_migration_is_idempotent_and_preserves_content():
    legacy = """# Legacy
> YouTube ID: draft

## Script
[NARRATOR]: *Exact* words. <!-- 00:00:01,000 -> 00:00:02,000 -->
[VISUAL]: Exact picture!
"""
    formatted = format_script(parse_script(legacy, legacy=True))
    assert "*Exact* words." in formatted
    assert "<!-- 00:00:01,000 -> 00:00:02,000 -->" in formatted
    assert "[VISUAL]: Exact picture!" in formatted
    assert format_script(parse_script(formatted, legacy=True)) == formatted


def test_write_then_check_recursively_discovers_drafts(tmp_path):
    path = tmp_path / "video_scripts" / "drafts" / "one" / "script.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Draft\n> YouTube ID: draft\n## Script\n[NARRATOR]: Hi.\n")
    assert main(["--check", str(tmp_path / "video_scripts")]) == 1
    assert main(["--write", str(tmp_path / "video_scripts")]) == 0
    assert main(["--check", str(tmp_path / "video_scripts")]) == 0


def test_every_committed_script_is_valid_and_canonical():
    root = pathlib.Path(__file__).resolve().parents[1] / "video_scripts"
    for path in root.rglob("script.md"):
        text = path.read_text(encoding="utf-8")
        parsed = parse_script(text)
        validate_script(parsed, path)
        assert format_script(parsed) == text
