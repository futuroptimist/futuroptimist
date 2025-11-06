"""Minimal JSON-RPC server exposing the transcript service for MCP."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .errors import BaseYtMcpError
from .models import MetadataResponse, TracksResponse, write_schemas
from .youtube_client import YouTubeTranscriptService

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
write_schemas(SCHEMA_DIR)


class McpServer:
    """Implements ``tools.list`` and ``tools.call`` for JSON-RPC clients."""

    VERSION = "0.1.0"

    def __init__(self, service: YouTubeTranscriptService | None = None) -> None:
        self.service = service or YouTubeTranscriptService()
        self.schemas = {
            name: json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
            for name in [
                "transcript.schema.json",
                "tracks.schema.json",
                "metadata.schema.json",
            ]
        }

    def tools_list(self) -> dict[str, Any]:
        return {
            "tools": [
                {
                    "name": "youtube.get_transcript",
                    "description": "Fetch a YouTube transcript with chunking",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "lang": {"type": ["string", "null"]},
                            "prefer_auto": {"type": ["boolean", "null"]},
                        },
                        "required": ["url"],
                    },
                    "outputSchema": self.schemas["transcript.schema.json"],
                },
                {
                    "name": "youtube.search_captions",
                    "description": "List available caption tracks",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"url": {"type": "string"}},
                        "required": ["url"],
                    },
                    "outputSchema": self.schemas["tracks.schema.json"],
                },
                {
                    "name": "youtube.get_metadata",
                    "description": "Fetch basic video metadata",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"url": {"type": "string"}},
                        "required": ["url"],
                    },
                    "outputSchema": self.schemas["metadata.schema.json"],
                },
                {
                    "name": "youtube.healthcheck",
                    "description": "Check service availability",
                    "inputSchema": {"type": "object", "properties": {}},
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "ok": {"type": "boolean"},
                            "version": {"type": "string"},
                        },
                    },
                },
            ]
        }

    def tools_call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "youtube.get_transcript":
            result = self.service.get_transcript(
                url=arguments["url"],
                lang=arguments.get("lang"),
                prefer_auto=arguments.get("prefer_auto"),
            )
            return result.model_dump()
        if name == "youtube.search_captions":
            tracks = self.service.list_tracks(url=arguments["url"])
            return TracksResponse(tracks=tracks).model_dump()
        if name == "youtube.get_metadata":
            metadata = self.service.get_metadata(url=arguments["url"])
            return MetadataResponse.model_validate(metadata.model_dump()).model_dump()
        if name == "youtube.healthcheck":
            return {"ok": True, "version": self.VERSION}
        raise ValueError(f"Unknown tool: {name}")

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        req_id = request.get("id")
        method = request.get("method")
        try:
            if method == "tools.list":
                result = self.tools_list()
                return {"jsonrpc": "2.0", "id": req_id, "result": result}
            if method == "tools.call":
                params = request.get("params") or {}
                name = params.get("name")
                arguments = params.get("arguments", {})
                result = self.tools_call(name, arguments)
                return {"jsonrpc": "2.0", "id": req_id, "result": result}
            raise ValueError("Unknown method")
        except BaseYtMcpError as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32000,
                    "message": exc.message,
                    "data": exc.to_dict(),
                },
            }
        except Exception as exc:  # pragma: no cover - defensive
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(exc)},
            }


def main() -> None:  # pragma: no cover - exercised via tests
    server = McpServer()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            }
        else:
            response = server.handle_request(request)
        print(json.dumps(response))
        sys.stdout.flush()


if __name__ == "__main__":  # pragma: no cover
    main()
