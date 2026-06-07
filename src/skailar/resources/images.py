"""The images resource: ``client.images.generate(...)``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._base_client import FinalRequestOptions
from .._types import NOT_GIVEN, Headers, NotGiven, Timeout
from .._utils import strip_not_given
from ..types.chat import ModelId
from ..types.images import ImageGenerationResponse

if TYPE_CHECKING:
    from .._client import AsyncSkailar, Skailar

__all__ = ["ImagesResource", "AsyncImagesResource"]

_PATH = "/v1/images/generations"


def _build_body(
    *,
    model: ModelId,
    prompt: str,
    n: int | NotGiven,
    size: str | NotGiven,
    quality: str | NotGiven,
    background: str | NotGiven,
) -> dict[str, object]:
    return strip_not_given(
        {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "quality": quality,
            "background": background,
        }
    )


class ImagesResource:
    """Synchronous image generation operations."""

    def __init__(self, client: Skailar) -> None:
        self._client = client

    def generate(
        self,
        *,
        model: ModelId,
        prompt: str,
        n: int | NotGiven = NOT_GIVEN,
        size: str | NotGiven = NOT_GIVEN,
        quality: str | NotGiven = NOT_GIVEN,
        background: str | NotGiven = NOT_GIVEN,
        timeout: Timeout | None = None,
        headers: Headers | None = None,
    ) -> ImageGenerationResponse:
        """Generate one or more images from a text prompt.

        Named ``generate`` to match ``openai``'s ``images.generate(...)``.

        Args:
            model: Image model identifier (e.g. ``"gpt-image-1"``).
            prompt: Natural-language description of the desired image.
            n: Number of images to generate, in ``[1, 10]``.
            size: Output resolution, e.g. ``"1024x1024"`` (provider-dependent).
            quality: Provider-specific quality hint (e.g. ``"standard"``, ``"hd"``).
            background: Provider-specific background hint (e.g. ``"transparent"``).
            timeout: Optional per-call timeout override.
            headers: Optional per-call extra headers.

        Returns:
            The :class:`ImageGenerationResponse`, whose ``data`` entries carry
            either a ``url`` or inline ``b64_json``.

        Raises:
            SkailarBadRequestError: On HTTP 400.
            SkailarRateLimitError: On HTTP 429 (after exhausting retries).
        """
        data = self._client.request(
            FinalRequestOptions(
                method="POST",
                path=_PATH,
                expect="json",
                body=_build_body(
                    model=model,
                    prompt=prompt,
                    n=n,
                    size=size,
                    quality=quality,
                    background=background,
                ),
                idempotent=False,
                timeout=timeout,
                headers=headers,
            )
        )
        return ImageGenerationResponse.from_dict(data)


class AsyncImagesResource:
    """Asynchronous image generation operations."""

    def __init__(self, client: AsyncSkailar) -> None:
        self._client = client

    async def generate(
        self,
        *,
        model: ModelId,
        prompt: str,
        n: int | NotGiven = NOT_GIVEN,
        size: str | NotGiven = NOT_GIVEN,
        quality: str | NotGiven = NOT_GIVEN,
        background: str | NotGiven = NOT_GIVEN,
        timeout: Timeout | None = None,
        headers: Headers | None = None,
    ) -> ImageGenerationResponse:
        """Async counterpart of :meth:`ImagesResource.generate`."""
        data = await self._client.request(
            FinalRequestOptions(
                method="POST",
                path=_PATH,
                expect="json",
                body=_build_body(
                    model=model,
                    prompt=prompt,
                    n=n,
                    size=size,
                    quality=quality,
                    background=background,
                ),
                idempotent=False,
                timeout=timeout,
                headers=headers,
            )
        )
        return ImageGenerationResponse.from_dict(data)
