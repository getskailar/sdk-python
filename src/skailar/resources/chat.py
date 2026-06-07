"""The chat resource: ``client.chat.completions.create(...)``.

Mirrors ``openai``'s chat completions call shape, including streaming via a
``stream=True`` flag that returns a :class:`Stream` / :class:`AsyncStream`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Literal, overload

from .._base_client import FinalRequestOptions
from .._streaming import AsyncStream, Stream
from .._types import NOT_GIVEN, Headers, NotGiven, Timeout
from .._utils import strip_not_given
from ..types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ModelId,
    ReasoningEffort,
    ResponseFormat,
    Tool,
    ToolChoice,
)

if TYPE_CHECKING:
    from .._client import AsyncSkailar, Skailar

__all__ = [
    "ChatCompletions",
    "ChatResource",
    "AsyncChatCompletions",
    "AsyncChatResource",
]

_PATH = "/v1/chat/completions"


def _build_body(
    *,
    model: ModelId,
    messages: Iterable[ChatCompletionMessageParam],
    stream: bool,
    max_tokens: int | NotGiven,
    temperature: float | NotGiven,
    top_p: float | NotGiven,
    reasoning_effort: ReasoningEffort | NotGiven,
    tools: Iterable[Tool] | NotGiven,
    tool_choice: ToolChoice | NotGiven,
    response_format: ResponseFormat | NotGiven,
    n: int | NotGiven,
    presence_penalty: float | NotGiven,
    frequency_penalty: float | NotGiven,
    logit_bias: dict[str, float] | NotGiven,
    user: str | NotGiven,
    seed: int | NotGiven,
    stop: str | list[str] | NotGiven,
) -> dict[str, object]:
    """Assemble the wire request body, dropping every unsupplied parameter."""
    return strip_not_given(
        {
            "model": model,
            "messages": list(messages),
            "stream": stream,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "reasoning_effort": reasoning_effort,
            "tools": list(tools) if not isinstance(tools, NotGiven) else tools,
            "tool_choice": tool_choice,
            "response_format": response_format,
            "n": n,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "logit_bias": logit_bias,
            "user": user,
            "seed": seed,
            "stop": stop,
        }
    )


class ChatCompletions:
    """The ``completions`` sub-namespace of the synchronous chat resource."""

    def __init__(self, client: Skailar) -> None:
        self._client = client

    @overload
    def create(
        self,
        *,
        model: ModelId,
        messages: Iterable[ChatCompletionMessageParam],
        stream: Literal[False] | NotGiven = ...,
        max_tokens: int | NotGiven = ...,
        temperature: float | NotGiven = ...,
        top_p: float | NotGiven = ...,
        reasoning_effort: ReasoningEffort | NotGiven = ...,
        tools: Iterable[Tool] | NotGiven = ...,
        tool_choice: ToolChoice | NotGiven = ...,
        response_format: ResponseFormat | NotGiven = ...,
        n: int | NotGiven = ...,
        presence_penalty: float | NotGiven = ...,
        frequency_penalty: float | NotGiven = ...,
        logit_bias: dict[str, float] | NotGiven = ...,
        user: str | NotGiven = ...,
        seed: int | NotGiven = ...,
        stop: str | list[str] | NotGiven = ...,
        timeout: Timeout | None = ...,
        headers: Headers | None = ...,
    ) -> ChatCompletion: ...

    @overload
    def create(
        self,
        *,
        model: ModelId,
        messages: Iterable[ChatCompletionMessageParam],
        stream: Literal[True],
        max_tokens: int | NotGiven = ...,
        temperature: float | NotGiven = ...,
        top_p: float | NotGiven = ...,
        reasoning_effort: ReasoningEffort | NotGiven = ...,
        tools: Iterable[Tool] | NotGiven = ...,
        tool_choice: ToolChoice | NotGiven = ...,
        response_format: ResponseFormat | NotGiven = ...,
        n: int | NotGiven = ...,
        presence_penalty: float | NotGiven = ...,
        frequency_penalty: float | NotGiven = ...,
        logit_bias: dict[str, float] | NotGiven = ...,
        user: str | NotGiven = ...,
        seed: int | NotGiven = ...,
        stop: str | list[str] | NotGiven = ...,
        timeout: Timeout | None = ...,
        headers: Headers | None = ...,
    ) -> Stream[ChatCompletionChunk]: ...

    def create(
        self,
        *,
        model: ModelId,
        messages: Iterable[ChatCompletionMessageParam],
        stream: bool | NotGiven = NOT_GIVEN,
        max_tokens: int | NotGiven = NOT_GIVEN,
        temperature: float | NotGiven = NOT_GIVEN,
        top_p: float | NotGiven = NOT_GIVEN,
        reasoning_effort: ReasoningEffort | NotGiven = NOT_GIVEN,
        tools: Iterable[Tool] | NotGiven = NOT_GIVEN,
        tool_choice: ToolChoice | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        n: int | NotGiven = NOT_GIVEN,
        presence_penalty: float | NotGiven = NOT_GIVEN,
        frequency_penalty: float | NotGiven = NOT_GIVEN,
        logit_bias: dict[str, float] | NotGiven = NOT_GIVEN,
        user: str | NotGiven = NOT_GIVEN,
        seed: int | NotGiven = NOT_GIVEN,
        stop: str | list[str] | NotGiven = NOT_GIVEN,
        timeout: Timeout | None = None,
        headers: Headers | None = None,
    ) -> ChatCompletion | Stream[ChatCompletionChunk]:
        """Create a chat completion, buffered or streamed.

        Args:
            model: Model identifier or alias to route the request to.
            messages: The ordered conversation history.
            stream: When ``True``, returns a :class:`Stream` of chunks instead of
                a buffered :class:`ChatCompletion`.
            max_tokens: Hard cap on tokens generated.
            temperature: Sampling temperature in ``[0, 2]``.
            top_p: Nucleus sampling probability mass in ``[0, 1]``.
            reasoning_effort: Reasoning budget for reasoning-capable models.
            tools: Function-calling tool definitions the model may call.
            tool_choice: Constraint on whether/which tools may be called.
            response_format: Requested output structure.
            n: Number of independent completions to generate.
            presence_penalty: Penalty in ``[-2, 2]`` discouraging repeated topics.
            frequency_penalty: Penalty in ``[-2, 2]`` discouraging repeated tokens.
            logit_bias: Per-token logit bias map keyed by token id.
            user: Opaque stable end-user identifier for abuse monitoring.
            seed: Seed for best-effort deterministic sampling.
            stop: One or more stop sequences that halt generation.
            timeout: Optional per-call timeout override.
            headers: Optional per-call extra headers.

        Returns:
            A :class:`ChatCompletion`, or a :class:`Stream` of
            :class:`ChatCompletionChunk` when ``stream=True``.

        Raises:
            SkailarBadRequestError: On HTTP 400 (malformed request).
            SkailarAuthError: On HTTP 401 (bad key).
            SkailarRateLimitError: On HTTP 429 (after exhausting retries).
            SkailarUpstreamError: On HTTP 5xx (after exhausting retries).
            SkailarConnectionError: On network failure or timeout.
        """
        is_stream = stream is True
        body = _build_body(
            model=model,
            messages=messages,
            stream=is_stream,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            reasoning_effort=reasoning_effort,
            tools=tools,
            tool_choice=tool_choice,
            response_format=response_format,
            n=n,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
            user=user,
            seed=seed,
            stop=stop,
        )
        options = FinalRequestOptions(
            method="POST",
            path=_PATH,
            expect="stream" if is_stream else "json",
            body=body,
            idempotent=True,
            timeout=timeout,
            headers=headers,
        )
        if is_stream:
            stream_obj: Stream[ChatCompletionChunk] = self._client.request(options)
            return stream_obj
        return ChatCompletion.from_dict(self._client.request(options))


class ChatResource:
    """The synchronous chat resource root, mirroring ``openai``'s ``client.chat``."""

    def __init__(self, client: Skailar) -> None:
        self.completions = ChatCompletions(client)


