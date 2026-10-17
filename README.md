# Agent Harness & Multi-Agent Workflow Orchestrator
---
A durable, policy-enforced runtime for multi-agent workflows. Think Airflow + LangGraph for AI agents: workflows are declared in YAML, compiled into a DAG, executed by a scheduler, and verified by a two-tier critic before anything is returned.
---

## Why this exists

Most agent loops are a single LLM calling tools in a `while` loop. They fail in predictable ways: unbounded retries, self-graded output, full-history context bloat, side effects firing twice, and no way to see what a run cost. This harness fixes those at the architecture level rather than with prompts.

| Problem | Design response |
|---|---|
| Harness and orchestrator treated as separate systems | One durable graph runtime; workflows are config on top |
| Every role is an LLM | Only Planner and Critic use an LLM; Executor is deterministic code |
| Any failure replans everything | Typed failure routing (retry tool / re-run step / replan subtree) |
| Model grades its own work | Deterministic gates first, then a judge from a different model family |
| Linear plans | Planner emits a DAG; independent steps run in parallel |
| Unbounded loops and spend | Hard budgets: tokens, USD, wall-clock, replans |
| Full history to every agent | Typed shared state; nodes read only declared slices |

---

## Architecture

```
                 ┌────────────── Control Plane ──────────────┐
                 │ Policy engine · Budgets · HITL gates      │
                 │ Model router · Cost ledger · Tracing      │
                 └──────────────────────┬────────────────────┘
                                        │
START → PLAN(DAG) → SCHEDULER ─┬─ step A ─┐
                               ├─ step B ─┼→ VERIFY → ROUTE
                               └─ step C ─┘             │
                                    ▲                   ├─ pass      → SYNTHESIZE → END
                                    │                   ├─ tool_err  → retry step (backoff)
                                    │                   ├─ bad_out   → re-run step w/ critique
                                    └───────────────────┴─ bad_plan  → replan subtree only
                                        (budget exhausted → ESCALATE to human)

            Tool/MCP Gateway: schema validation · authz · rate limit · cache · audit
                    APIs            DBs            Search / Retrieval
```

### Components

- **Planner** (strong LLM): turns a goal into a `PlanDAG` of steps with `id`, `deps`, `tool`, `args`, `acceptance_criteria`, `side_effect`.
- **Scheduler**: runs every step whose dependencies are satisfied, concurrently.
- **Executor** (deterministic): performs tool calls from the plan; reasoning steps call a mid-tier model.
- **Verifier**: tier 1 deterministic gates, tier 2 LLM judge on a different model family.
- **Failure Router**: maps verdicts to the cheapest correct recovery action.
- **Tool/MCP Gateway**: the single choke point for schema validation, authorization, rate limiting, caching, approval and audit.
- **Control Plane**: budgets, model routing, cost ledger, tracing.

---

## Failure taxonomy

| Failure | Action | Cost |
|---|---|---|
| Timeout / 5xx | Same call, exponential backoff + jitter, max 3 | ~0 |
| Schema invalid | Re-prompt step with validator error | Low |
| Ungrounded output | Re-run step with critic feedback | Medium |
| Wrong approach | Replan affected subtree only | High |
| Budget exhausted / repeated identical failure | Escalate to human | Stops the bleed |

**Loop detection:** hash `(step_id, args, error)`. The same hash seen twice means no further retry.

---

## Verification (two tiers)

1. **Deterministic gates** (cheap, run first)
   - JSON schema validation
   - Cited URLs resolve
   - Quoted spans exist in the source
   - Unit tests pass
   - Numeric claims recompute
2. **LLM judge** (only if gates pass)
   - Different model family from the producer
   - Scores against each step's `acceptance_criteria`

"Grounded" becomes a checkable claim rather than an opinion.

---

## Model routing

| Tier | Used for |
|---|---|
| `strong` | Planner, Critic |
| `strong_alt` | Judge (different family from producer) |
| `mid` | Analysis, coding, reporting |
| `small` | Routing, classification, extraction, formatting |

Expected effect: 50-70% lower cost with no quality loss on the cheap steps.

---

## Context and memory

- **Short-term:** typed state `{goal, plan, step_results, artifacts, critiques, budget}`. Each node declares which keys it reads.
- **Artifacts:** large outputs go to an artifact store; state keeps a URI and a short summary.
- **Long-term:** vector store + key-value facts, written **only after verification passes**.
- **Compaction:** triggered when context exceeds ~60% of the window.

---

## Durability

- Checkpoint after every node (Postgres). Runs can resume, replay, or fork from any step.
- Every tool call carries an **idempotency key**, so retries never double-fire side effects.

---

## Guardrails and human approval

- Policy is enforced **in the gateway, in code**, not in prompts.
- Read-only tools run freely. Tools marked `side_effect: true` require approval.
- Approval mechanisms: LangGraph `interrupt()` or an async approval queue. Timeout default is **deny**.
- PII and prompt-injection scanning on input and output.
- Tool results are tagged as untrusted data and never treated as instructions.

