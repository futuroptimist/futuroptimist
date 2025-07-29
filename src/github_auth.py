"""GitHub authentication helpers."""

from __future__ import annotations

import os


def get_github_token() -> str:
    """Return an API token from ``GH_TOKEN`` or ``GITHUB_TOKEN`` env vars."""
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token is None:
        raise EnvironmentError("GH_TOKEN or GITHUB_TOKEN must be set")
    return token
