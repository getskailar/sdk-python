"""Types for the chat completions resource (``POST /v1/chat/completions``).

Request bodies are :class:`TypedDict` shapes modelled on the OpenAI wire format,
so the SDK is a drop-in replacement for ``openai`` for these calls. Response
objects are frozen dataclasses built from the parsed JSON.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

from typing_extensions import Required, TypedDict

from .shared import Usage

__all__ = [
    "KNOWN_MODELS",
    "KnownModelId",
    "ModelId",
    "ChatRole",
    "TextContentPart",
    "ImageURL",
    "ImageContentPart",
    "ContentPart",
    "ChatCompletionMessageParam",
    "ToolFunctionParam",
    "ToolParam",
    "Tool",
    "ToolChoice",
    "ResponseFormat",
    "ReasoningEffort",
    "FinishReason",
    "ToolCall",
    "ChatCompletionMessage",
    "Choice",
    "ChatCompletion",
    "ChoiceDelta",
    "ChunkChoice",
    "ChatCompletionChunk",
]

KNOWN_MODELS: tuple[str, ...] = (
    "epoch-mini",
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-sonnet-4-6",
    "claude-opus-4-6",
    "claude-haiku-4-5",
    "claude-sonnet-4-5",
    "o3",
    "o4-mini",
    "gpt-5",
    "gpt-5-mini",
    "gpt-5.1",
    "gpt-5.4",
    "gpt-5.4-nano",
    "gpt-5.4-mini",
    "gpt-5.5",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
    "gemini-3.5-flash",
    "deepseek-v4-flash",
    "deepseek-v4-pro",
    "grok-4.20-non-reasoning",
    "grok-4.20-reasoning",
    "grok-4.3",
    "grok-build-0.1",
    "gpt-image-1",
)
"""Identifiers of models known when this SDK was cut, used for editor autocomplete.

The authoritative, always-current catalog is ``GET /v1/models``; new models work
immediately without an SDK upgrade.
"""

KnownModelId = Literal[
    "epoch-mini",
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-sonnet-4-6",
    "claude-opus-4-6",
    "claude-haiku-4-5",
    "claude-sonnet-4-5",
    "o3",
    "o4-mini",
    "gpt-5",
    "gpt-5-mini",
    "gpt-5.1",
    "gpt-5.4",
    "gpt-5.4-nano",
    "gpt-5.4-mini",
    "gpt-5.5",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
    "gemini-3.5-flash",
    "deepseek-v4-flash",
    "deepseek-v4-pro",
    "grok-4.20-non-reasoning",
    "grok-4.20-reasoning",
    "grok-4.3",
    "grok-build-0.1",
    "gpt-image-1",
]

ModelId: TypeAlias = "KnownModelId | str"
"""A model identifier: any known id (with autocomplete) or any other string.

Python collapses ``Literal[...] | str`` to ``str`` for assignability while still
surfacing the literals as completions in most editors.
"""

ChatRole = Literal["system", "user", "assistant", "tool"]


class TextContentPart(TypedDict):
    """A plain-text fragment of multi-part message content."""

    type: Literal["text"]
    text: str


class ImageURL(TypedDict, total=False):
    """The image reference inside an :class:`ImageContentPart`."""

    url: Required[str]
    detail: Literal["low", "high", "auto"]


class ImageContentPart(TypedDict):
    """An image fragment of multi-part message content, used for vision input.

    The ``url`` may be an inline ``data:`` URI or an HTTPS URL, for instance one
    returned by ``POST /v1/uploads/images``.
    """

    type: Literal["image_url"]
    image_url: ImageURL


ContentPart: TypeAlias = "TextContentPart | ImageContentPart"


class ChatCompletionMessageParam(TypedDict, total=False):
    """One message in a chat conversation, as supplied on the request.

    For ``role="tool"``, ``tool_call_id`` is required and must reference the
    ``id`` of the assistant tool call being answered.
    """

    role: Required[ChatRole]
    content: str | list[ContentPart] | None
    tool_calls: list[ToolCallParam]
    tool_call_id: str


class ToolCallFunctionParam(TypedDict):
    """The function payload of an assistant :class:`ToolCallParam`."""

    name: str
    arguments: str


class ToolCallParam(TypedDict):
    """A tool invocation supplied back to the model on an assistant turn."""

    id: str
    type: Literal["function"]
    function: ToolCallFunctionParam


class ToolFunctionParam(TypedDict, total=False):
    """A function definition inside a :class:`ToolParam`."""

    name: Required[str]
    description: str
    parameters: dict[str, Any]


class ToolParam(TypedDict):
    """A function-calling tool definition, OpenAI-compatible."""

    type: Literal["function"]
    function: ToolFunctionParam


Tool = ToolParam


class _ToolChoiceFunction(TypedDict):
    name: str


class ToolChoiceNamed(TypedDict):
    """The object form of :data:`ToolChoice` that pins a specific function."""

    type: Literal["function"]
    function: _ToolChoiceFunction


ToolChoice: TypeAlias = 'Literal["auto", "none", "required"] | ToolChoiceNamed'
"""Controls whether/which tools may be called."""


class ResponseFormat(TypedDict, total=False):
    """Requested output structure, OpenAI-compatible.

    Honored only when the selected upstream model supports it.
    """

    type: Required[Literal["text", "json_object", "json_schema"]]
    json_schema: dict[str, Any]


ReasoningEffort = Literal["low", "medium", "high"]
"""Reasoning budget for reasoning-capable models. Ignored by other models."""

FinishReason = Literal["stop", "length", "tool_calls", "content_filter"]


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A tool invocation emitted by the assistant.

    Attributes:
        id: Stable identifier correlating this call with its tool result.
        name: Name of the invoked function.
        arguments: JSON-encoded argument object as a string; callers ``json.loads`` it.
    """

    id: str
    type: Literal["function"]
    name: str
    arguments: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolCall:
        """Build a :class:`ToolCall` from a parsed JSON object."""
        function = data.get("function") or {}
        return cls(
            id=data.get("id", ""),
            type="function",
            name=function.get("name", ""),
            arguments=function.get("arguments", ""),
        )