---

## Observability and cost

- One OpenTelemetry trace per run; one span per node and per tool call.
- Span attributes: model, tokens in/out, cost, retries, verdict.
- Live per-run cost ledger enforces budgets.
- Dashboard metric: **cost per successful task**.
- Golden-set evals run in CI on every prompt or graph change.

---

## Caching

- **Prompt cache:** stable prefix (system prompt, tool schemas).
- **Tool-result cache:** key `hash(tool, args)` with TTL.
- **Plan cache:** recurring task templates.

---

## Workflow spec

```yaml
workflow: market_research_report
budget: { max_usd: 2.00, max_tokens: 400k, max_seconds: 300, max_replans: 2 }
nodes:
  planner:    { model: strong, output: PlanDAG }
  researcher: { model: small,  tools: [search, fetch], parallel: 5, cache_ttl: 1h }
  analyst:    { model: mid,    deps: [researcher] }
  coder:      { model: mid,    tools: [sandbox], gate: tests_pass, deps: [analyst] }
  reviewer:   { model: strong_alt, checks: [schema, citations, recompute, rubric] }
  reporter:   { model: mid,    deps: [reviewer] }
edges:
  reviewer:
    pass: reporter
    tool_error: retry_step
    bad_output: rerun_step
    bad_plan: planner(subtree)
    budget_exhausted: human
approvals: { side_effect_tools: required, timeout_action: deny }
```

---

## Core loop

```python
async def run(goal, wf):
    state = State(goal=goal, budget=wf.budget)
    plan = await planner(state)
    while not plan.done and state.budget.ok():
        ready = plan.ready_steps()                         # DAG frontier
        for step in ready:
            gateway.authorize(step)                        # policy + HITL
        results = await gather(*(execute(s, state) for s in ready))
        for step, out in results:
            verdict = verify(step, out)                    # deterministic -> LLM judge
            match verdict.kind:
                case "pass":       plan.mark_done(step, out)
                case "tool_error": plan.retry(step, backoff=True)
                case "bad_output": plan.rerun(step, feedback=verdict.critique)
                case "bad_plan":   plan = await planner(state, replace=plan.subtree(step))
            if state.loop_detected(step, verdict):
                return escalate(state)
        state.checkpoint()
    return await reporter(state)
```

---

## Suggested stack

| Concern | Choice |
|---|---|
| Graph runtime + checkpointer | LangGraph |
| Run API + streaming | FastAPI (SSE) |
| Checkpoints + cost ledger | Postgres |
| Vector memory | pgvector (or any vector DB) |
| Tracing | OpenTelemetry + Langfuse |
| Tool layer | MCP gateway |
| Artifact store | S3 / Azure Blob |
| Validation | Pydantic |

---

## Proposed repo layout

```
agent-harness/
├── README.md
├── pyproject.toml
├── workflows/
│   └── market_research_report.yaml
├── harness/
│   ├── state.py          # typed State, PlanDAG, Step models
│   ├── planner.py
│   ├── scheduler.py      # DAG frontier + concurrency
│   ├── executor.py
│   ├── verifier/
│   │   ├── gates.py      # schema, citations, recompute, tests
│   │   └── judge.py
│   ├── router.py         # failure taxonomy + loop detection
│   ├── budget.py         # token / USD / time / replan limits
│   ├── models.py         # model router
│   ├── memory.py         # short-term, long-term, compaction
│   ├── gateway/
│   │   ├── policy.py     # authz, rate limit, side-effect rules
│   │   ├── approval.py   # HITL queue
│   │   └── mcp.py
│   ├── checkpoint.py
│   └── telemetry.py      # OTel spans, cost ledger
├── api/
│   └── main.py           # FastAPI: POST /runs, GET /runs/{id}, SSE stream
├── evals/
│   └── golden/           # golden-set tasks run in CI
└── tests/
```

---

## Build order

1. State schema, tool gateway, checkpointing (foundation)
2. Planner, DAG scheduler, deterministic verifier
3. Failure router, budgets, loop detection
4. LLM critic, model router, caching
5. OTel tracing, cost ledger, eval harness
6. Human-approval UI

---

## Quickstart (target interface)

```bash
pip install -e .
export DATABASE_URL=postgresql://...
export OTEL_EXPORTER_OTLP_ENDPOINT=...

uvicorn api.main:app --reload

curl -X POST localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"workflow": "market_research_report", "goal": "Compare EU vs US AI regulation"}'

curl -N localhost:8000/runs/<run_id>/events    # SSE stream
```

---

## Design principles

1. Deterministic where possible, LLM only where judgment is needed.
2. Cheapest correct recovery action first.
3. Policy in code, never in prompts.
4. Every run is resumable, replayable and auditable.
5. Memory is written only after verification.
6. Every run has a hard budget and an escape hatch to a human.

---

## Status

Design stage. Next milestone: foundation layer (state, gateway, checkpointing) with one working example workflow.
