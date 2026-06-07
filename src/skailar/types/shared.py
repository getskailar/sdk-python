"""Primitive types shared across multiple Skailar API resources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["Usage"]


@dataclass(frozen=True, slots=True)
class Usage:
    """Token accounting returned with every completion, streamed or not.

    Mirrors the OpenAI ``usage`` object. On a stream each chunk carries the
    running totals observed so far rather than a per-chunk delta.

    Attributes:
        prompt_tokens: Tokens consumed by the prompt (input side).
        completion_tokens: Tokens produced by the model (output side).
        total_tokens: Sum of prompt and completion tokens.
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Usage:
        """Build a :class:`Usage` from a parsed JSON object."""
        return cls(
            prompt_tokens=data["prompt_tokens"],
            completion_tokens=data["completion_tokens"],
            total_tokens=data["total_tokens"],
        )
