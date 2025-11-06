"""HTTP entrypoint when running ``python -m tools.youtube_mcp``."""
from __future__ import annotations

import argparse

import uvicorn

from .http_server import create_app
from .settings import from_env


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the YouTube transcript HTTP server")
    parser.add_argument("--host", default=None, help="Bind host (default from settings)")
    parser.add_argument("--port", type=int, default=None, help="Port (default from settings)")
    args = parser.parse_args(argv)

    settings = from_env()
    host = args.host or settings.http_host
    port = args.port or settings.http_port

    app = create_app()
    uvicorn.run(app, host=host, port=port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
