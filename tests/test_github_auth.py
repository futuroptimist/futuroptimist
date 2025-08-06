import pytest

from src.github_auth import get_github_token


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
