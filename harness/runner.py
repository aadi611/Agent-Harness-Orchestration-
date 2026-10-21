"""Core loop (see README). Wires planner, scheduler, verifier, router, budget, checkpoint."""
from __future__ import annotations

from harness import planner
from harness.checkpoint import InMemoryCheckpointer
from harness.executor import execute
from harness.router import Action, LoopDetector, route
from harness.scheduler import run_frontier
from harness.state import State
from harness.verifier import run_gates
from harness.workflow import Workflow


async def run(goal: str, wf: Workflow, run_id: str = "local") -> State:
    state = State(goal=goal, budget=wf.budget.model_copy())
    ckpt = InMemoryCheckpointer()
    loops = LoopDetector()
    state.plan = await planner.plan(state)

    while not state.plan.done and state.budget.ok():
        for step, out in await run_frontier(state.plan, execute):
            verdict = run_gates(out)  # TODO: then LLM judge
            action = route(verdict)
            if action is Action.ACCEPT:
                state.step_results[step.id] = out
                state.plan.mark_done(step.id)
            elif loops.check(step.id, step.args, verdict.error or verdict.critique):
                return state  # TODO: escalate to human
            elif action is Action.REPLAN_SUBTREE:
                state.budget.record_replan()
                state.plan = await planner.plan(state, replace=state.plan.subtree(step.id))
            # RETRY_STEP / RERUN_STEP: step stays pending and is picked up next frontier
        ckpt.save(run_id, state)
    return state
