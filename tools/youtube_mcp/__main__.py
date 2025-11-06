"""Module entrypoint for running the HTTP server."""

from __future__ import annotations

import argparse

import uvicorn

from .settings import Settings


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube MCP HTTP server")
    parser.add_argument("--host", default=None, help="Bind host (overrides settings)")
    parser.add_argument("--port", type=int, default=None, help="Bind port (overrides settings)")
    args = parser.parse_args()

    settings = Settings.from_env()
    host = args.host or settings.http_host
    port = args.port or settings.http_port

    uvicorn.run("tools.youtube_mcp.http_server:app", host=host, port=port, reload=False)


if __name__ == "__main__":  # pragma: no cover
    main()
