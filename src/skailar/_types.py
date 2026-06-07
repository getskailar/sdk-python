"""Sentinels and shared transport types used across the SDK internals."""

from __future__ import annotations

from typing import Literal

import httpx

__all__ = ["NotGiven", "NOT_GIVEN", "Timeout", "Headers", "Body"]


class NotGiven:
    """Sentinel marking an argument the caller never supplied.

    Distinct from ``None``: ``None`` is a value sent to the server (JSON ``null``),
    while a :class:`NotGiven` argument is stripped from the wire body entirely.
    The singleton :data:`NOT_GIVEN` is the only instance ever used.
    """

    def __bool__(self) -> Literal[False]:
        return False

    def __repr__(self) -> str:
        return "NOT_GIVEN"


NOT_GIVEN = NotGiven()

Timeout = float | httpx.Timeout
Headers = dict[str, str]
Body = dict[str, object]
