"""GitHub authentication helpers."""

from __future__ import annotations

import os
import pathlib
import os.path


def _read_token_file(var: str) -> str | None:
    path = os.getenv(var)
    if not path:
        return None
    try:
        expanded = os.path.expanduser(os.path.expandvars(path))
        return pathlib.Path(expanded).read_text()
    except OSError:
        return None


def get_github_token() -> str:
    """Return an API token from env vars or file paths.

    ``GH_TOKEN`` takes precedence, followed by ``GH_TOKEN_FILE``,
    ``GITHUB_TOKEN`` and ``GITHUB_TOKEN_FILE``. Leading/trailing whitespace is
    stripped and a blank token raises ``EnvironmentError``.
    """

    token = os.getenv("GH_TOKEN") or _read_token_file("GH_TOKEN_FILE")
    token = token or os.getenv("GITHUB_TOKEN") or _read_token_file("GITHUB_TOKEN_FILE")
    if token is None:
        raise EnvironmentError(
            "GH_TOKEN/GH_TOKEN_FILE or GITHUB_TOKEN/GITHUB_TOKEN_FILE must be set"
        )
    token = token.strip()
    if not token:
        raise EnvironmentError("GitHub token cannot be blank")
    return token
