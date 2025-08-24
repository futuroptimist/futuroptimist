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
    prompts_text = "## Related prompt guides\n\n- [Item](/docs/prompts-items)\n"
    item_text = "---\ntitle: Item\n---\n# Item"

    def fake_urlopen(url):
        if url.endswith("prompts-codex.md"):
            return DummyResp(prompts_text.encode())
        if url.endswith("prompts-items.md"):
            return DummyResp(item_text.encode())
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(upd.urllib.request, "urlopen", fake_urlopen)
    rows = upd.fetch_remote_titles("https://example.com/prompts-codex.md")
    assert rows == [
        (
            "dspace/prompts-items.md",
            (
                "https://github.com/democratizedspace/dspace/blob/v3/frontend/src/pages/docs/md/"
                "prompts-items.md"
            ),
            "Item",
        )
    ]


def test_main_generates_summary_with_remote(tmp_path, monkeypatch):
    prompts_text = "## Related prompt guides\n\n- [Item](/docs/prompts-items)\n"
    item_text = "---\ntitle: Item\n---\n# Item"

    def fake_urlopen(url):
        if url.endswith("prompts-codex.md"):
            return DummyResp(prompts_text.encode())
        if url.endswith("prompts-items.md"):
            return DummyResp(item_text.encode())
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(upd.urllib.request, "urlopen", fake_urlopen)
    out = tmp_path / "summary.md"
    argv = [
        "update_prompt_docs_summary.py",
        "--repos-from",
        "dict/prompt-doc-repos.txt",
        "--out",
        str(out),
        "--external-prompts-codex",
        "https://example.com/prompts-codex.md",
    ]
    monkeypatch.setattr(sys, "argv", argv)
    upd.main()
    text = out.read_text()
    assert "dspace/prompts-items.md" in text
