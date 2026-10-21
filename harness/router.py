"""Failure taxonomy and loop detection: cheapest correct recovery first."""
from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel


class VerdictKind(str, Enum):
    PASS = "pass"
    TOOL_ERROR = "tool_error"      # retry step with backoff
    BAD_OUTPUT = "bad_output"      # re-run step with critique
    BAD_PLAN = "bad_plan"          # replan subtree only
    BUDGET_EXHAUSTED = "budget_exhausted"  # escalate to human


class Verdict(BaseModel):
    kind: VerdictKind
    critique: str = ""
    error: str = ""


class Action(str, Enum):
    ACCEPT = "accept"
    RETRY_STEP = "retry_step"
    RERUN_STEP = "rerun_step"
    REPLAN_SUBTREE = "replan_subtree"
    ESCALATE = "escalate"


_ROUTES = {
    VerdictKind.PASS: Action.ACCEPT,
    VerdictKind.TOOL_ERROR: Action.RETRY_STEP,
    VerdictKind.BAD_OUTPUT: Action.RERUN_STEP,
    VerdictKind.BAD_PLAN: Action.REPLAN_SUBTREE,
    VerdictKind.BUDGET_EXHAUSTED: Action.ESCALATE,
}


def route(verdict: Verdict) -> Action:
    return _ROUTES[verdict.kind]


class LoopDetector:
    """Hash (step_id, args, error); the same hash seen twice means stop retrying."""

    def __init__(self) -> None:
        self._seen: set[str] = set()

    @staticmethod
    def fingerprint(step_id: str, args: dict, error: str) -> str:
        payload = json.dumps([step_id, args, error], sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()

    def check(self, step_id: str, args: dict, error: str) -> bool:
        """Return True if this failure was already seen (loop detected)."""
        fp = self.fingerprint(step_id, args, error)
        if fp in self._seen:
            return True
        self._seen.add(fp)
        return False
