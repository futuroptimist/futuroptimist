"""HTTP utilities."""

from __future__ import annotations

import urllib.request
from urllib.parse import urlparse


def urlopen_http(url_or_req: urllib.request.Request | str):
    """Open ``url_or_req`` if scheme is http or https.

    Raises
    ------
    ValueError
        If the scheme is not http/https.
    """
    if isinstance(url_or_req, urllib.request.Request):
        url = url_or_req.full_url
    else:
        url = url_or_req
    if urlparse(url).scheme not in {"http", "https"}:
        raise ValueError("Only http and https URLs are allowed")
    return urllib.request.urlopen(url_or_req)  # nosec B310
