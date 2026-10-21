"""Checkpoint after every node (Postgres). Runs can resume, replay, or fork."""
from __future__ import annotations

from harness.state import State


class InMemoryCheckpointer:
    """Dev stand-in; swap for a Postgres-backed checkpointer."""

    def __init__(self) -> None:
        self._runs: dict[str, list[str]] = {}

    def save(self, run_id: str, state: State) -> int:
        self._runs.setdefault(run_id, []).append(state.model_dump_json())
        return len(self._runs[run_id]) - 1

    def load(self, run_id: str, index: int = -1) -> State:
        return State.model_validate_json(self._runs[run_id][index])