@dataclass(frozen=True, slots=True)
class ChatCompletionMessage:
    """The assistant message inside a non-streamed :class:`Choice`.

    Attributes:
        role: Always ``"assistant"``.
        content: The generated text; may be empty when only tool calls are present.
        reasoning_content: Reasoning trace for models that expose their thinking.
        tool_calls: Tool calls the assistant requested, if any.
    """

    role: Literal["assistant"]
    content: str | None
    reasoning_content: str | None
    tool_calls: tuple[ToolCall, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatCompletionMessage:
        """Build a :class:`ChatCompletionMessage` from a parsed JSON object."""
        return cls(
            role="assistant",
            content=data.get("content"),
            reasoning_content=data.get("reasoning_content"),
            tool_calls=tuple(ToolCall.from_dict(tc) for tc in data.get("tool_calls") or ()),
        )


@dataclass(frozen=True, slots=True)
class Choice:
    """A single completed choice within a non-streamed :class:`ChatCompletion`."""

    index: int
    message: ChatCompletionMessage
    finish_reason: FinishReason | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Choice:
        """Build a :class:`Choice` from a parsed JSON object."""
        return cls(
            index=data.get("index", 0),
            message=ChatCompletionMessage.from_dict(data.get("message") or {}),
            finish_reason=data.get("finish_reason"),
        )


@dataclass(frozen=True, slots=True)
class ChatCompletion:
    """A complete, non-streamed chat completion (``object: "chat.completion"``)."""

    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    choices: tuple[Choice, ...]
    usage: Usage | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatCompletion:
        """Build a :class:`ChatCompletion` from a parsed JSON object."""
        usage = data.get("usage")
        return cls(
            id=data.get("id", ""),
            object="chat.completion",
            created=data.get("created", 0),
            model=data.get("model", ""),
            choices=tuple(Choice.from_dict(c) for c in data.get("choices") or ()),
            usage=Usage.from_dict(usage) if usage is not None else None,
        )


@dataclass(frozen=True, slots=True)
class ChunkToolCall:
    """An incremental tool-call fragment carried by a streamed delta."""

    index: int
    id: str | None
    name: str | None
    arguments: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChunkToolCall:
        """Build a :class:`ChunkToolCall` from a parsed JSON object."""
        function = data.get("function") or {}
        return cls(
            index=data.get("index", 0),
            id=data.get("id"),
            name=function.get("name"),
            arguments=function.get("arguments"),
        )


@dataclass(frozen=True, slots=True)
class ChoiceDelta:
    """The incremental payload of a streamed :class:`ChunkChoice`.

    Streaming assembles a tool call across chunks: the first fragment for a given
    index carries ``id``/``name``, later fragments append to ``arguments``.
    """

    role: Literal["assistant"] | None
    content: str | None
    reasoning_content: str | None
    tool_calls: tuple[ChunkToolCall, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChoiceDelta:
        """Build a :class:`ChoiceDelta` from a parsed JSON object."""
        return cls(
            role=data.get("role"),
            content=data.get("content"),
            reasoning_content=data.get("reasoning_content"),
            tool_calls=tuple(
                ChunkToolCall.from_dict(tc) for tc in data.get("tool_calls") or ()
            ),
        )


@dataclass(frozen=True, slots=True)
class ChunkChoice:
    """A single choice slice within a streamed :class:`ChatCompletionChunk`."""

    index: int
    delta: ChoiceDelta
    finish_reason: FinishReason | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChunkChoice:
        """Build a :class:`ChunkChoice` from a parsed JSON object."""
        return cls(
            index=data.get("index", 0),
            delta=ChoiceDelta.from_dict(data.get("delta") or {}),
            finish_reason=data.get("finish_reason"),
        )


@dataclass(frozen=True, slots=True)
class ChatCompletionChunk:
    """One streamed delta (``object: "chat.completion.chunk"``).

    The gateway reports cumulative :class:`Usage` on each chunk; treat ``usage``
    as the latest snapshot, not an increment.
    """

    id: str
    object: Literal["chat.completion.chunk"]
    created: int
    model: str
    choices: tuple[ChunkChoice, ...]
    usage: Usage | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatCompletionChunk:
        """Build a :class:`ChatCompletionChunk` from a parsed JSON object."""
        usage = data.get("usage")
        return cls(
            id=data.get("id", ""),
            object="chat.completion.chunk",
            created=data.get("created", 0),
            model=data.get("model", ""),
            choices=tuple(ChunkChoice.from_dict(c) for c in data.get("choices") or ()),
            usage=Usage.from_dict(usage) if usage is not None else None,
        )
