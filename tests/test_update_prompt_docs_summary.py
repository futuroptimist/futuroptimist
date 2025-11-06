import io
import sys

import scripts.update_prompt_docs_summary as upd


class DummyResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_extract_related_links():
    text = (
        "## Related prompt guides\n\n"
        "- [Item](/docs/prompts-items)\n"
        "- [Docs](/docs/prompts-docs#section)\n\n"
        "## Next"
    )
    links = upd.extract_related_links(text)
    assert links == ["/docs/prompts-items", "/docs/prompts-docs#section"]


def test_fetch_remote_titles(monkeypatch):
    prompts_text = "## Related prompt guides\n\n- [Item](items.md#foo)\n"
    item_text = "---\ntitle: Item\n---\n# Item"

    def fake_urlopen(url):
        if (
            url
            == "https://raw.githubusercontent.com/foo/bar/main/docs/prompts/codex/automation.md"
        ):
            return DummyResp(prompts_text.encode())
        if (
            url
            == "https://raw.githubusercontent.com/foo/bar/main/docs/prompts/codex/items.md"
        ):
            return DummyResp(item_text.encode())
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(upd.urllib.request, "urlopen", fake_urlopen)
    rows = upd.fetch_remote_titles(
        "https://github.com/foo/bar/blob/main/docs/prompts/codex/automation.md"
    )
    assert rows == [
        (
            "bar/items.md#foo",
            "https://github.com/foo/bar/blob/main/docs/prompts/codex/items.md#foo",
            "Item",
        )
    ]


def test_main_generates_summary_with_remote(tmp_path, monkeypatch):
    prompts_text = "## Related prompt guides\n\n- [Item](items.md#foo)\n"
    item_text = "---\ntitle: Item\n---\n# Item"

    def fake_urlopen(url):
        if (
            url
            == "https://raw.githubusercontent.com/foo/bar/main/docs/prompts/codex/automation.md"
        ):
            return DummyResp(prompts_text.encode())
        if (
            url
            == "https://raw.githubusercontent.com/foo/bar/main/docs/prompts/codex/items.md"
        ):
            return DummyResp(item_text.encode())
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(upd.urllib.request, "urlopen", fake_urlopen)
    out = tmp_path / "summary.md"
    repos = tmp_path / "repos.txt"
    repos.write_text("foo/bar\n")
    argv = [
        "update_prompt_docs_summary.py",
        "--repos-from",
        str(repos),
        "--out",
        str(out),
        "--external-prompts-codex",
        "https://github.com/foo/bar/blob/main/docs/prompts/codex/automation.md",
    ]
    monkeypatch.setattr(sys, "argv", argv)
    upd.main()
    text = out.read_text()
    assert "bar/docs/prompts/codex/automation.md" in text
    assert "bar/items.md#foo" in text


def test_main_handles_multiple_external_codex(tmp_path, monkeypatch):
    prompts_text = "## Related prompt guides\n\n- [Item](items.md)\n"
    item_text = "---\ntitle: Item\n---\n# Item"

    raw_base = "https://raw.githubusercontent.com"
    mapping = {
        f"{raw_base}/foo/bar/main/docs/prompts/codex/automation.md": prompts_text,
        f"{raw_base}/foo/bar/main/docs/prompts/codex/items.md": item_text,
        f"{raw_base}/foo/baz/main/docs/prompts/codex/automation.md": prompts_text,
        f"{raw_base}/foo/baz/main/docs/prompts/codex/items.md": item_text,
    }

    def fake_urlopen(url):
        if url in mapping:
            return DummyResp(mapping[url].encode())
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(upd.urllib.request, "urlopen", fake_urlopen)
    out = tmp_path / "summary.md"
    repos = tmp_path / "repos.txt"
    repos.write_text("foo/bar\nfoo/baz\n")
    argv = [
        "update_prompt_docs_summary.py",
        "--repos-from",
        str(repos),
        "--out",
        str(out),
        "--external-prompts-codex",
        "https://github.com/foo/bar/blob/main/docs/prompts/codex/automation.md",
        "--external-prompts-codex",
        "https://github.com/foo/baz/blob/main/docs/prompts/codex/automation.md",
    ]
    monkeypatch.setattr(sys, "argv", argv)
    upd.main()
    text = out.read_text()
    assert "bar/docs/prompts/codex/automation.md" in text
    assert "baz/docs/prompts/codex/automation.md" in text
    assert "bar/items.md" in text
    assert "baz/items.md" in text


def test_main_uses_repos_from_file(tmp_path, monkeypatch):
    prompts_text = "## Related prompt guides\n\n- [Item](items.md)\n"
    item_text = "---\ntitle: Item\n---\n# Item"

    raw_base = "https://raw.githubusercontent.com"
    mapping = {
        f"{raw_base}/foo/bar/main/docs/prompts/codex/automation.md": prompts_text,
        f"{raw_base}/foo/bar/main/docs/prompts/codex/items.md": item_text,
    }

    def fake_urlopen(url):
        if url in mapping:
            return DummyResp(mapping[url].encode())
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(upd.urllib.request, "urlopen", fake_urlopen)
    out = tmp_path / "summary.md"
    repos = tmp_path / "repos.txt"
    repos.write_text("foo/bar\n")
    argv = [
        "update_prompt_docs_summary.py",
        "--repos-from",
        str(repos),
        "--out",
        str(out),
    ]
    monkeypatch.setattr(sys, "argv", argv)
    upd.main()
    text = out.read_text()
    assert "bar/docs/prompts/codex/automation.md" in text
    assert "bar/items.md" in text
