"""Load a YAML workflow spec."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from harness.budget import Budget


class Workflow(BaseModel):
    workflow: str
    budget: Budget = Budget()
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, str]] = {}
    approvals: dict[str, str] = {}


def load_workflow(path: str | Path) -> Workflow:
    return Workflow.model_validate(yaml.safe_load(Path(path).read_text()))
