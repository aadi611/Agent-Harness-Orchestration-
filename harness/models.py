"""Model router: map a tier to a concrete model."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Tier(str, Enum):
    STRONG = "strong"          # planner, critic
    STRONG_ALT = "strong_alt"  # judge, different family from producer
    MID = "mid"                # analysis, coding, reporting
    SMALL = "small"            # routing, classification, extraction


class ModelSpec(BaseModel):
    provider: str
    name: str


# Placeholder defaults; override per deployment.
DEFAULT_ROUTES: dict[Tier, ModelSpec] = {
    Tier.STRONG: ModelSpec(provider="anthropic", name="strong-model"),
    Tier.STRONG_ALT: ModelSpec(provider="openai", name="strong-alt-model"),
    Tier.MID: ModelSpec(provider="anthropic", name="mid-model"),
    Tier.SMALL: ModelSpec(provider="anthropic", name="small-model"),
}


class ModelRouter:
    def __init__(self, routes: dict[Tier, ModelSpec] | None = None) -> None:
        self.routes = routes or DEFAULT_ROUTES

    def resolve(self, tier: Tier | str) -> ModelSpec:
        return self.routes[Tier(tier)]

    def judge_for(self, producer: ModelSpec) -> ModelSpec:
        """Judge must be a different model family from the producer."""
        spec = self.routes[Tier.STRONG_ALT]
        if spec.provider == producer.provider:
            raise ValueError("judge must be a different model family from the producer")
        return spec
