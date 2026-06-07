"""The :class:`Skailar` (sync) and :class:`AsyncSkailar` (async) clients.

Each owns an :mod:`httpx` client and a request loop that applies authentication,
per-attempt timeouts, retries with capped jittered backoff, and error mapping.
All pure helpers are inherited from :class:`skailar._base_client.BaseClient`.
"""

from __future__ import annotations

import asyncio
import time
from types import TracebackType
from typing import Any

import httpx

from ._base_client import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    BaseClient,
    FinalRequestOptions,
)
from ._exceptions import SkailarConnectionError
from ._streaming import AsyncStream, Stream
from ._types import Headers, Timeout
from ._utils import backoff_delay, cap_retry_delay
from .resources.audio import AsyncAudioResource, AudioResource
from .resources.chat import AsyncChatResource, ChatResource
from .resources.images import AsyncImagesResource, ImagesResource
from .resources.models import AsyncModelsResource, ModelsResource
from .resources.uploads import AsyncUploadsResource, UploadsResource
from .types.ping import PingKeyResponse

__all__ = ["Skailar", "AsyncSkailar"]

_CONNECTION_ERRORS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.ReadError,
    httpx.WriteError,
    httpx.RemoteProtocolError,
    httpx.NetworkError,
)


class Skailar(BaseClient):
    """The official synchronous Skailar API client.

    Construct once and reuse. Resource namespaces (:attr:`chat`, :attr:`models`,
    :attr:`images`, :attr:`audio`, :attr:`uploads`) provide the OpenAI-compatible
    and Skailar-native operations. Usable as a context manager so the underlying
    HTTP connection pool is closed on exit::

        with Skailar(api_key="skl_live_...") as client:
            res = client.chat.completions.create(
                model="claude-sonnet-4-6",
                messages=[{"role": "user", "content": "Hello!"}],
            )
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | httpx.URL | None = None,
        timeout: Timeout = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.Client | None = None,
        default_headers: Headers | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            api_key: Skailar key of the form ``skl_live_<43 url-safe base64 chars>``.
                Defaults to the ``SKAILAR_API_KEY`` environment variable.
            base_url: Gateway base URL without a trailing ``/v1`` (default
                ``https://api.skailar.com``). Point at ``http://localhost:8080``
                for a local gateway.
            timeout: Per-attempt timeout in seconds, or an :class:`httpx.Timeout`.
            max_retries: Maximum automatic retries for transient failures.
            http_client: An injected :class:`httpx.Client`, primarily for testing.
            default_headers: Headers merged into every request; ``Authorization``
                always wins and cannot be overridden.

        Raises:
            ValueError: If no API key is resolvable.
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )
        self._http = http_client or httpx.Client()
        self._owns_http = http_client is None

        self.chat = ChatResource(self)
        self.models = ModelsResource(self)
        self.images = ImagesResource(self)
        self.audio = AudioResource(self)
        self.uploads = UploadsResource(self)

    def ping(
        self, *, timeout: Timeout | None = None, headers: Headers | None = None
    ) -> PingKeyResponse:
        """Verify the configured API key against ``GET /v1/ping-key``.

        Args:
            timeout: Optional per-call timeout override.
            headers: Optional per-call extra headers.

        Returns:
            The ``{"status", "user_id"}`` payload when the key is valid.

        Raises:
            SkailarAuthError: If the key is missing, invalid or revoked.
        """
        data = self.request(
            FinalRequestOptions(
                method="GET",
                path="/v1/ping-key",
                expect="json",
                idempotent=True,
                timeout=timeout,
                headers=headers,
            )
        )
        return PingKeyResponse.from_dict(data)

    def request(self, options: FinalRequestOptions) -> Any:
        """Dispatch a request with retries and error mapping.

        Returns the parsed JSON (``expect="json"``), a :class:`Stream`
        (``expect="stream"``), or the open :class:`httpx.Response` for binary
        bodies (``expect="binary"``).
        """
        url = f"{self.base_url}{options.path}"
        headers = self._build_headers(options)
        is_stream = options.expect == "stream"
        keep_open = options.expect in ("stream", "binary")
        attempt = 0

        while True:
            request = self._http.build_request(
                options.method,
                url,
                json=options.body,
                headers=headers,
                timeout=self._request_timeout(options),
            )
            try:
                response = self._http.send(request, stream=keep_open)
            except _CONNECTION_ERRORS as exc:
                conn_err = SkailarConnectionError(_connection_message(exc))
                if options.idempotent and self._should_retry(attempt):
                    attempt += 1
                    time.sleep(backoff_delay(attempt))
                    continue
                raise conn_err from exc

            if response.is_success:
                if is_stream:
                    return Stream[Any](response)
                if options.expect == "binary":
                    return response
                response.read()
                return response.json()

            response.read()
            api_error = self._to_api_error(response, response.text)
            response.close()
            if self._is_retryable_status(response.status_code, options.idempotent) and (
                self._should_retry(attempt)
            ):
                attempt += 1
                delay = cap_retry_delay(self._retry_after_seconds(api_error))
                time.sleep(delay if delay is not None else backoff_delay(attempt))
                continue
            raise api_error

    def close(self) -> None:
        """Close the underlying HTTP client if the SDK created it."""
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> Skailar:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncSkailar(BaseClient):
    """The official asynchronous Skailar API client.

    Identical surface to :class:`Skailar`, backed by :class:`httpx.AsyncClient`.
    Usable as an async context manager::

        async with AsyncSkailar(api_key="skl_live_...") as client:
            res = await client.chat.completions.create(
                model="claude-sonnet-4-6",
                messages=[{"role": "user", "content": "Hello!"}],
            )
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | httpx.URL | None = None,
        timeout: Timeout = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.AsyncClient | None = None,
        default_headers: Headers | None = None,
    ) -> None:
        """Initialize the async client. See :class:`Skailar` for argument detail."""
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers,
        )
        self._http = http_client or httpx.AsyncClient()
        self._owns_http = http_client is None

        self.chat = AsyncChatResource(self)
        self.models = AsyncModelsResource(self)
        self.images = AsyncImagesResource(self)
        self.audio = AsyncAudioResource(self)
        self.uploads = AsyncUploadsResource(self)

    async def ping(
        self, *, timeout: Timeout | None = None, headers: Headers | None = None
    ) -> PingKeyResponse:
        """Verify the configured API key against ``GET /v1/ping-key``.

        Returns:
            The ``{"status", "user_id"}`` payload when the key is valid.

        Raises:
            SkailarAuthError: If the key is missing, invalid or revoked.
        """
        data = await self.request(
            FinalRequestOptions(
                method="GET",
                path="/v1/ping-key",
                expect="json",
                idempotent=True,
                timeout=timeout,
                headers=headers,
            )
        )
        return PingKeyResponse.from_dict(data)

    async def request(self, options: FinalRequestOptions) -> Any:
        """Async counterpart of :meth:`Skailar.request`."""
        url = f"{self.base_url}{options.path}"
        headers = self._build_headers(options)
        is_stream = options.expect == "stream"
        keep_open = options.expect in ("stream", "binary")
        attempt = 0

        while True:
            request = self._http.build_request(
                options.method,
                url,
                json=options.body,
                headers=headers,
                timeout=self._request_timeout(options),
            )
            try:
                response = await self._http.send(request, stream=keep_open)
            except _CONNECTION_ERRORS as exc:
                conn_err = SkailarConnectionError(_connection_message(exc))
                if options.idempotent and self._should_retry(attempt):
                    attempt += 1
                    await asyncio.sleep(backoff_delay(attempt))
                    continue
                raise conn_err from exc

            if response.is_success:
                if is_stream:
                    return AsyncStream[Any](response)
                if options.expect == "binary":
                    return response
                await response.aread()
                return response.json()

            await response.aread()
            api_error = self._to_api_error(response, response.text)
            await response.aclose()
            if self._is_retryable_status(response.status_code, options.idempotent) and (
                self._should_retry(attempt)
            ):
                attempt += 1
                delay = cap_retry_delay(self._retry_after_seconds(api_error))
                await asyncio.sleep(delay if delay is not None else backoff_delay(attempt))
                continue
            raise api_error

    async def close(self) -> None:
        """Close the underlying async HTTP client if the SDK created it."""
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> AsyncSkailar:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()


def _connection_message(exc: Exception) -> str:
    """Distinguish a timeout from a generic network failure for the error message."""
    if isinstance(exc, httpx.TimeoutException):
        return "Request timed out"
    return "Network request to the Skailar API failed"
