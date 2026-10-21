"""Tier 2: LLM judge on a different model family. Stubbed for now."""
from __future__ import annotations

from typing import Any

from harness.router import Verdict


async def judge(output: Any, acceptance_criteria: list[str]) -> Verdict:
    """Score output against acceptance_criteria. Runs only if tier-1 gates pass.

    TODO: call STRONG_ALT tier via ModelRouter.judge_for(producer).
    """
    raise NotImplementedError("LLM judge not wired up yet")
