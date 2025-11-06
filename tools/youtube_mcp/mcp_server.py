"""Minimal JSON-RPC server exposing MCP compatible tools."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from . import __version__
from .cache import Cache
from .errors import BaseYtMcpError, InvalidArgument
from .models import MetadataRequest, TracksRequest, TranscriptRequest
from .settings import Settings
from .youtube_client import YouTubeTranscriptService

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"


def _load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / name
    data = json.loads(path.read_text())
    if not isinstance(data, dict):  # pragma: no cover - schema integrity check
        raise ValueError(f"Schema {name} is not a JSON object")
    return cast(dict[str, Any], data)


settings = Settings.from_env()
cache = Cache(settings.cache_dir / "transcripts.sqlite3", settings.cache_ttl_days)
service = YouTubeTranscriptService(settings, cache)

TOOL_REGISTRY: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
TOOL_DESCRIPTIONS = {
    "youtube.get_transcript": "Fetch and chunk a transcript for RAG",
    "youtube.search_captions": "List available caption tracks",
    "youtube.get_metadata": "Fetch lightweight metadata",
    "youtube.healthcheck": "Service health probe",
}
SCHEMAS: dict[str, dict[str, Any]] = {
    "youtube.get_transcript": _load_schema("transcript.schema.json"),
    "youtube.search_captions": _load_schema("tracks.schema.json"),
    "youtube.get_metadata": _load_schema("metadata.schema.json"),
    "youtube.healthcheck": {"type": "object", "properties": {}, "additionalProperties": False},
}


def tool(name: str) -> Callable[[Callable[[dict[str, Any]], dict[str, Any]]], Callable[[dict[str, Any]], dict[str, Any]]]:
    def decorator(func: Callable[[dict[str, Any]], dict[str, Any]]) -> Callable[[dict[str, Any]], dict[str, Any]]:
        TOOL_REGISTRY[name] = func
        return func

    return decorator


@tool("youtube.get_transcript")
def _call_get_transcript(arguments: dict[str, Any]) -> dict[str, Any]:
    request = TranscriptRequest.model_validate(arguments)
    response = service.get_transcript(request.url, lang=request.lang, prefer_auto=request.prefer_auto)
    return response.model_dump()


@tool("youtube.search_captions")
def _call_tracks(arguments: dict[str, Any]) -> dict[str, Any]:
    request = TracksRequest.model_validate(arguments)
    tracks = service.list_tracks(request.url)
    return {"tracks": [track.model_dump() for track in tracks]}


@tool("youtube.get_metadata")
def _call_metadata(arguments: dict[str, Any]) -> dict[str, Any]:
    request = MetadataRequest.model_validate(arguments)
    metadata = service.get_metadata(request.url)
    return metadata.model_dump()


@tool("youtube.healthcheck")
def _call_health(arguments: dict[str, Any]) -> dict[str, Any]:
    if arguments:
        raise InvalidArgument("Healthcheck does not accept arguments")
    return {"ok": True, "version": __version__}


def _handle_request(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("jsonrpc") != "2.0":
        raise InvalidArgument("Invalid jsonrpc version")
    method = payload.get("method")
    request_id = payload.get("id")

    try:
        result: dict[str, Any]
        if method == "tools.list":
            tools_payload: list[dict[str, Any]] = []
            for name in TOOL_REGISTRY:
                tools_payload.append(
                    {
                        "name": name,
                        "description": TOOL_DESCRIPTIONS[name],
                        "inputSchema": {"schema": SCHEMAS[name]},
                    }
                )
            result = {"tools": tools_payload}
        elif method == "tools.call":
            params = payload.get("params") or {}
            raw_name = params.get("name")
            if not isinstance(raw_name, str):
                raise InvalidArgument("Missing tool name")
            tool_name = raw_name
            if tool_name not in TOOL_REGISTRY:
                raise InvalidArgument(f"Unknown tool {tool_name}")
            arguments = params.get("arguments") or {}
            result = {"content": TOOL_REGISTRY[tool_name](arguments)}
        else:
            raise InvalidArgument(f"Unknown method {method}")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except BaseYtMcpError as exc:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": exc.message, "data": exc.to_dict()},
        }
    except Exception as exc:  # pragma: no cover - unexpected failure  # noqa: BLE001
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32603, "message": "Internal error", "data": {"reason": str(exc)}},
        }


def serve() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            }
        else:
            response = _handle_request(payload)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":  # pragma: no cover
    serve()
