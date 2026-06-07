"""Internal helpers: NotGiven stripping, base64 normalization, and retry math."""

from __future__ import annotations

import base64
import random
from typing import Any

from ._types import NotGiven

__all__ = [
    "strip_not_given",
    "to_base64",
    "cap_retry_delay",
    "backoff_delay",
    "MAX_RETRY_DELAY_SECONDS",
]

MAX_RETRY_DELAY_SECONDS = 60.0
"""Upper bound on a single automatic retry delay, in seconds.

Caps a server ``Retry-After`` so an oversized value cannot park a call for
minutes; the true requested value is still exposed on
:attr:`SkailarRateLimitError.retry_after`.
"""

_BACKOFF_BASE_SECONDS = 0.5
_BACKOFF_CAP_SECONDS = 8.0


def strip_not_given(data: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose value is the :data:`NOT_GIVEN` sentinel.

    Args:
        data: A request-body mapping that may contain unsupplied parameters.

    Returns:
        A new mapping with every :class:`NotGiven` value removed. ``None`` values
        are preserved, since they are meaningful (JSON ``null``) on the wire.
    """
    return {key: value for key, value in data.items() if not isinstance(value, NotGiven)}


def to_base64(data: bytes | bytearray | str) -> str:
    """Normalize a binary payload into a base64 string with no ``data:`` prefix.

    Args:
        data: Raw bytes to encode, or a string assumed to be already base64.

    Returns:
        The base64 representation. A ``str`` input is returned unchanged on the
        assumption it is pre-encoded; pass ``bytes`` when you hold raw data.
    """
    if isinstance(data, str):
        return data
    return base64.b64encode(bytes(data)).decode("ascii")


def cap_retry_delay(retry_after_seconds: int | float | None) -> float | None:
    """Bound a server ``Retry-After`` value to :data:`MAX_RETRY_DELAY_SECONDS`.

    Args:
        retry_after_seconds: Seconds requested by the server, or ``None``.

    Returns:
        The capped delay in seconds, or ``None`` when no value was given.
    """
    if retry_after_seconds is None:
        return None
    return min(max(0.0, float(retry_after_seconds)), MAX_RETRY_DELAY_SECONDS)


def backoff_delay(attempt: int) -> float:
    """Compute a full-jitter exponential backoff delay in seconds.

    A random value in ``[0, min(cap, base * 2**attempt))`` spreads retries across
    clients to avoid synchronized load on the gateway.

    Args:
        attempt: The retry number, starting at 1 for the first retry.

    Returns:
        A randomized delay in seconds.
    """
    exponential = min(_BACKOFF_CAP_SECONDS, _BACKOFF_BASE_SECONDS * 2**attempt)
    delay: float = random.random() * exponential
    return delay
