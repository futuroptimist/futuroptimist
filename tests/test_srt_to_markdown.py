import json
import runpy
import random
import sys
import warnings

import src.srt_to_markdown as stm


def test_parse_and_convert(tmp_path):
    srt = """1
00:00:00,000 --> 00:00:01,000
Hello world.

2
00:00:01,500 --> 00:00:02,000
Another line.
"""
    srt_path = tmp_path / "video.srt"
    srt_path.write_text(srt)

    entries = stm.parse_srt(srt_path)
    assert entries == [
        ("00:00:00,000", "00:00:01,000", "Hello world."),
        ("00:00:01,500", "00:00:02,000", "Another line."),
    ]

    md = stm.to_markdown(entries, "Title", "XYZ")
    assert "# Title" in md
    assert "[NARRATOR]: Hello world." in md
    assert "00:00:00,000" in md


def test_unicode_and_italics(tmp_path):
    srt = """1
00:00:00,000 --> 00:00:02,000
<i>Hello 😊 &amp; welcome</i>
"""
    path = tmp_path / "unicode.srt"
    path.write_text(srt, encoding="utf-8")

    entries = stm.parse_srt(path)
    assert entries == [("00:00:00,000", "00:00:02,000", "*Hello 😊 & welcome*")]


def test_bold_tags(tmp_path):
    srt = """1
00:00:00,000 --> 00:00:01,000
<b>Bold</b> text
"""
    path = tmp_path / "bold.srt"
    path.write_text(srt)

    entries = stm.parse_srt(path)
    assert entries == [("00:00:00,000", "00:00:01,000", "**Bold** text")]


def test_uppercase_tags(tmp_path):
    srt = """1
00:00:00,000 --> 00:00:01,000
<I>Hello</I> <B>World</B>
"""
    path = tmp_path / "upper.srt"
    path.write_text(srt)

    entries = stm.parse_srt(path)
    assert entries == [("00:00:00,000", "00:00:01,000", "*Hello* **World**")]


def test_em_and_strong_tags(tmp_path):
    srt = """1
00:00:00,000 --> 00:00:01,000
<em>Hello</em> <strong>World</strong>
"""
    path = tmp_path / "emstrong.srt"
    path.write_text(srt)

    entries = stm.parse_srt(path)
    assert entries == [("00:00:00,000", "00:00:01,000", "*Hello* **World**")]


def test_line_break_tags(tmp_path):
    srt = """1
00:00:00,000 --> 00:00:01,000
Hello<br>world<br />again
"""
    path = tmp_path / "breaks.srt"
    path.write_text(srt)

    entries = stm.parse_srt(path)
    assert entries == [("00:00:00,000", "00:00:01,000", "Hello world again")]


def test_nbsp_entities(tmp_path):
    srt = """1
00:00:00,000 --> 00:00:01,000
Hello&nbsp;world
"""
    path = tmp_path / "nbsp.srt"
    path.write_text(srt)

    entries = stm.parse_srt(path)
    assert entries == [("00:00:00,000", "00:00:01,000", "Hello world")]


def test_strip_unknown_html_tags(tmp_path):
    srt = """1
00:00:00,000 --> 00:00:01,000
<u>Under</u> <font color='red'>color</font>
"""
    path = tmp_path / "unknown.srt"
    path.write_text(srt)

    entries = stm.parse_srt(path)
    assert entries == [("00:00:00,000", "00:00:01,000", "Under color")]


def test_tags_with_attributes(tmp_path):
    srt = """1
00:00:00,000 --> 00:00:01,000
<i class='x'>Hi</i> <b style="color:red">there</b>
"""
    path = tmp_path / "attr.srt"
    path.write_text(srt)

    entries = stm.parse_srt(path)
    assert entries == [("00:00:00,000", "00:00:01,000", "*Hi* **there**")]


