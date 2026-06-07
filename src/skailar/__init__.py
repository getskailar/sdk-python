"""The official Python SDK for the Skailar API.

Exposes the synchronous :class:`Skailar` and asynchronous :class:`AsyncSkailar`
clients, the typed error hierarchy, the streaming wrappers, and the public
request/response types.

Example:
    >>> from skailar import Skailar
    >>> client = Skailar(api_key="skl_live_...")
    >>> res = client.chat.completions.create(
    ...     model="claude-sonnet-4-6",
    ...     messages=[{"role": "user", "content": "Hello!"}],
    ... )
    >>> print(res.choices[0].message.content)
"""

from __future__ import annotations

from ._client import AsyncSkailar, Skailar
from ._exceptions import (
    SkailarAPIError,
    SkailarAuthError,
    SkailarBadRequestError,
    SkailarConnectionError,
    SkailarError,
    SkailarNotFoundError,
    SkailarRateLimitError,
    SkailarUpstreamError,
)
from ._streaming import AsyncStream, Stream
from ._types import NOT_GIVEN, NotGiven
from .resources import AsyncSpeechStream, SpeechStream
from .types import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    Choice,
    ChoiceDelta,
    ChunkChoice,
    GeneratedImage,
    ImageGenerationResponse,
    Model,
    ModelCapabilities,
    ModelList,
    ModelPricing,
    ModelSummary,
    PingKeyResponse,
    Tool,
    ToolCall,
    TranscriptionResponse,
    UploadResponse,
    Usage,
)

__version__ = "0.0.1"

__all__ = [
    "Skailar",
    "AsyncSkailar",
    "Stream",
    "AsyncStream",
    "SpeechStream",
    "AsyncSpeechStream",
    "NOT_GIVEN",
    "NotGiven",
    "SkailarError",
    "SkailarAPIError",
    "SkailarAuthError",
    "SkailarBadRequestError",
    "SkailarNotFoundError",
    "SkailarRateLimitError",
    "SkailarUpstreamError",
    "SkailarConnectionError",
    "ChatCompletion",
    "ChatCompletionChunk",
    "ChatCompletionMessage",
    "ChatCompletionMessageParam",
    "Choice",
    "ChoiceDelta",
    "ChunkChoice",
    "GeneratedImage",
    "ImageGenerationResponse",
    "Model",
    "ModelCapabilities",
    "ModelList",
    "ModelPricing",
    "ModelSummary",
    "PingKeyResponse",
    "Tool",
    "ToolCall",
    "TranscriptionResponse",
    "UploadResponse",
    "Usage",
    "__version__",
]
