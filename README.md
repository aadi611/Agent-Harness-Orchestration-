Target architecture
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

Key optimizations

1. Plan as a DAG, execute with a scheduler

The Planner returns steps[] with id, deps, tool, args, acceptance_criteria and side_effect: bool.
The scheduler runs all steps whose deps are satisfied concurrently, which typically cuts latency 2-4x on research-style flows.

2. Two-tier verification (cheap first)

Deterministic gates: JSON schema, citation URL resolves, quoted span exists in the source, unit tests pass, numbers recompute.
LLM judge, only if the gates pass, on a different model family, scoring against each step’s acceptance_criteria.

This keeps most failures from ever reaching an LLM call, and “grounded” becomes a checkable claim instead of an opinion.

3. Failure taxonomy, not a blanket retry

Failure	Action	Cost
Timeout or 5xx	Same call, exponential backoff + jitter, max 3	~0
Schema invalid	Re-prompt the step with the validator error	Low
Ungrounded output	Re-run the step with the critic’s feedback	Medium
Wrong approach	Replan only the affected subtree	High
Budget exhausted or repeated identical failure	Escalate to a human	Stops the bleed

Add loop detection by hashing (step, args, error). The same hash twice means don’t retry.

4. Model routing

Strong model: Planner and Critic.
Mid model: Executor reasoning steps and the reporter.
Small model: routing, classification, extraction, formatting.
This usually cuts cost 50-70% with no quality loss on the cheap steps.

5. Context and memory

Short-term: typed state (goal, plan, step_results, artifacts, critiques, budget). Nodes read only what they declare.
Large outputs go to an artifact store; state holds a URI and a 2-line summary.
Long-term: vector store plus a key-value store of facts, written only after verification passes, so memory isn’t polluted by unverified output.
Compact when context exceeds about 60% of the window.

6. Durability

Checkpoint after every node (Postgres). Any run can resume, replay or fork from a step.
Every tool call carries an idempotency key, so retries never double-fire side effects.

7. Guardrails and human approval

Policy lives in the tool gateway, not in prompts, and is enforced in code.
Read-only tools run freely. side_effect: true tools require approval, via LangGraph interrupt(), an async approval queue, or a timeout that defaults to deny.
Input and output PII and injection scan. Tool results are tagged as untrusted data, never as instructions.

8. Observability and cost

One OpenTelemetry trace per run; one span per node and per tool call, with attributes for tokens in/out, model, cost, retries and verdict.
Per-run cost ledger enforces budgets live and feeds a dashboard of cost per successful task.
Golden-set evals run in CI on every prompt or graph change.

9. Caching

Prompt caching for the stable prefix (system prompt, tool schemas).
Tool-result cache keyed by hash(tool, args) with a TTL.
Plan cache for recurring task templates.
