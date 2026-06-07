"""Shared pytest fixtures and helpers for the SDK test suite.

All HTTP traffic is intercepted by ``pytest-httpx`` so tests never touch the
network. The default base URL is a sentinel host that only resolves through the
mock.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest

from skailar import AsyncSkailar, Skailar

BASE_URL = "http://test.local"
API_KEY = "skl_live_test_key"


@pytest.fixture
def client() -> Iterator[Skailar]:
    """A synchronous client pointed at the mocked base URL."""
    with Skailar(api_key=API_KEY, base_url=BASE_URL, max_retries=2) as instance:
        yield instance


@pytest.fixture
async def async_client() -> AsyncIterator[AsyncSkailar]:
    """An asynchronous client pointed at the mocked base URL."""
    async with AsyncSkailar(api_key=API_KEY, base_url=BASE_URL, max_retries=2) as instance:
        yield instance


def chat_completion_payload(content: str = "Hello there!") -> dict[str, object]:
    """A minimal well-formed ``ChatCompletion`` JSON body."""
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 1,
        "model": "claude-sonnet-4-6",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
    }


def sse_stream(*contents: str, line_ending: str = "\n") -> bytes:
    """Build an SSE chat-completion stream body ending with ``[DONE]``.

    Args:
        contents: One content fragment per chunk.
        line_ending: The line terminator to use (to exercise ``\\n``/``\\r\\n``/``\\r``).

    Returns:
        The encoded SSE byte payload.
    """
    import json

    events: list[str] = []
    for fragment in contents:
        chunk = {
            "id": "chatcmpl-1",
            "object": "chat.completion.chunk",
            "created": 1,
            "model": "claude-sonnet-4-6",
            "choices": [{"index": 0, "delta": {"content": fragment}, "finish_reason": None}],
        }
        events.append(f"data: {json.dumps(chunk)}")
    events.append("data: [DONE]")
    return (line_ending.join(events) + line_ending).encode("utf-8")
