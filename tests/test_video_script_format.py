from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import video_script_format as vsf


def test_parse_valid_full_document() -> None:
    text = """# Title

> Draft script for video `draft`

## Outline

- Hook

## Script

### Opening

[NARRATOR]: *Hello*. <!-- 00:00:00,000 -> 00:00:01,000 -->

[VISUAL]: A shot.
"""
    document = vsf.parse_script(text)
    vsf.validate_document(document)
    assert document["outline"] == ["Hook"]
    assert document["segments"][1]["timing"] == {
        "start": "00:00:00,000",
        "end": "00:00:01,000",
    }
    assert vsf.format_document(document) == text


def test_transcript_only_is_valid() -> None:
    document = vsf.parse_script(
        "# Title\n\n> Transcript for video `abc`\n\n## Script\n\n[NARRATOR]: Hello.\n"
    )
    vsf.validate_document(document)
    assert document["kind"] == "transcript"


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("", "H1"),
        ("# Title\n\n## Script\n", "source"),
        ("# Title\n\n> Draft script for video `x`\n", "## Script"),
        (
            "# Title\n\n> Draft script for video `x`\n\n## Script\n\n[NARRATOR]:\n",
            "empty",
        ),
        (
            "# Title\n\n> Draft script for video `x`\n\n## Script\n\n[AUDIO]: Hi\n",
            "must be",
        ),
        (
            "# Title\n\n> Draft script for video `x`\n\n## Script\n\nplain prose\n",
            "must be",
        ),
    ],
)
def test_invalid_documents(text: str, message: str) -> None:
    with pytest.raises(vsf.ScriptFormatError, match=message):
        vsf.parse_script(text)


def test_schema_rejects_mutated_object() -> None:
    with pytest.raises(vsf.ScriptFormatError, match="schema"):
        vsf.validate_document(
            {
                "schema_version": 1,
                "title": "T",
                "kind": "draft",
                "video_id": "x",
                "segments": [],
            }
        )


def test_legacy_migration_is_idempotent_and_preserves_text() -> None:
    legacy = """# Title
> YouTube ID: draft

> Draft outline
> Hook

## Script
[NARRATOR]: **Exact** text. <!-- 0:00 -> 0:01 -->
[VISUAL]: Exact visual!
> 0:01-0:02: Next
"""
    canonical = vsf.format_document(vsf.parse_script(legacy, migrate=True))
    assert "## Outline\n\n- Hook" in canonical
    assert "### 0:01-0:02: Next" in canonical
    assert "**Exact** text. <!-- 0:00 -> 0:01 -->" in canonical
    assert vsf.format_document(vsf.parse_script(canonical)) == canonical


@pytest.mark.parametrize(
    "comment",
    [
        "<!--  00:00:00,000   ->  00:00:01,000  -->",
        "<!-- 00:00:00,000 → 00:00:01,000 -->",
    ],
)
def test_migration_preserves_exact_timing_comment(comment: str) -> None:
    legacy = (
        "# T\n> YouTube ID: draft\n## Script\n"
        f"[NARRATOR]: Exact timing.  {comment}\n"
    )
    assert comment in vsf.format_document(vsf.parse_script(legacy, migrate=True))


def test_write_rejects_editorial_body_blockquote_without_modifying_file(
    tmp_path: Path, capsys
) -> None:
    script = tmp_path / "script.md"
    original = (
        "# T\n> YouTube ID: draft\n## Script\n"
        "[NARRATOR]: Hi.\n> Editor note: revise this.\n"
    )
    script.write_text(original)
    assert vsf.main(["--write", str(script)]) == 1
    assert script.read_text() == original
    assert f"{script}:5: cannot migrate body blockquote" in capsys.readouterr().err


def test_metadata_mismatch(tmp_path: Path) -> None:
    script = tmp_path / "script.md"
    script.write_text(
        "# T\n\n> Transcript for video `wrong`\n\n## Script\n\n[NARRATOR]: Hi.\n"
    )
    (tmp_path / "metadata.json").write_text(json.dumps({"youtube_id": "right"}))
    with pytest.raises(vsf.ScriptFormatError, match="does not match"):
        vsf.process(script, write=False)


@pytest.mark.parametrize("metadata_id", [None, "", "draft", "<youtube_id>"])
def test_metadata_sentinels_allow_script_sentinels(
    tmp_path: Path, metadata_id: str | None
) -> None:
    script = tmp_path / "script.md"
    script.write_text(
        "# T\n\n> Draft script for video `draft`\n\n" "## Script\n\n[NARRATOR]: Hi.\n"
    )
    (tmp_path / "metadata.json").write_text(json.dumps({"youtube_id": metadata_id}))
    assert vsf.process(script, write=False) is False


def test_non_object_metadata_is_clean_cli_error(tmp_path: Path, capsys) -> None:
    script = tmp_path / "script.md"
    script.write_text(
        "# T\n\n> Draft script for video `draft`\n\n" "## Script\n\n[NARRATOR]: Hi.\n"
    )
    (tmp_path / "metadata.json").write_text("[]")
    assert vsf.main(["--check", str(script)]) == 1
    assert "metadata.json must contain a JSON object" in capsys.readouterr().err


@pytest.mark.parametrize("kind", ["missing", "empty_directory"])
def test_invalid_input_is_clean_cli_error(tmp_path: Path, capsys, kind: str) -> None:
    path = tmp_path / kind
    if kind == "empty_directory":
        path.mkdir()
    assert vsf.main(["--check", str(path)]) == 1
    error = capsys.readouterr().err
    assert str(path) in error
    assert "does not exist" in error or "contains no script.md" in error


@pytest.mark.parametrize("placeholder", ["draft", "<youtube_id>"])
def test_metadata_rejects_stale_placeholder(tmp_path: Path, placeholder: str) -> None:
    script = tmp_path / "script.md"
    script.write_text(
        f"# T\n\n> Draft script for video `{placeholder}`\n\n"
        "## Script\n\n[NARRATOR]: Hi.\n"
    )
    (tmp_path / "metadata.json").write_text(json.dumps({"youtube_id": "assigned-id"}))
    with pytest.raises(vsf.ScriptFormatError, match="does not match"):
        vsf.process(script, write=True)


def test_check_is_read_only_and_write_migrates_recursively(tmp_path: Path) -> None:
    script = tmp_path / "drafts" / "demo" / "script.md"
    script.parent.mkdir(parents=True)
    script.write_text("# T\n> YouTube ID: draft\n## Script\n[NARRATOR]: Hi.\n")
    original = script.read_text()
    assert vsf.main(["--check", str(tmp_path)]) == 1
    assert script.read_text() == original
    assert vsf.main(["--write", str(tmp_path)]) == 0
    assert vsf.main(["--check", str(tmp_path)]) == 0


def test_all_committed_scripts_are_canonical() -> None:
    root = Path(__file__).resolve().parents[1]
    assert vsf.main(["--check", str(root / "video_scripts")]) == 0
