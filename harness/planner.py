"""Planner (strong LLM): goal -> PlanDAG. LLM call is stubbed for now."""
from __future__ import annotations

from harness.state import PlanDAG, State


async def plan(state: State, replace: set[str] | None = None) -> PlanDAG:
    """Produce a PlanDAG for state.goal; if `replace` is set, replan only that subtree.

    TODO: call the STRONG tier via ModelRouter with a structured-output schema.
    """
    raise NotImplementedError("planner LLM call not wired up yet")
