"""Short-term typed state, long-term memory (written only after verification), compaction."""
from __future__ import annotations

COMPACTION_THRESHOLD = 0.60  # compact when context exceeds ~60% of the window


class LongTermMemory:
    """Key-value facts; vector store (pgvector) to follow."""

    def __init__(self) -> None:
        self._facts: dict[str, str] = {}

    def write_verified(self, key: str, value: str) -> None:
        self._facts[key] = value

    def read(self, key: str) -> str | None:
        return self._facts.get(key)


def needs_compaction(used_tokens: int, window_tokens: int) -> bool:
    return used_tokens / window_tokens > COMPACTION_THRESHOLD
