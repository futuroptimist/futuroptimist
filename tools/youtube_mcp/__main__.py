"""Module entrypoint for running the HTTP server."""

from __future__ import annotations

import argparse

import uvicorn

from .settings import Settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the YouTube MCP HTTP server")
    parser.add_argument("--host", default=None, help="Host address")
    parser.add_argument("--port", type=int, default=None, help="Port number")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    host = args.host or settings.http_host
    port = args.port or settings.http_port

    uvicorn.run("tools.youtube_mcp.http_server:app", host=host, port=port, reload=False)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
