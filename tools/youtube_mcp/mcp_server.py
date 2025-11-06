"""Minimal JSON-RPC server exposing MCP-compatible tools."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .errors import BaseYtMcpError, InvalidArgument
from .models import HealthResponse
from .settings import from_env
from .youtube_client import YouTubeTranscriptService

_SCHEMAS = {
    "youtube.get_transcript": Path(__file__).with_name("schemas") / "transcript.schema.json",
    "youtube.search_captions": Path(__file__).with_name("schemas") / "tracks.schema.json",
    "youtube.get_metadata": Path(__file__).with_name("schemas") / "metadata.schema.json",
}


class McpServer:
    """Simple stdio-based JSON-RPC server."""

    def __init__(self, service: YouTubeTranscriptService | None = None) -> None:
        self.service = service or YouTubeTranscriptService(settings=from_env())

    def _load_schema(self, name: str) -> dict[str, Any]:
        path = _SCHEMAS.get(name)
        if not path:
            return {}
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def list_tools(self) -> dict[str, Any]:
        def _entry(name: str, description: str) -> dict[str, Any]:
            schema = self._load_schema(name)
            return {
                "name": name,
                "description": description,
                "input_schema": schema.get("input", {}),
                "output_schema": schema.get("output", {}),
            }

        tools = [
            _entry(
                "youtube.get_transcript",
                "Fetch normalized transcript, segments, and chunks.",
            ),
            _entry(
                "youtube.search_captions",
                "List available caption tracks for a video.",
            ),
            _entry(
                "youtube.get_metadata",
                "Fetch lightweight video metadata.",
            ),
            {
                "name": "youtube.healthcheck",
                "description": "Service healthcheck.",
                "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
                "output_schema": {
                    "type": "object",
                    "required": ["ok", "version"],
                    "properties": {
                        "ok": {"type": "boolean"},
                        "version": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
        ]
        return {"tools": tools}

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if name == "youtube.get_transcript":
            url = arguments.get("url")
            if not isinstance(url, str):
                raise InvalidArgument("Parameter 'url' is required.")
            response = self.service.get_transcript(
                url,
                lang=arguments.get("lang"),
                prefer_auto=arguments.get("prefer_auto"),
            )
            return response.model_dump()
        if name == "youtube.search_captions":
            url = arguments.get("url")
            if not isinstance(url, str):
                raise InvalidArgument("Parameter 'url' is required.")
            tracks = self.service.list_tracks(url)
            return {"tracks": [track.model_dump() for track in tracks]}
        if name == "youtube.get_metadata":
            url = arguments.get("url")
            if not isinstance(url, str):
                raise InvalidArgument("Parameter 'url' is required.")
            metadata = self.service.get_metadata(url)
            return metadata.model_dump()
        if name == "youtube.healthcheck":
            return HealthResponse(ok=True, version=__version__).model_dump()
        raise ValueError(f"Unknown tool: {name}")

    def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        response: dict[str, Any] = {"jsonrpc": "2.0", "id": payload.get("id")}
        try:
            method = payload.get("method")
            if method == "tools.list":
                response["result"] = self.list_tools()
            elif method == "tools.call":
                params = payload.get("params", {})
                name = params.get("name")
                if not isinstance(name, str):
                    raise ValueError("Missing tool name")
                arguments = params.get("arguments", {}) or {}
                result = self.call_tool(name, arguments)
                response["result"] = result
            else:
                response["error"] = {
                    "code": "MethodNotFound",
                    "message": "Unknown method",
                }
        except BaseYtMcpError as exc:
            response["error"] = {"code": exc.code, "message": exc.message}
        except Exception as exc:  # pragma: no cover - defensive
            response["error"] = {"code": "InternalError", "message": str(exc)}
        return response

    def serve(self) -> None:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            response = self.handle(payload)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


def main() -> None:
    McpServer().serve()


if __name__ == "__main__":
    main()
