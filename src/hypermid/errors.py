"""Hypermid SDK error types."""

from __future__ import annotations

from typing import Any, Dict, Optional


class HypermidError(Exception):
    """Raised when the Hypermid API returns an error response.

    Attributes:
        code: Machine-readable error code (e.g. ``"NO_ROUTE_FOUND"``).
        message: Human-readable error message.
        status: HTTP status code from the response.
        details: Optional structured details returned by the server.
        request_id: Server-side request identifier for support tickets.
    """

    def __init__(
        self,
        code: str,
        message: str,
        status: int,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.status = status
        self.details = details
        self.request_id = request_id


class HypermidTimeoutError(Exception):
    """Raised when a single API request times out."""

    def __init__(self, timeout_seconds: float) -> None:
        super().__init__(f"Request timed out after {timeout_seconds}s")
        self.timeout_seconds = timeout_seconds


class HypermidNetworkError(Exception):
    """Raised when a request fails for network / transport reasons."""

    def __init__(self, message: str, cause: Optional[BaseException] = None) -> None:
        super().__init__(message)
        self.cause = cause


class HypermidPollTimeoutError(Exception):
    """Raised when a poll-until helper exceeds its overall deadline."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
