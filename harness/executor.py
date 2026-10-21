"""Executor: deterministic tool calls from the plan via the gateway."""
from __future__ import annotations

from typing import Any

from harness.gateway.policy import authorize
from harness.state import Step


async def execute(step: Step) -> Any:
    authorize(step)
    # TODO: dispatch to the MCP gateway with an idempotency key.
    raise NotImplementedError(f"no tool dispatch for {step.tool!r} yet")
