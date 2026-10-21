"""Hard limits: tokens, USD, wall-clock, replans."""
from __future__ import annotations

import time

from pydantic import BaseModel, Field


class Budget(BaseModel):
    max_usd: float = 2.00
    max_tokens: int = 400_000
    max_seconds: float = 300.0
    max_replans: int = 2

    spent_usd: float = 0.0
    spent_tokens: int = 0
    replans: int = 0
    started_at: float = Field(default_factory=time.monotonic)

    def charge(self, usd: float = 0.0, tokens: int = 0) -> None:
        self.spent_usd += usd
        self.spent_tokens += tokens

    def record_replan(self) -> None:
        self.replans += 1

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.started_at

    def ok(self) -> bool:
        return (
            self.spent_usd < self.max_usd
            and self.spent_tokens < self.max_tokens
            and self.elapsed < self.max_seconds
            and self.replans <= self.max_replans
        )
