"""MCP gateway: single choke point for schema validation, rate limit, cache, audit."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def idempotency_key(run_id: str, step_id: str, args: dict[str, Any]) -> str:
    """Retries reuse the key so side effects never double-fire."""
    payload = json.dumps([run_id, step_id, args], sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


async def call_tool(tool: str, args: dict[str, Any], *, key: str) -> Any:
    # TODO: validate against tool schema, rate-limit, cache by hash(tool, args), audit.
    raise NotImplementedError(f"MCP dispatch for {tool!r} not implemented yet")
