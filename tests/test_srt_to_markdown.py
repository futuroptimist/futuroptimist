import sys
import runpy
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


def test_entrypoint(tmp_path, monkeypatch, capsys):
    srt_path = tmp_path / "in.srt"
    srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n")
    out = tmp_path / "out.md"
    monkeypatch.setattr(
        sys, "argv", ["srt_to_markdown.py", str(srt_path), "-o", str(out)]
    )
    runpy.run_module("src.srt_to_markdown", run_name="__main__")
    assert out.exists()

    sys.modules.pop("__main__", None)
    monkeypatch.setattr(sys, "argv", ["srt_to_markdown.py", str(srt_path)])
    runpy.run_module("src.srt_to_markdown", run_name="__main__")
    captured = capsys.readouterr()
    assert "[NARRATOR]: Hi" in captured.out
