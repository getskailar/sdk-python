"""A dependency-free SSE parser and the sync/async chat-completion stream wrappers.

The stream wrappers expose an SSE response as an iterable of decoded
:class:`ChatCompletionChunk` objects, support early ``close()``, and work as
context managers (sync ``with`` / async ``async with``).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from types import TracebackType
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

import httpx

from ._exceptions import SkailarAPIError, SkailarConnectionError, parse_error_body

if TYPE_CHECKING:
    from .types.chat import ChatCompletionChunk

__all__ = ["Stream", "AsyncStream", "SSELineBuffer"]

_T = TypeVar("_T")


class SSELineBuffer:
    """Incremental buffer that splits raw SSE text into complete lines.

    Recognizes all three SSE line terminators (``\\n``, ``\\r\\n``, ``\\r``). A
    partial line, or a trailing lone ``\\r`` that might be the start of a
    ``\\r\\n`` split across reads, is retained until the next feed resolves it.
    """

    def __init__(self) -> None:
        self._buffer = ""

    def feed(self, text: str) -> list[str]:
        """Append decoded text and return every newly-completed line.

        Args:
            text: The decoded chunk to append to the buffer.

        Returns:
            The complete lines now available, in order, without terminators.
        """
        self._buffer += text
        lines: list[str] = []
        while True:
            line = self._next_line()
            if line is None:
                break
            lines.append(line)
        return lines

    def flush(self) -> str | None:
        """Return any trailing buffered line at end-of-stream.

        Returns:
            The remaining buffered text with trailing newlines stripped, or
            ``None`` if the buffer is empty.
        """
        tail = self._buffer.rstrip("\r\n")
        self._buffer = ""
        return tail or None

    def _next_line(self) -> str | None:
        index = -1
        for j, char in enumerate(self._buffer):
            if char in ("\n", "\r"):
                index = j
                break
        if index == -1:
            return None
        line = self._buffer[:index]
        if self._buffer[index] == "\r":
            if index == len(self._buffer) - 1:
                return None  # maybe `\r\n` split across reads
            skip = 2 if self._buffer[index + 1] == "\n" else 1
            self._buffer = self._buffer[index + skip:]
        else:
            self._buffer = self._buffer[index + 1:]
        return line


def _data_payload(line: str) -> str | None:
    """Extract the ``data:`` payload from one SSE line, or ``None`` to skip it."""
    if line == "" or line.startswith(":"):
        return None
    if not line.startswith("data:"):
        return None
    return line[5:].lstrip()


def _decode_chunk(data: str) -> ChatCompletionChunk:
    """Parse one SSE ``data:`` payload into a chunk, raising on in-band errors.

    Raises:
        SkailarConnectionError: If the payload is not valid JSON.
        SkailarAPIError: If the payload carries the gateway's in-band ``error`` field.
    """
    try:
        parsed: Any = json.loads(data)
    except json.JSONDecodeError as exc:
        raise SkailarConnectionError(
            f"Malformed streaming event (not JSON): {data[:200]}"
        ) from exc
    if isinstance(parsed, dict) and "error" in parsed:
        code, message = parse_error_body(parsed)
        raise SkailarAPIError.from_response(
            500, code, message or "Streaming error", None, parsed
        )
    from .types.chat import ChatCompletionChunk

    return ChatCompletionChunk.from_dict(parsed)


class Stream(Generic[_T]):
    """A synchronous, closeable iterable of :class:`ChatCompletionChunk` values.

    Returned by ``chat.completions.create(..., stream=True)``. Iterate it with a
    ``for`` loop; each iteration yields one decoded chunk. Use it as a context
    manager so the underlying connection is always released::

        with client.chat.completions.create(..., stream=True) as stream:
            for chunk in stream:
                ...
    """

    def __init__(self, response: httpx.Response) -> None:
        self._response = response
        self._buffer = SSELineBuffer()
        self._closed = False
        self._iterator = self._iterate()

    def __iter__(self) -> Stream[_T]:
        return self

    def __next__(self) -> _T:
        return cast("_T", next(self._iterator))

    def _iterate(self) -> Iterator[ChatCompletionChunk]:
        try:
            for text in self._response.iter_text():
                for line in self._buffer.feed(text):
                    payload = _data_payload(line)
                    if payload is None:
                        continue
                    if payload == "[DONE]":
                        return
                    yield _decode_chunk(payload)
            tail = self._buffer.flush()
            if tail is not None:
                payload = _data_payload(tail)
                if payload is not None and payload != "[DONE]":
                    yield _decode_chunk(payload)
        except httpx.HTTPError as exc:
            raise SkailarConnectionError("Stream read failed") from exc
        finally:
            self.close()

    def close(self) -> None:
        """Close the underlying connection, tearing down an in-flight stream."""
        if self._closed:
            return
        self._closed = True
        self._response.close()

    def __enter__(self) -> Stream[_T]:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncStream(Generic[_T]):
    """An asynchronous, closeable async-iterable of :class:`ChatCompletionChunk`.

    Returned by ``async_client.chat.completions.create(..., stream=True)``.
    Iterate with ``async for``; use ``async with`` so the connection is released::

        async with await client.chat.completions.create(..., stream=True) as stream:
            async for chunk in stream:
                ...
    """

    def __init__(self, response: httpx.Response) -> None:
        self._response = response
        self._buffer = SSELineBuffer()
        self._closed = False
        self._iterator = self._iterate()

    def __aiter__(self) -> AsyncStream[_T]:
        return self

    async def __anext__(self) -> _T:
        return cast("_T", await self._iterator.__anext__())

    async def _iterate(self) -> AsyncIterator[ChatCompletionChunk]:
        try:
            async for text in self._response.aiter_text():
                for line in self._buffer.feed(text):
                    payload = _data_payload(line)
                    if payload is None:
                        continue
                    if payload == "[DONE]":
                        return
                    yield _decode_chunk(payload)
            tail = self._buffer.flush()
            if tail is not None:
                payload = _data_payload(tail)
                if payload is not None and payload != "[DONE]":
                    yield _decode_chunk(payload)
        except httpx.HTTPError as exc:
            raise SkailarConnectionError("Stream read failed") from exc
        finally:
            await self.close()

    async def close(self) -> None:
        """Close the underlying connection, tearing down an in-flight stream."""
        if self._closed:
            return
        self._closed = True
        await self._response.aclose()

    async def __aenter__(self) -> AsyncStream[_T]:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()
