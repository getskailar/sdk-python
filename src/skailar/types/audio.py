"""Types for the audio resource: transcription and speech synthesis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

__all__ = [
    "BinaryInput",
    "TranscriptionMime",
    "SpeechVoice",
    "TranscriptionResponse",
]

BinaryInput = bytes | bytearray | str
"""Binary payload accepted by SDK methods that upload bytes.

A ``str`` is treated as **already-encoded** base64 (no ``data:`` prefix) and is
forwarded without validation -- pass ``bytes`` for raw data.
"""

TranscriptionMime = Literal[
    "audio/wav",
    "audio/webm",
    "audio/mp4",
    "audio/m4a",
    "audio/mpeg",
    "audio/mp3",
]

SpeechVoice = Literal[
    "alloy",
    "ash",
    "ballad",
    "coral",
    "echo",
    "fable",
    "nova",
    "onyx",
    "sage",
    "shimmer",
]


@dataclass(frozen=True, slots=True)
class TranscriptionResponse:
    """Response body for ``POST /v1/audio/transcriptions``.

    Attributes:
        text: The transcribed text.
    """

    text: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TranscriptionResponse:
        """Build a :class:`TranscriptionResponse` from a parsed JSON object."""
        return cls(text=data.get("text", ""))
