import pytest

import tests.conftest as conf


class DummyItem:
    def __init__(self, keywords):
        self.keywords = keywords


def test_should_skip_e2e_truthy_values(monkeypatch):
    for value in ["1", "true", "YES", "on", " 1 "]:
        assert conf.should_skip_e2e_from_env(value) is True


def test_should_skip_e2e_falsey_values(monkeypatch):
    for value in [None, "", "0", "false", "no", "off", " \t "]:
        assert conf.should_skip_e2e_from_env(value) is False


def test_pytest_runtest_setup_skips_e2e_when_flag(monkeypatch):
    monkeypatch.setenv("SKIP_E2E", "1")
    item = DummyItem({"e2e": True})
    with pytest.raises(pytest.skip.Exception):
        conf.pytest_runtest_setup(item)


def test_pytest_runtest_setup_no_skip_without_marker(monkeypatch):
    monkeypatch.delenv("SKIP_E2E", raising=False)
    item = DummyItem({})
    # Should not raise
    conf.pytest_runtest_setup(item)


def test_pytest_runtest_setup_allows_other_tests(monkeypatch):
    monkeypatch.setenv("SKIP_E2E", "0")
    item = DummyItem({"unit": True})
    conf.pytest_runtest_setup(item)
