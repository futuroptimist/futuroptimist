"""Custom error hierarchy for the YouTube MCP service."""
from __future__ import annotations

from http import HTTPStatus


class BaseYtMcpError(Exception):
    """Base class for domain-specific errors."""

    code: str = "InternalError"
    http_status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def as_dict(self) -> dict[str, str]:
        """Serialize the error for JSON responses."""

        return {"code": self.code, "message": self.message}


class InvalidArgument(BaseYtMcpError):
    code = "InvalidArgument"
    http_status = HTTPStatus.BAD_REQUEST


class VideoUnavailable(BaseYtMcpError):
    code = "VideoUnavailable"
    http_status = HTTPStatus.NOT_FOUND


class NoCaptionsAvailable(BaseYtMcpError):
    code = "NoCaptionsAvailable"
    http_status = HTTPStatus.NOT_FOUND


class PolicyRejected(BaseYtMcpError):
    code = "PolicyRejected"
    http_status = HTTPStatus.FORBIDDEN


class NetworkError(BaseYtMcpError):
    code = "NetworkError"
    http_status = HTTPStatus.BAD_GATEWAY


class RateLimited(BaseYtMcpError):
    code = "RateLimited"
    http_status = HTTPStatus.TOO_MANY_REQUESTS