def test_collapse_whitespace(tmp_path):
    srt = """1
00:00:00,000 --> 00:00:01,000
Hello<br>  <b>world</b>
"""
    path = tmp_path / "spaces.srt"
    path.write_text(srt)

    entries = stm.parse_srt(path)
    assert entries == [("00:00:00,000", "00:00:01,000", "Hello **world**")]


def test_strip_speaker_prefix(tmp_path):
    srt = """1
00:00:00,000 --> 00:00:01,000
- [Narrator] Hello world
"""
    path = tmp_path / "speaker.srt"
    path.write_text(srt)

    entries = stm.parse_srt(path)
    assert entries == [("00:00:00,000", "00:00:01,000", "Hello world")]


def test_skip_non_dialog_entries(tmp_path):
    srt = """1
00:00:00,000 --> 00:00:01,000
[Music]

2
00:00:01,500 --> 00:00:02,000
Real line
"""
    path = tmp_path / "non_dialog.srt"
    path.write_text(srt)

    entries = stm.parse_srt(path)
    assert entries == [("00:00:01,500", "00:00:02,000", "Real line")]


def test_skip_reversed_times_fuzz(tmp_path):
    random.seed(0)
    path = tmp_path / "bad.srt"
    for _ in range(10):
        start_ms = random.randint(500, 999)
        end_ms = random.randint(0, 499)
        srt = f"1\n00:00:00,{start_ms:03d} --> 00:00:00,{end_ms:03d}\nBad timing\n"
        path.write_text(srt)
        assert stm.parse_srt(path) == []


def test_parse_srt_edge_cases(tmp_path):
    content = """foo
1
badtime
skip

2
00:00:01,000 --> 00:00:02,000
bar

3"""
    p = tmp_path / "edge.srt"
    p.write_text(content)
    entries = stm.parse_srt(p)
    assert entries == [("00:00:01,000", "00:00:02,000", "bar")]


def test_parse_srt_without_index(tmp_path):
    srt = """00:00:00,000 --> 00:00:01,000
Hello

00:00:01,500 --> 00:00:02,000
World
"""
    p = tmp_path / "noindex.srt"
    p.write_text(srt)
    entries = stm.parse_srt(p)
    assert entries == [
        ("00:00:00,000", "00:00:01,000", "Hello"),
        ("00:00:01,500", "00:00:02,000", "World"),
    ]


def test_entrypoint(tmp_path, monkeypatch, capsys):
    srt_path = tmp_path / "in.srt"
    srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n")
    out = tmp_path / "out.md"
    monkeypatch.setattr(
        sys, "argv", ["srt_to_markdown.py", str(srt_path), "-o", str(out)]
    )
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=".*found in sys.modules.*",
            category=RuntimeWarning,
        )
        runpy.run_module("src.srt_to_markdown", run_name="__main__")
    assert out.exists()

    sys.modules.pop("__main__", None)
    monkeypatch.setattr(sys, "argv", ["srt_to_markdown.py", str(srt_path)])
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=".*found in sys.modules.*",
            category=RuntimeWarning,
        )
        runpy.run_module("src.srt_to_markdown", run_name="__main__")
    captured = capsys.readouterr()
    assert "[NARRATOR]: Hi" in captured.out


def test_to_markdown_splits_sentences():
    entries = [
        (
            "00:00:00,000",
            "00:00:05,000",
            "First sentence. Second sentence? Third sentence!",
        )
    ]
    md = stm.to_markdown(entries, "", "")
    narrator_lines = [
        line for line in md.splitlines() if line.startswith("[NARRATOR]: ")
    ]
    assert narrator_lines == [
        "[NARRATOR]: First sentence.  <!-- 00:00:00,000 -> 00:00:05,000 -->",
        "[NARRATOR]: Second sentence?  <!-- 00:00:00,000 -> 00:00:05,000 -->",
        "[NARRATOR]: Third sentence!  <!-- 00:00:00,000 -> 00:00:05,000 -->",
    ]


