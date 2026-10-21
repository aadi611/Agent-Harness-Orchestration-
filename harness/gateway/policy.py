"""Policy in code, not prompts: authz, rate limits, side-effect rules."""
from __future__ import annotations

from harness.gateway.approval import ApprovalRequired, is_approved
from harness.state import Step


def authorize(step: Step) -> None:
    """Read-only tools run freely; side_effect tools require approval (default deny)."""
    if step.side_effect and not is_approved(step.id):
        raise ApprovalRequired(step.id)
