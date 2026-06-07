"""The typed error hierarchy raised by the Skailar SDK.

Every failure surfaces as a subclass of :class:`SkailarError`, so a single
``except SkailarError`` covers the whole SDK. Transport/network failures become
:class:`SkailarConnectionError`; any non-2xx HTTP response becomes the most
specific :class:`SkailarAPIError` subclass for its status code.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "SkailarError",
    "SkailarAPIError",
    "SkailarAuthError",
    "SkailarBadRequestError",
    "SkailarNotFoundError",
    "SkailarRateLimitError",
    "SkailarUpstreamError",
    "SkailarConnectionError",
    "parse_error_body",
]


def parse_error_body(body: Any) -> tuple[str | None, str | None]:
    """Extract a ``(code, message)`` pair from an arbitrary parsed error body.

    Tolerant of three layouts: flat (``{"error": "code", "message": "msg"}``),
    nested object (``{"error": {"type"|"code", "message"}}``), and OpenAI-style
    (``{"error": {"code", "message"}}``).

    Args:
        body: The already-parsed response body (or ``None``).

    Returns:
        A ``(code, message)`` tuple, each element possibly ``None``.
    """
    if not isinstance(body, dict):
        return None, None
    err = body.get("error")

    if isinstance(err, str):
        message = body["message"] if isinstance(body.get("message"), str) else err
        return err, message

    if isinstance(err, dict):
        code = err["type"] if isinstance(err.get("type"), str) else (
            err["code"] if isinstance(err.get("code"), str) else None
        )
        message = err["message"] if isinstance(err.get("message"), str) else None
        return code, message

    top_message = body["message"] if isinstance(body.get("message"), str) else None
    return None, top_message


class SkailarError(Exception):
    """Base class for every error raised by the Skailar SDK.

    Not raised directly; serves as the common ``except`` target.

    Attributes:
        status: HTTP status code, or ``None`` for non-HTTP failures (e.g. network).
        code: Machine-readable error code from the body, if any.
        request_id: Correlation id from the ``x-request-id`` response header, if any.
        raw: The raw response body captured for debugging (parsed JSON or text).
    """

    status: int | None
    code: str | None
    request_id: str | None
    raw: Any

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        code: str | None = None,
        request_id: str | None = None,
        raw: Any = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.request_id = request_id
        self.raw = raw


class SkailarConnectionError(SkailarError):
    """The request never produced an HTTP response.

    Covers DNS failures, connection resets, TLS errors, and client-side timeouts.
    Its :attr:`status` is always ``None``. The originating ``httpx`` exception is
    available via ``__cause__``.
    """

    def __init__(self, message: str = "Failed to connect to the Skailar API") -> None:
        super().__init__(message)


class SkailarAPIError(SkailarError):
    """Base class for any non-2xx HTTP response from the gateway."""

    def __init__(
        self,
        message: str,
        *,
        status: int,
        code: str | None = None,
        request_id: str | None = None,
        raw: Any = None,
    ) -> None:
        super().__init__(message, status=status, code=code, request_id=request_id, raw=raw)

    @staticmethod
    def from_response(
        status: int,
        code: str | None,
        message: str | None,
        request_id: str | None,
        raw: Any,
        retry_after: int | None = None,
    ) -> SkailarAPIError:
        """Build the most specific :class:`SkailarAPIError` subclass for a status code.

        Args:
            status: The HTTP status code returned by the gateway.
            code: Machine-readable error code from the body, if any.
            message: Human-readable error message from the body, if any.
            request_id: The ``x-request-id`` header value, if present.
            raw: The raw response body for diagnostics.
            retry_after: Seconds from a ``Retry-After`` header, for 429 responses.

        Returns:
            A :class:`SkailarAuthError`, :class:`SkailarBadRequestError`,
            :class:`SkailarNotFoundError`, :class:`SkailarRateLimitError`,
            :class:`SkailarUpstreamError`, or a plain :class:`SkailarAPIError`.
        """
        kwargs: dict[str, Any] = {"code": code, "request_id": request_id, "raw": raw}
        if status == 401:
            return SkailarAuthError(message=message, **kwargs)
        if status == 400:
            return SkailarBadRequestError(message=message, **kwargs)
        if status == 404:
            return SkailarNotFoundError(message=message, **kwargs)
        if status == 429:
            return SkailarRateLimitError(message=message, retry_after=retry_after, **kwargs)
        if status >= 500:
            return SkailarUpstreamError(status, message=message, **kwargs)
        return SkailarAPIError(message or "API error", status=status, **kwargs)


class SkailarAuthError(SkailarAPIError):
    """HTTP 401 -- the API key is missing, malformed, or revoked."""

    def __init__(self, *, message: str | None = None, **kwargs: Any) -> None:
        super().__init__(message or "Invalid or missing API key", status=401, **kwargs)


class SkailarBadRequestError(SkailarAPIError):
    """HTTP 400 -- the request was malformed or failed validation."""

    def __init__(self, *, message: str | None = None, **kwargs: Any) -> None:
        super().__init__(message or "Bad request", status=400, **kwargs)


class SkailarNotFoundError(SkailarAPIError):
    """HTTP 404 -- the requested resource (e.g. a model id) does not exist."""

    def __init__(self, *, message: str | None = None, **kwargs: Any) -> None:
        super().__init__(message or "Resource not found", status=404, **kwargs)


class SkailarRateLimitError(SkailarAPIError):
    """HTTP 429 -- the account exceeded its rate limit.

    Attributes:
        retry_after: Seconds to wait before retrying, parsed from ``Retry-After``;
            ``None`` if the header was absent or unparseable.
    """

    retry_after: int | None

    def __init__(
        self, *, message: str | None = None, retry_after: int | None = None, **kwargs: Any
    ) -> None:
        super().__init__(message or "Rate limit exceeded", status=429, **kwargs)
        self.retry_after = retry_after


class SkailarUpstreamError(SkailarAPIError):
    """HTTP 5xx -- the upstream model provider failed or timed out.

    The gateway propagates provider 5xx failures (502/503/504) with a structured
    body. These are transient and are retried automatically for idempotent calls.
    """

    def __init__(self, status: int, *, message: str | None = None, **kwargs: Any) -> None:
        super().__init__(message or "Upstream provider error", status=status, **kwargs)
