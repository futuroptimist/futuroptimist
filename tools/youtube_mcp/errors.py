"""Custom exceptions for the YouTube transcript service."""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import Any


@dataclass
class BaseYtMcpError(Exception):
    """Base error carrying a structured error code and HTTP status."""

    code: str
    message: str
    http_status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message}


class InvalidArgument(BaseYtMcpError):  # noqa: N818
    def __init__(self, message: str):
        super().__init__("InvalidArgument", message, HTTPStatus.BAD_REQUEST)


class VideoUnavailable(BaseYtMcpError):  # noqa: N818
    def __init__(self, message: str = "Video is unavailable"):
        super().__init__("VideoUnavailable", message, HTTPStatus.NOT_FOUND)


class NoCaptionsAvailable(BaseYtMcpError):  # noqa: N818
    def __init__(self, message: str = "No captions available for this video"):
        super().__init__("NoCaptionsAvailable", message, HTTPStatus.NOT_FOUND)


class PolicyRejected(BaseYtMcpError):  # noqa: N818
    def __init__(self, message: str = "Request rejected by policy"):
        super().__init__("PolicyRejected", message, HTTPStatus.FORBIDDEN)


class NetworkError(BaseYtMcpError):
    def __init__(self, message: str = "Network error while contacting YouTube"):
        super().__init__("NetworkError", message, HTTPStatus.SERVICE_UNAVAILABLE)


class RateLimited(BaseYtMcpError):  # noqa: N818
    def __init__(self, message: str = "Rate limited by upstream service"):
        super().__init__("RateLimited", message, HTTPStatus.TOO_MANY_REQUESTS)
