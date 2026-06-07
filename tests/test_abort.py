"""Tests for cancellation and per-call option overrides.

The TypeScript SDK exposes ``AbortSignal`` and ``withOptions``; the Python SDK's
equivalents are per-call ``timeout`` overrides and closing a stream's underlying
connection via ``close()`` / the context manager.
"""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from skailar import Skailar
from tests.conftest import API_KEY, BASE_URL, sse_stream


def test_per_call_timeout_override_applied(client: Skailar, httpx_mock: HTTPXMock) -> None:
    captured: list[httpx.Timeout] = []

    def _callback(request: httpx.Request) -> httpx.Response:
        captured.append(request.extensions["timeout"])
        return httpx.Response(200, json={"status": "ok", "user_id": "u"})

    httpx_mock.add_callback(_callback)
    client.ping(timeout=5.0)
    assert captured[0]["read"] == 5.0


def test_client_level_timeout_used_by_default(httpx_mock: HTTPXMock) -> None:
    captured: list[dict[str, float | None]] = []

    def _callback(request: httpx.Request) -> httpx.Response:
        captured.append(request.extensions["timeout"])
        return httpx.Response(200, json={"status": "ok", "user_id": "u"})

    httpx_mock.add_callback(_callback)
    with Skailar(api_key=API_KEY, base_url=BASE_URL, timeout=12.0) as client:
        client.ping()
    assert captured[0]["read"] == 12.0


def test_stream_close_releases_connection(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        stream=httpx.ByteStream(sse_stream("a", "b", "c", "d")),
        headers={"content-type": "text/event-stream"},
    )
    stream = client.chat.completions.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "x"}],
        stream=True,
    )
    first = next(iter(stream))
    assert first.choices[0].delta.content == "a"
    stream.close()
    # Closing twice is a safe no-op.
    stream.close()


def test_with_context_manager_closes_client(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json={"status": "ok", "user_id": "u"})
    client = Skailar(api_key=API_KEY, base_url=BASE_URL)
    with client:
        client.ping()
    with pytest.raises(RuntimeError):
        client.ping()
