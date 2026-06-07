"""Shared transport logic for the sync and async clients.

:class:`BaseClient` holds the pure, side-effect-free pieces both clients share:
configuration resolution, header assembly with non-overridable auth, error
mapping, and retry decisions. The concrete clients in :mod:`skailar._client`
own the actual request loops (which differ only in ``await``/``sleep``).
"""

from __future__ import annotations

import os
from email.utils import parsedate_to_datetime
from typing import Any, Literal

import httpx

from ._exceptions import (
    SkailarAPIError,
    SkailarRateLimitError,
    parse_error_body,
)
from ._types import Headers, Timeout

__all__ = ["BaseClient", "FinalRequestOptions"]

DEFAULT_BASE_URL = "https://api.skailar.com"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2

Expect = Literal["json", "stream", "binary"]
Method = Literal["GET", "POST"]


class FinalRequestOptions:
    """A fully-resolved description of one HTTP request to dispatch."""

    def __init__(
        self,
        *,
        method: Method,
        path: str,
        expect: Expect,
        body: dict[str, Any] | None = None,
        idempotent: bool = False,
        timeout: Timeout | None = None,
        headers: Headers | None = None,
    ) -> None:
        self.method = method
        self.path = path
        self.expect = expect
        self.body = body
        self.idempotent = idempotent
        self.timeout = timeout
        self.headers = headers


class BaseClient:
    """Configuration and pure transport helpers shared by both clients."""

    api_key: str
    base_url: str
    timeout: Timeout
    max_retries: int
    default_headers: Headers

    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str | httpx.URL | None,
        timeout: Timeout,
        max_retries: int,
        default_headers: Headers | None,
    ) -> None:
        resolved_key = api_key if api_key is not None else os.environ.get("SKAILAR_API_KEY")
        if not resolved_key:
            raise ValueError(
                "Missing Skailar API key. Pass api_key=... or set the "
                "SKAILAR_API_KEY environment variable."
            )
        self.api_key = resolved_key
        self.base_url = str(base_url or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_headers = default_headers or {}

    def _build_headers(self, options: FinalRequestOptions) -> Headers:
        """Assemble the outgoing header set, with ``Authorization`` always last.

        Precedence (later wins): client ``default_headers`` -> the SDK's default
        ``Accept`` and ``Content-Type`` -> per-call headers -> ``Authorization``.
        The bearer token is applied last and any caller-supplied authorization
        header (in any casing) is dropped first, so it can never be overridden or
        leaked. ``Accept``/``Content-Type`` remain overridable on purpose (e.g.
        audio speech sends ``Accept: audio/mpeg``).

        Args:
            options: The request being dispatched.

        Returns:
            The header mapping to send.
        """
        headers: Headers = dict(self.default_headers)
        headers["Accept"] = (
            "text/event-stream" if options.expect == "stream" else "application/json"
        )
        if options.body is not None:
            headers["Content-Type"] = "application/json"
        if options.headers:
            headers.update(options.headers)
        for key in list(headers):
            if key.lower() == "authorization":
                del headers[key]
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request_timeout(self, options: FinalRequestOptions) -> Timeout:
        return options.timeout if options.timeout is not None else self.timeout

    def _to_api_error(self, response: httpx.Response, raw_text: str) -> SkailarAPIError:
        """Map a non-2xx response into the most specific API error subclass.

        Args:
            response: The failed HTTP response.
            raw_text: The already-read response body text.

        Returns:
            The mapped :class:`SkailarAPIError`.
        """
        raw: Any = raw_text
        if raw_text:
            try:
                raw = response.json()
            except ValueError:
                raw = raw_text
        else:
            raw = None
        code, message = parse_error_body(raw)
        request_id = self._extract_request_id(response.headers)
        retry_after = (
            self._parse_retry_after(response.headers.get("retry-after"))
            if response.status_code == 429
            else None
        )
        return SkailarAPIError.from_response(
            response.status_code, code, message, request_id, raw, retry_after
        )

    @staticmethod
    def _extract_request_id(headers: httpx.Headers) -> str | None:
        for name in ("x-request-id", "x-skailar-request-id", "request-id"):
            value: str | None = headers.get(name)
            if value:
                return value
        return None

    @staticmethod
    def _parse_retry_after(header: str | None) -> int | None:
        """Parse a ``Retry-After`` header (seconds or HTTP-date) into seconds."""
        if not header:
            return None
        try:
            return max(0, int(float(header)))
        except ValueError:
            pass
        try:
            from datetime import datetime, timezone

            when = parsedate_to_datetime(header)
            delta = (when - datetime.now(timezone.utc)).total_seconds()
            return max(0, int(delta))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _is_retryable_status(status: int, idempotent: bool) -> bool:
        """Whether an HTTP error status is eligible for automatic retry.

        A ``429`` is always retryable (rejected before execution). A ``5xx`` may
        mean the request already executed server-side, so it is retried only when
        the caller marked the request idempotent.
        """
        if status == 429:
            return True
        return status >= 500 and idempotent

    def _should_retry(self, attempt: int) -> bool:
        return attempt < self.max_retries

    def _retry_after_seconds(self, error: SkailarAPIError) -> int | None:
        if isinstance(error, SkailarRateLimitError):
            return error.retry_after
        return None