class AsyncChatCompletions:
    """The ``completions`` sub-namespace of the asynchronous chat resource."""

    def __init__(self, client: AsyncSkailar) -> None:
        self._client = client

    @overload
    async def create(
        self,
        *,
        model: ModelId,
        messages: Iterable[ChatCompletionMessageParam],
        stream: Literal[False] | NotGiven = ...,
        max_tokens: int | NotGiven = ...,
        temperature: float | NotGiven = ...,
        top_p: float | NotGiven = ...,
        reasoning_effort: ReasoningEffort | NotGiven = ...,
        tools: Iterable[Tool] | NotGiven = ...,
        tool_choice: ToolChoice | NotGiven = ...,
        response_format: ResponseFormat | NotGiven = ...,
        n: int | NotGiven = ...,
        presence_penalty: float | NotGiven = ...,
        frequency_penalty: float | NotGiven = ...,
        logit_bias: dict[str, float] | NotGiven = ...,
        user: str | NotGiven = ...,
        seed: int | NotGiven = ...,
        stop: str | list[str] | NotGiven = ...,
        timeout: Timeout | None = ...,
        headers: Headers | None = ...,
    ) -> ChatCompletion: ...

    @overload
    async def create(
        self,
        *,
        model: ModelId,
        messages: Iterable[ChatCompletionMessageParam],
        stream: Literal[True],
        max_tokens: int | NotGiven = ...,
        temperature: float | NotGiven = ...,
        top_p: float | NotGiven = ...,
        reasoning_effort: ReasoningEffort | NotGiven = ...,
        tools: Iterable[Tool] | NotGiven = ...,
        tool_choice: ToolChoice | NotGiven = ...,
        response_format: ResponseFormat | NotGiven = ...,
        n: int | NotGiven = ...,
        presence_penalty: float | NotGiven = ...,
        frequency_penalty: float | NotGiven = ...,
        logit_bias: dict[str, float] | NotGiven = ...,
        user: str | NotGiven = ...,
        seed: int | NotGiven = ...,
        stop: str | list[str] | NotGiven = ...,
        timeout: Timeout | None = ...,
        headers: Headers | None = ...,
    ) -> AsyncStream[ChatCompletionChunk]: ...

    async def create(
        self,
        *,
        model: ModelId,
        messages: Iterable[ChatCompletionMessageParam],
        stream: bool | NotGiven = NOT_GIVEN,
        max_tokens: int | NotGiven = NOT_GIVEN,
        temperature: float | NotGiven = NOT_GIVEN,
        top_p: float | NotGiven = NOT_GIVEN,
        reasoning_effort: ReasoningEffort | NotGiven = NOT_GIVEN,
        tools: Iterable[Tool] | NotGiven = NOT_GIVEN,
        tool_choice: ToolChoice | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        n: int | NotGiven = NOT_GIVEN,
        presence_penalty: float | NotGiven = NOT_GIVEN,
        frequency_penalty: float | NotGiven = NOT_GIVEN,
        logit_bias: dict[str, float] | NotGiven = NOT_GIVEN,
        user: str | NotGiven = NOT_GIVEN,
        seed: int | NotGiven = NOT_GIVEN,
        stop: str | list[str] | NotGiven = NOT_GIVEN,
        timeout: Timeout | None = None,
        headers: Headers | None = None,
    ) -> ChatCompletion | AsyncStream[ChatCompletionChunk]:
        """Async counterpart of :meth:`ChatCompletions.create`."""
        is_stream = stream is True
        body = _build_body(
            model=model,
            messages=messages,
            stream=is_stream,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            reasoning_effort=reasoning_effort,
            tools=tools,
            tool_choice=tool_choice,
            response_format=response_format,
            n=n,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
            user=user,
            seed=seed,
            stop=stop,
        )
        options = FinalRequestOptions(
            method="POST",
            path=_PATH,
            expect="stream" if is_stream else "json",
            body=body,
            idempotent=True,
            timeout=timeout,
            headers=headers,
        )
        if is_stream:
            stream_obj: AsyncStream[ChatCompletionChunk] = await self._client.request(options)
            return stream_obj
        return ChatCompletion.from_dict(await self._client.request(options))


class AsyncChatResource:
    """The asynchronous chat resource root."""

    def __init__(self, client: AsyncSkailar) -> None:
        self.completions = AsyncChatCompletions(client)
