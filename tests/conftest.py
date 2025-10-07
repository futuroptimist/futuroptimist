import os
import pathlib
import pytest


@pytest.fixture(autouse=True, scope="session")
def force_utf8_path_text():
    orig_write = pathlib.Path.write_text
    orig_read = pathlib.Path.read_text

    def _write(
        self: pathlib.Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
    ):
        if encoding is None:
            encoding = "utf-8"
        return orig_write(self, data, encoding=encoding, errors=errors)  # type: ignore[arg-type]

    def _read(
        self: pathlib.Path, encoding: str | None = None, errors: str | None = None
    ):
        if encoding is None:
            encoding = "utf-8"
        return orig_read(self, encoding=encoding, errors=errors)  # type: ignore[arg-type]

    pathlib.Path.write_text = _write  # type: ignore[assignment]
    pathlib.Path.read_text = _read  # type: ignore[assignment]
    yield
    pathlib.Path.write_text = orig_write  # type: ignore[assignment]
    pathlib.Path.read_text = orig_read  # type: ignore[assignment]


_FALSEY = {"", "0", "false", "no", "off"}


def should_skip_e2e_from_env(value: str | None) -> bool:
    """Return True when environment value requests skipping e2e tests."""

    if value is None:
        return False
    token = value.strip().lower()
    if token in _FALSEY:
        return False
    return bool(token)


def pytest_runtest_setup(item):  # type: ignore[override]
    if should_skip_e2e_from_env(os.environ.get("SKIP_E2E")) and "e2e" in item.keywords:
        pytest.skip("SKIP_E2E set: skipping end-to-end tests")
