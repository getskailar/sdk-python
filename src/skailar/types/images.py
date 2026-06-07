"""Types for the image generation resource (``POST /v1/images/generations``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["GeneratedImage", "ImageGenerationResponse"]


@dataclass(frozen=True, slots=True)
class GeneratedImage:
    """A single generated image.

    Exactly one of ``url`` or ``b64_json`` is populated, depending on the
    provider's delivery mode.

    Attributes:
        url: HTTPS URL of the generated image, when delivered by reference.
        b64_json: Base64-encoded image bytes, when delivered inline.
        revised_prompt: The prompt after any provider-side rewriting, if applicable.
    """

    url: str | None
    b64_json: str | None
    revised_prompt: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GeneratedImage:
        """Build a :class:`GeneratedImage` from a parsed JSON object."""
        return cls(
            url=data.get("url"),
            b64_json=data.get("b64_json"),
            revised_prompt=data.get("revised_prompt"),
        )


@dataclass(frozen=True, slots=True)
class ImageGenerationResponse:
    """Response body for ``POST /v1/images/generations``."""

    created: int
    data: tuple[GeneratedImage, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ImageGenerationResponse:
        """Build an :class:`ImageGenerationResponse` from a parsed JSON object."""
        return cls(
            created=data.get("created", 0),
            data=tuple(GeneratedImage.from_dict(d) for d in data.get("data") or ()),
        )
