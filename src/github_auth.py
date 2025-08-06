"""GitHub authentication helpers."""

from __future__ import annotations

import os


def get_github_token() -> str:
    """Return an API token from ``GH_TOKEN`` or ``GITHUB_TOKEN`` env vars.

    Leading and trailing whitespace is stripped to avoid accidental newline
    characters; a blank token raises ``EnvironmentError``.
    """
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token is None:
        raise EnvironmentError("GH_TOKEN or GITHUB_TOKEN must be set")
    token = token.strip()
    if not token:
        raise EnvironmentError("GitHub token cannot be blank")
    return token
