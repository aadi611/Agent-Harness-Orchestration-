"""Typed shared state: State, PlanDAG, Step. Nodes read only declared slices."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from harness.budget import Budget


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Step(BaseModel):
    id: str
    deps: list[str] = Field(default_factory=list)
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    acceptance_criteria: list[str] = Field(default_factory=list)
    side_effect: bool = False
    status: StepStatus = StepStatus.PENDING
    attempts: int = 0


class PlanDAG(BaseModel):
    steps: dict[str, Step] = Field(default_factory=dict)

    def add(self, step: Step) -> None:
        self.steps[step.id] = step

    @property
    def done(self) -> bool:
        return all(s.status == StepStatus.DONE for s in self.steps.values())

    def ready_steps(self) -> list[Step]:
        """DAG frontier: pending steps whose deps are all done."""
        return [
            s
            for s in self.steps.values()
            if s.status == StepStatus.PENDING
            and all(self.steps[d].status == StepStatus.DONE for d in s.deps)
        ]

    def mark_done(self, step_id: str) -> None:
        self.steps[step_id].status = StepStatus.DONE

    def subtree(self, step_id: str) -> set[str]:
        """The step plus every transitive dependent (what a replan replaces)."""
        out = {step_id}
        changed = True
        while changed:
            changed = False
            for s in self.steps.values():
                if s.id not in out and out.intersection(s.deps):
                    out.add(s.id)
                    changed = True
        return out


class State(BaseModel):
    goal: str
    plan: PlanDAG = Field(default_factory=PlanDAG)
    step_results: dict[str, Any] = Field(default_factory=dict)
    artifacts: dict[str, str] = Field(default_factory=dict)  # id -> URI
    critiques: dict[str, list[str]] = Field(default_factory=dict)
    budget: Budget = Field(default_factory=Budget)
