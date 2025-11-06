"""Module entry-point to start the HTTP server."""

from __future__ import annotations

import argparse

import uvicorn

from .settings import get_settings


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Run the YouTube transcript HTTP server")
    parser.add_argument("--host", default=settings.http_host)
    parser.add_argument("--port", type=int, default=settings.http_port)
    args = parser.parse_args()

    uvicorn.run("tools.youtube_mcp.http_server:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":  # pragma: no cover
    main()
