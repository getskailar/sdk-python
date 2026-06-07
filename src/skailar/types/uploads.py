"""Types for the uploads resource: image and file uploads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

__all__ = ["ImageContentType", "FileContentType", "UploadResponse"]

ImageContentType = Literal["image/png", "image/jpeg", "image/gif", "image/webp"]
"""Content types accepted by ``POST /v1/uploads/images``."""

FileContentType = Literal["application/pdf", "text/plain"]
"""Content types accepted by ``POST /v1/uploads/files``."""


@dataclass(frozen=True, slots=True)
class UploadResponse:
    """Response body for the upload endpoints.

    Attributes:
        url: URL of the stored asset, ready to embed in subsequent calls -- for
            example as the ``url`` of a vision image content part.
        content_type: MIME type the asset was stored as.
    """

    url: str
    content_type: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UploadResponse:
        """Build an :class:`UploadResponse` from a parsed JSON object."""
        return cls(url=data.get("url", ""), content_type=data.get("content_type", ""))
