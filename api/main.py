"""FastAPI: POST /runs, GET /runs/{id}, SSE stream at /runs/{id}/events."""
from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Agent Harness")
_runs: dict[str, dict] = {}


class RunRequest(BaseModel):
    workflow: str
    goal: str


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/runs", status_code=202)
async def create_run(req: RunRequest) -> dict[str, str]:
    run_id = uuid.uuid4().hex
    _runs[run_id] = {"workflow": req.workflow, "goal": req.goal, "status": "queued"}
    # TODO: load workflow, schedule harness.runner.run in the background.
    return {"run_id": run_id}


@app.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict:
    if run_id not in _runs:
        raise HTTPException(404, "run not found")
    return {"run_id": run_id, **_runs[run_id]}
