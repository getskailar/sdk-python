"""The uploads resource: ``client.uploads.images.create(...)`` and
``client.uploads.files.create(...)``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._base_client import FinalRequestOptions
from .._types import Headers, Timeout
from .._utils import to_base64
from ..types.audio import BinaryInput
from ..types.uploads import FileContentType, ImageContentType, UploadResponse

if TYPE_CHECKING:
    from .._client import AsyncSkailar, Skailar

__all__ = ["UploadsResource", "AsyncUploadsResource"]


class ImageUploads:
    """Synchronous image upload operations (``POST /v1/uploads/images``)."""

    def __init__(self, client: Skailar) -> None:
        self._client = client

    def create(
        self,
        *,
        data: BinaryInput,
        content_type: ImageContentType,
        timeout: Timeout | None = None,
        headers: Headers | None = None,
    ) -> UploadResponse:
        """Upload an image and obtain a URL usable as vision input.

        ``data`` is base64-encoded client-side into the gateway's ``base64`` field.

        Args:
            data: The image bytes, or a pre-encoded base64 ``str``.
            content_type: MIME type of the image being uploaded.
            timeout: Optional per-call timeout override.
            headers: Optional per-call extra headers.

        Returns:
            The :class:`UploadResponse` whose ``url`` can be embedded in a chat
            completion as an ``image_url`` content part.
        """
        result = self._client.request(
            FinalRequestOptions(
                method="POST",
                path="/v1/uploads/images",
                expect="json",
                body={"base64": to_base64(data), "content_type": content_type},
                idempotent=False,
                timeout=timeout,
                headers=headers,
            )
        )
        return UploadResponse.from_dict(result)


class FileUploads:
    """Synchronous file upload operations (``POST /v1/uploads/files``)."""

    def __init__(self, client: Skailar) -> None:
        self._client = client

    def create(
        self,
        *,
        data: BinaryInput,
        content_type: FileContentType,
        timeout: Timeout | None = None,
        headers: Headers | None = None,
    ) -> UploadResponse:
        """Upload a document (``application/pdf`` or ``text/plain``).

        Args:
            data: The document bytes, or a pre-encoded base64 ``str``.
            content_type: MIME type of the document being uploaded.
            timeout: Optional per-call timeout override.
            headers: Optional per-call extra headers.

        Returns:
            The :class:`UploadResponse` with the stored asset URL.
        """
        result = self._client.request(
            FinalRequestOptions(
                method="POST",
                path="/v1/uploads/files",
                expect="json",
                body={"base64": to_base64(data), "content_type": content_type},
                idempotent=False,
                timeout=timeout,
                headers=headers,
            )
        )
        return UploadResponse.from_dict(result)


class UploadsResource:
    """The synchronous uploads resource root, grouping image and file uploads."""

    def __init__(self, client: Skailar) -> None:
        self.images = ImageUploads(client)
        self.files = FileUploads(client)


class AsyncImageUploads:
    """Asynchronous image upload operations."""

    def __init__(self, client: AsyncSkailar) -> None:
        self._client = client

    async def create(
        self,
        *,
        data: BinaryInput,
        content_type: ImageContentType,
        timeout: Timeout | None = None,
        headers: Headers | None = None,
    ) -> UploadResponse:
        """Async counterpart of :meth:`ImageUploads.create`."""
        result = await self._client.request(
            FinalRequestOptions(
                method="POST",
                path="/v1/uploads/images",
                expect="json",
                body={"base64": to_base64(data), "content_type": content_type},
                idempotent=False,
                timeout=timeout,
                headers=headers,
            )
        )
        return UploadResponse.from_dict(result)


class AsyncFileUploads:
    """Asynchronous file upload operations."""

    def __init__(self, client: AsyncSkailar) -> None:
        self._client = client

    async def create(
        self,
        *,
        data: BinaryInput,
        content_type: FileContentType,
        timeout: Timeout | None = None,
        headers: Headers | None = None,
    ) -> UploadResponse:
        """Async counterpart of :meth:`FileUploads.create`."""
        result = await self._client.request(
            FinalRequestOptions(
                method="POST",
                path="/v1/uploads/files",
                expect="json",
                body={"base64": to_base64(data), "content_type": content_type},
                idempotent=False,
                timeout=timeout,
                headers=headers,
            )
        )
        return UploadResponse.from_dict(result)


class AsyncUploadsResource:
    """The asynchronous uploads resource root."""

    def __init__(self, client: AsyncSkailar) -> None:
        self.images = AsyncImageUploads(client)
        self.files = AsyncFileUploads(client)
