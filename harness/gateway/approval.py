"""Human-in-the-loop approval queue. Timeout default is deny."""
from __future__ import annotations


class ApprovalRequired(Exception):
    def __init__(self, step_id: str) -> None:
        super().__init__(f"step {step_id!r} requires human approval")
        self.step_id = step_id


_approved: set[str] = set()


def approve(step_id: str) -> None:
    _approved.add(step_id)


def is_approved(step_id: str) -> bool:
    return step_id in _approved
