"""Custom exception hierarchy for the YouTube transcript tooling."""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import Any


@dataclass
class BaseYtMcpError(Exception):
    """Base class for typed errors surfaced to clients."""

    code: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable representation."""

        return {"code": self.code, "message": self.message}

    def http_status(self) -> HTTPStatus:
        """Map the error to an HTTP status code."""

        return ERROR_STATUS_MAP.get(type(self), HTTPStatus.INTERNAL_SERVER_ERROR)


class VideoUnavailable(BaseYtMcpError):  # noqa: N818
    pass


class NoCaptionsAvailable(BaseYtMcpError):  # noqa: N818
    pass


class PolicyRejected(BaseYtMcpError):  # noqa: N818
    pass


class NetworkError(BaseYtMcpError):
    pass


class RateLimited(BaseYtMcpError):  # noqa: N818
    pass


class InvalidArgument(BaseYtMcpError):  # noqa: N818
    pass


ERROR_STATUS_MAP: dict[type[BaseYtMcpError], HTTPStatus] = {
    InvalidArgument: HTTPStatus.BAD_REQUEST,
    PolicyRejected: HTTPStatus.FORBIDDEN,
    RateLimited: HTTPStatus.TOO_MANY_REQUESTS,
    NoCaptionsAvailable: HTTPStatus.NOT_FOUND,
    VideoUnavailable: HTTPStatus.NOT_FOUND,
    NetworkError: HTTPStatus.BAD_GATEWAY,
}


def as_error(exc: Exception) -> BaseYtMcpError:
    """Normalise arbitrary exceptions into the service error hierarchy."""

    if isinstance(exc, BaseYtMcpError):
        return exc
    return BaseYtMcpError("InternalError", str(exc))


__all__ = [
    "ERROR_STATUS_MAP",
    "BaseYtMcpError",
    "InvalidArgument",
    "NetworkError",
    "NoCaptionsAvailable",
    "PolicyRejected",
    "RateLimited",
    "VideoUnavailable",
    "as_error",
]
