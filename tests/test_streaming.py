"""Tests for SSE streaming: sync, async, line-ending tolerance and early close."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from skailar import AsyncSkailar, Skailar
from skailar._streaming import SSELineBuffer
from tests.conftest import sse_stream


def test_stream_sync(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        stream=__import__("httpx").ByteStream(sse_stream("Hello", " ", "world")),
        headers={"content-type": "text/event-stream"},
    )
    out = ""
    with client.chat.completions.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "hi"}],
        stream=True,
    ) as stream:
        for chunk in stream:
            out += chunk.choices[0].delta.content or ""
    assert out == "Hello world"


async def test_stream_async(async_client: AsyncSkailar, httpx_mock: HTTPXMock) -> None:
    import httpx

    httpx_mock.add_response(
        stream=httpx.ByteStream(sse_stream("a", "b", "c")),
        headers={"content-type": "text/event-stream"},
    )
    out = ""
    async with await async_client.chat.completions.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "hi"}],
        stream=True,
    ) as stream:
        async for chunk in stream:
            out += chunk.choices[0].delta.content or ""
    assert out == "abc"


@pytest.mark.parametrize("line_ending", ["\n", "\r\n", "\r"])
def test_stream_line_endings(
    client: Skailar, httpx_mock: HTTPXMock, line_ending: str
) -> None:
    import httpx

    httpx_mock.add_response(
        stream=httpx.ByteStream(sse_stream("x", "y", line_ending=line_ending)),
        headers={"content-type": "text/event-stream"},
    )
    out = ""
    with client.chat.completions.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "hi"}],
        stream=True,
    ) as stream:
        for chunk in stream:
            out += chunk.choices[0].delta.content or ""
    assert out == "xy"


def test_stream_early_close_sync(client: Skailar, httpx_mock: HTTPXMock) -> None:
    import httpx

    httpx_mock.add_response(
        stream=httpx.ByteStream(sse_stream("1", "2", "3", "4", "5")),
        headers={"content-type": "text/event-stream"},
    )
    collected: list[str] = []
    stream = client.chat.completions.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "count"}],
        stream=True,
    )
    for chunk in stream:
        collected.append(chunk.choices[0].delta.content or "")
        if len(collected) == 2:
            break
    stream.close()
    assert collected == ["1", "2"]


async def test_stream_early_break_async(
    async_client: AsyncSkailar, httpx_mock: HTTPXMock
) -> None:
    import httpx

    httpx_mock.add_response(
        stream=httpx.ByteStream(sse_stream("1", "2", "3", "4")),
        headers={"content-type": "text/event-stream"},
    )
    collected: list[str] = []
    async with await async_client.chat.completions.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "count"}],
        stream=True,
    ) as stream:
        async for chunk in stream:
            collected.append(chunk.choices[0].delta.content or "")
            if len(collected) == 1:
                break
    assert collected == ["1"]


def test_sse_line_buffer_split_crlf() -> None:
    buffer = SSELineBuffer()
    assert buffer.feed("data: a\r") == []
    assert buffer.feed("\ndata: b\n") == ["data: a", "data: b"]


def test_sse_line_buffer_mixed() -> None:
    buffer = SSELineBuffer()
    assert buffer.feed("one\rtwo\nthree\r\n") == ["one", "two", "three"]
