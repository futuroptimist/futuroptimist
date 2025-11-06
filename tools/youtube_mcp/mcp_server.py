"""Minimal JSON-RPC server exposing MCP-compatible tools."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .errors import BaseYtMcpError, InvalidArgument
from .models import HealthResponse, MetadataRequest, TracksRequest, TranscriptRequest
from .settings import Settings
from .utils import ensure_utf8
from .youtube_client import YouTubeTranscriptService

_SCHEMAS = {
    "youtube.get_transcript": Path(__file__).parent
    / "schemas"
    / "transcript.schema.json",
    "youtube.search_captions": Path(__file__).parent / "schemas" / "tracks.schema.json",
    "youtube.get_metadata": Path(__file__).parent / "schemas" / "metadata.schema.json",
    "youtube.healthcheck": Path(__file__).parent / "schemas" / "health.schema.json",
}


class MCPServer:
    """Simple stdio JSON-RPC dispatcher for the MCP protocol."""

    def __init__(self, service: YouTubeTranscriptService) -> None:
        self.service = service
        self.tools = self._load_tool_definitions()

    def _load_tool_definitions(self) -> dict[str, dict[str, Any]]:
        definitions: dict[str, dict[str, Any]] = {}
        for name, path in _SCHEMAS.items():
            with path.open("r", encoding="utf-8") as handle:
                schema = json.load(handle)
            definitions[name] = schema
        return definitions

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        method = request.get("method")
        request_id = request.get("id")

        if method == "tools.list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": name,
                            "description": schema.get("description", ""),
                            "inputSchema": schema.get("input"),
                            "outputSchema": schema.get("output"),
                        }
                        for name, schema in self.tools.items()
                    ],
                },
            }

        if method == "tools.call":
            params = request.get("params", {})
            name = params.get("name")
            arguments = params.get("arguments", {})
            try:
                result = self._call_tool(name, arguments)
            except BaseYtMcpError as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32000,
                        "message": exc.message,
                        "data": exc.to_dict(),
                    },
                }
            return {"jsonrpc": "2.0", "id": request_id, "result": result}

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}",
            },
        }

    def _call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "youtube.get_transcript":
            transcript_request = TranscriptRequest(**arguments)
            response = self.service.get_transcript(
                transcript_request.url,
                lang=transcript_request.lang,
                prefer_auto=transcript_request.prefer_auto,
            )
            payload: dict[str, Any] = response.model_dump()
            return payload
        if name == "youtube.search_captions":
            tracks_request = TracksRequest(**arguments)
            tracks_payload: dict[str, Any] = self.service.search_captions(
                tracks_request.url
            ).model_dump()
            return tracks_payload
        if name == "youtube.get_metadata":
            metadata_request = MetadataRequest(**arguments)
            metadata_payload: dict[str, Any] = self.service.get_metadata(
                metadata_request.url
            ).model_dump()
            return metadata_payload
        if name == "youtube.healthcheck":
            health_payload: dict[str, Any] = HealthResponse(
                ok=True, version="0.1.0"
            ).model_dump()
            return health_payload
        raise InvalidArgument(f"Unknown tool: {name}")

    def serve_forever(self) -> None:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Invalid JSON: {exc}",
                    },
                }
            else:
                response = self.handle_request(payload)
            sys.stdout.write(ensure_utf8(json.dumps(response)) + "\n")
            sys.stdout.flush()


def main() -> None:  # pragma: no cover - exercised manually
    settings = Settings.from_env()
    service = YouTubeTranscriptService(settings=settings)
    server = MCPServer(service)
    server.serve_forever()


if __name__ == "__main__":  # pragma: no cover
    main()
