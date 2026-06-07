"""The models resource: ``client.models.list()`` and ``client.models.retrieve(id)``."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from .._base_client import FinalRequestOptions
from .._types import Headers, Timeout
from ..types.models import Model, ModelList, ModelSummary

if TYPE_CHECKING:
    from .._client import AsyncSkailar, Skailar

__all__ = ["ModelsResource", "AsyncModelsResource"]


def _encode_id(model_id: str) -> str:
    """Percent-encode each path segment while preserving slashes in the id."""
    return "/".join(quote(segment, safe="") for segment in model_id.split("/"))


class ModelsResource:
    """Synchronous model discovery operations."""

    def __init__(self, client: Skailar) -> None:
        self._client = client

    def list(
        self, *, timeout: Timeout | None = None, headers: Headers | None = None
    ) -> list[ModelSummary]:
        """List every model the gateway can route to.

        Unwraps the ``{object: "list", data}`` envelope and returns ``data``.

        Args:
            timeout: Optional per-call timeout override.
            headers: Optional per-call extra headers.

        Returns:
            The list of :class:`ModelSummary` cards.
        """
        data = self._client.request(
            FinalRequestOptions(
                method="GET",
                path="/v1/models",
                expect="json",
                idempotent=True,
                timeout=timeout,
                headers=headers,
            )
        )
        return list(ModelList.from_dict(data).data)

    def retrieve(
        self, model_id: str, *, timeout: Timeout | None = None, headers: Headers | None = None
    ) -> Model:
        """Retrieve the full detail card for a single model.

        Args:
            model_id: The model identifier; may contain slashes (e.g.
                ``"google/gemini-2.5-pro"``), which are preserved in the path.
            timeout: Optional per-call timeout override.
            headers: Optional per-call extra headers.

        Returns:
            The :class:`Model` detail.

        Raises:
            SkailarNotFoundError: If no model matches the id.
        """
        data = self._client.request(
            FinalRequestOptions(
                method="GET",
                path=f"/v1/models/{_encode_id(model_id)}",
                expect="json",
                idempotent=True,
                timeout=timeout,
                headers=headers,
            )
        )
        return Model.from_dict(data)


class AsyncModelsResource:
    """Asynchronous model discovery operations."""

    def __init__(self, client: AsyncSkailar) -> None:
        self._client = client

    async def list(
        self, *, timeout: Timeout | None = None, headers: Headers | None = None
    ) -> list[ModelSummary]:
        """Async counterpart of :meth:`ModelsResource.list`."""
        data = await self._client.request(
            FinalRequestOptions(
                method="GET",
                path="/v1/models",
                expect="json",
                idempotent=True,
                timeout=timeout,
                headers=headers,
            )
        )
        return list(ModelList.from_dict(data).data)

    async def retrieve(
        self, model_id: str, *, timeout: Timeout | None = None, headers: Headers | None = None
    ) -> Model:
        """Async counterpart of :meth:`ModelsResource.retrieve`."""
        data = await self._client.request(
            FinalRequestOptions(
                method="GET",
                path=f"/v1/models/{_encode_id(model_id)}",
                expect="json",
                idempotent=True,
                timeout=timeout,
                headers=headers,
            )
        )
        return Model.from_dict(data)