def test_to_markdown_handles_abbreviations():
    entries = [
        (
            "00:00:10,000",
            "00:00:15,000",
            "Dr. Smith arrives soon. Ready to roll.",
        )
    ]
    md = stm.to_markdown(entries, "", "")
    narrator_lines = [
        line for line in md.splitlines() if line.startswith("[NARRATOR]: ")
    ]
    assert narrator_lines == [
        "[NARRATOR]: Dr. Smith arrives soon.  <!-- 00:00:10,000 -> 00:00:15,000 -->",
        "[NARRATOR]: Ready to roll.  <!-- 00:00:10,000 -> 00:00:15,000 -->",
    ]


def test_parse_srt_invalid_utf8(tmp_path):
    data = b"1\n00:00:00,000 --> 00:00:01,000\nHi\x80\n"
    p = tmp_path / "bad.srt"
    p.write_bytes(data)
    entries = stm.parse_srt(p)
    assert entries == [("00:00:00,000", "00:00:01,000", "Hi�")]


def test_parse_srt_large_hour_values(tmp_path):
    srt = """1
100:00:00,000 --> 100:00:01,000
Hello
"""
    path = tmp_path / "long.srt"
    path.write_text(srt)
    entries = stm.parse_srt(path)
    assert entries == [("100:00:00,000", "100:00:01,000", "Hello")]


def test_parse_srt_hour_boundary(tmp_path):
    srt = """1
99:59:59,000 --> 100:00:00,000
Boundary
"""
    path = tmp_path / "boundary.srt"
    path.write_text(srt)
    entries = stm.parse_srt(path)
    assert entries == [("99:59:59,000", "100:00:00,000", "Boundary")]


def test_generate_script_for_slug(tmp_path):
    repo = tmp_path
    slug = "20250101_demo"
    slug_dir = repo / "video_scripts" / slug
    slug_dir.mkdir(parents=True)
    metadata = {"youtube_id": "abc123", "title": "Demo Title"}
    (slug_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    subs = repo / "subtitles"
    subs.mkdir()
    (subs / "abc123.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nHello world.\n")

    out_path, created = stm.generate_script_for_slug(slug, repo_root=repo)

    assert out_path == slug_dir / "script.md"
    assert created is True
    content = out_path.read_text()
    assert content.startswith("# Demo Title")
    assert "[NARRATOR]: Hello world." in content
    assert "`abc123`" in content


def test_generate_script_for_slug_no_overwrite_keeps_existing(tmp_path):
    repo = tmp_path
    slug = "20250102_demo"
    slug_dir = repo / "video_scripts" / slug
    slug_dir.mkdir(parents=True)
    metadata = {"youtube_id": "def456", "title": "Existing Script"}
    (slug_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    subs = repo / "subtitles"
    subs.mkdir()
    (subs / "def456.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nHello again.\n")
    existing = slug_dir / "script.md"
    existing.write_text("old content")

    out_path, created = stm.generate_script_for_slug(
        slug, repo_root=repo, overwrite=False
    )

    assert out_path == existing
    assert created is False
    assert existing.read_text() == "old content"


def test_main_slug_no_overwrite_skips_existing(tmp_path, capsys):
    repo = tmp_path
    slug = "20250103_demo"
    slug_dir = repo / "video_scripts" / slug
    slug_dir.mkdir(parents=True)
    metadata = {"youtube_id": "ghi789", "title": "CLI Skip"}
    (slug_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    subs = repo / "subtitles"
    subs.mkdir()
    (subs / "ghi789.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nHello CLI.\n")
    script_path = slug_dir / "script.md"
    script_path.write_text("keep me")

    stm.main(
        [
            "--slug",
            slug,
            "--repo-root",
            str(repo),
            "--no-overwrite",
        ]
    )

    captured = capsys.readouterr()
    assert "Skipped existing" in captured.out
    assert script_path.read_text() == "keep me"
