"""Type for the utility resource (``GET /v1/ping-key``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["PingKeyResponse"]


@dataclass(frozen=True, slots=True)
class PingKeyResponse:
    """Response body for ``GET /v1/ping-key``.

    Attributes:
        status: Always ``"ok"`` when the key is valid.
        user_id: The Skailar user id owning the key (UUID string).
    """

    status: str
    user_id: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PingKeyResponse:
        """Build a :class:`PingKeyResponse` from a parsed JSON object."""
        return cls(status=data.get("status", ""), user_id=data.get("user_id", ""))
