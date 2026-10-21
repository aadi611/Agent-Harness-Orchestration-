"""Scheduler: run every ready step concurrently."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from harness.state import PlanDAG, Step


async def run_frontier(
    plan: PlanDAG,
    execute: Callable[[Step], Awaitable[Any]],
) -> list[tuple[Step, Any]]:
    ready = plan.ready_steps()
    outputs = await asyncio.gather(*(execute(s) for s in ready))
    return list(zip(ready, outputs, strict=True))
