"""OTel spans (one trace per run, one span per node and tool call) and cost ledger."""
from __future__ import annotations

from collections import defaultdict


class CostLedger:
    def __init__(self) -> None:
        self.usd: dict[str, float] = defaultdict(float)
        self.tokens: dict[str, int] = defaultdict(int)

    def record(self, run_id: str, usd: float, tokens: int) -> None:
        self.usd[run_id] += usd
        self.tokens[run_id] += tokens
