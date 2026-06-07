"""Types for the models resource (``GET /v1/models`` and ``GET /v1/models/{id}``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = [
    "ModelCapabilities",
    "ModelPricing",
    "ModelSummary",
    "Model",
    "ModelList",
]


@dataclass(frozen=True, slots=True)
class ModelCapabilities:
    """Capability flags describing what a model can do."""

    streaming: bool
    tool_calls: bool
    vision: bool
    json_mode: bool
    reasoning: bool | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelCapabilities:
        """Build :class:`ModelCapabilities` from a parsed JSON object."""
        return cls(
            streaming=bool(data.get("streaming", False)),
            tool_calls=bool(data.get("tool_calls", False)),
            vision=bool(data.get("vision", False)),
            json_mode=bool(data.get("json_mode", False)),
            reasoning=data.get("reasoning"),
        )


@dataclass(frozen=True, slots=True)
class ModelPricing:
    """Per-token pricing for a model.

    Attributes:
        input_per_mtok: Cost per one million input tokens, in ``currency``.
        output_per_mtok: Cost per one million output tokens, in ``currency``.
        currency: ISO 4217 currency code (e.g. ``"USD"``).
    """

    input_per_mtok: float
    output_per_mtok: float
    currency: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelPricing:
        """Build :class:`ModelPricing` from a parsed JSON object."""
        return cls(
            input_per_mtok=data.get("input_per_mtok", 0.0),
            output_per_mtok=data.get("output_per_mtok", 0.0),
            currency=data.get("currency", "USD"),
        )


@dataclass(frozen=True, slots=True)
class ModelSummary:
    """Summary card for a model as returned by ``GET /v1/models``."""

    id: str
    object: str
    created: int
    owned_by: str
    display_name: str
    context_window: int
    max_output_tokens: int
    capabilities: ModelCapabilities
    pricing: ModelPricing
    status: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelSummary:
        """Build a :class:`ModelSummary` from a parsed JSON object."""
        return cls(
            id=data.get("id", ""),
            object=data.get("object", "model"),
            created=data.get("created", 0),
            owned_by=data.get("owned_by", ""),
            display_name=data.get("display_name", ""),
            context_window=data.get("context_window", 0),
            max_output_tokens=data.get("max_output_tokens", 0),
            capabilities=ModelCapabilities.from_dict(data.get("capabilities") or {}),
            pricing=ModelPricing.from_dict(data.get("pricing") or {}),
            status=data.get("status", ""),
        )


@dataclass(frozen=True, slots=True)
class Model(ModelSummary):
    """Full detail card for a model as returned by ``GET /v1/models/{id}``.

    Extends :class:`ModelSummary` with descriptive and routing metadata; all
    extended fields are optional because availability varies by provider.
    """

    description: str | None = None
    modalities_input: tuple[str, ...] = ()
    modalities_output: tuple[str, ...] = ()
    supported_parameters: tuple[str, ...] = ()
    knowledge_cutoff: str | None = None
    released_at: str | None = None
    documentation_url: str | None = None
    aliases: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Model:
        """Build a :class:`Model` from a parsed JSON object."""
        modalities = data.get("modalities") or {}
        return cls(
            id=data.get("id", ""),
            object=data.get("object", "model"),
            created=data.get("created", 0),
            owned_by=data.get("owned_by", ""),
            display_name=data.get("display_name", ""),
            context_window=data.get("context_window", 0),
            max_output_tokens=data.get("max_output_tokens", 0),
            capabilities=ModelCapabilities.from_dict(data.get("capabilities") or {}),
            pricing=ModelPricing.from_dict(data.get("pricing") or {}),
            status=data.get("status", ""),
            description=data.get("description"),
            modalities_input=tuple(modalities.get("input") or ()),
            modalities_output=tuple(modalities.get("output") or ()),
            supported_parameters=tuple(data.get("supported_parameters") or ()),
            knowledge_cutoff=data.get("knowledge_cutoff"),
            released_at=data.get("released_at"),
            documentation_url=data.get("documentation_url"),
            aliases=tuple(data.get("aliases") or ()),
        )


@dataclass(frozen=True, slots=True)
class ModelList:
    """Envelope returned by ``GET /v1/models``."""

    object: str
    data: tuple[ModelSummary, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelList:
        """Build a :class:`ModelList` from a parsed JSON object."""
        return cls(
            object=data.get("object", "list"),
            data=tuple(ModelSummary.from_dict(m) for m in data.get("data") or ()),
        )
