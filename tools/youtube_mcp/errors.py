"""Custom exceptions used by the YouTube MCP service."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass(slots=True)
class BaseYtMcpError(Exception):
    """Base error that carries a machine readable code and message."""

    code: str
    message: str
    details: Mapping[str, Any] | None = None
    http_status: ClassVar[int] = 400

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            payload["details"] = dict(self.details)
        return payload


class InvalidArgument(BaseYtMcpError):  # noqa: N818
    http_status = 422

    def __init__(self, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(code="InvalidArgument", message=message, details=details)


class VideoUnavailable(BaseYtMcpError):  # noqa: N818
    http_status = 404

    def __init__(self, message: str = "Video is unavailable") -> None:
        super().__init__(code="VideoUnavailable", message=message)


class NoCaptionsAvailable(BaseYtMcpError):  # noqa: N818
    http_status = 404

    def __init__(self, message: str = "No captions are available for this video") -> None:
        super().__init__(code="NoCaptionsAvailable", message=message)


class PolicyRejected(BaseYtMcpError):  # noqa: N818
    http_status = 403

    def __init__(self, message: str = "Video is private or unlisted and cannot be fetched") -> None:
        super().__init__(code="PolicyRejected", message=message)


class NetworkError(BaseYtMcpError):
    http_status = 503

    def __init__(self, message: str = "Network request failed", *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(code="NetworkError", message=message, details=details)


class RateLimited(BaseYtMcpError):  # noqa: N818
    http_status = 429

    def __init__(self, message: str = "Rate limited by upstream service") -> None:
        super().__init__(code="RateLimited", message=message)


ERROR_BY_CODE: dict[str, type[BaseYtMcpError]] = {
    "InvalidArgument": InvalidArgument,
    "VideoUnavailable": VideoUnavailable,
    "NoCaptionsAvailable": NoCaptionsAvailable,
    "PolicyRejected": PolicyRejected,
    "NetworkError": NetworkError,
    "RateLimited": RateLimited,
}
