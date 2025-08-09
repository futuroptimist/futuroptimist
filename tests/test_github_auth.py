import pytest

from src.github_auth import get_github_token


@pytest.fixture(autouse=True)
def clear_token_file_env(monkeypatch):
    monkeypatch.delenv("GH_TOKEN_FILE", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN_FILE", raising=False)


def test_get_token_prefers_gh_token(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "a")
    monkeypatch.setenv("GITHUB_TOKEN", "b")
    assert get_github_token() == "a"


def test_get_token_falls_back(monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "b")
    assert get_github_token() == "b"


def test_get_token_missing(monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(EnvironmentError):
        get_github_token()


def test_get_token_strips_whitespace(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", " a\n")
    assert get_github_token() == "a"


def test_get_token_rejects_blank(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "  \n\t")
    with pytest.raises(EnvironmentError):
        get_github_token()


def test_get_token_from_file(monkeypatch, tmp_path):
    token_file = tmp_path / "token.txt"
    token_file.write_text("filetoken\n")
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GH_TOKEN_FILE", str(token_file))
    assert get_github_token() == "filetoken"


def test_file_precedence_over_github_token(monkeypatch, tmp_path):
    token_file = tmp_path / "token.txt"
    token_file.write_text("filetoken")
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setenv("GH_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("GITHUB_TOKEN", "envtoken")
    assert get_github_token() == "filetoken"


def test_github_token_file_fallback(monkeypatch, tmp_path):
    token_file = tmp_path / "token.txt"
    token_file.write_text("filetoken")
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN_FILE", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN_FILE", str(token_file))
    assert get_github_token() == "filetoken"
