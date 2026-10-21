"""Tier 1: cheap deterministic gates, run before any LLM judge."""
from __future__ import annotations

import json
from typing import Any

from harness.router import Verdict, VerdictKind


def schema_gate(output: Any, required_keys: list[str]) -> bool:
    return isinstance(output, dict) and all(k in output for k in required_keys)


def quote_gate(quote: str, source_text: str) -> bool:
    """Quoted spans must exist in the source."""
    return quote in source_text


def recompute_gate(claimed: float, recomputed: float, tol: float = 1e-6) -> bool:
    return abs(claimed - recomputed) <= tol


def run_gates(output: Any, required_keys: list[str] | None = None) -> Verdict:
    if required_keys and not schema_gate(output, required_keys):
        return Verdict(
            kind=VerdictKind.BAD_OUTPUT,
            critique=f"output must be an object with keys {json.dumps(required_keys)}",
        )
    return Verdict(kind=VerdictKind.PASS)
