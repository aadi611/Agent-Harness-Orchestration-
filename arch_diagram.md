# Agent Harness: Architecture Diagram

A durable, policy-enforced runtime for multi-agent workflows. Workflows are declared in YAML, compiled into a DAG, executed by a scheduler, and verified by a two-tier critic before anything is returned.

## 1. System overview

```mermaid
flowchart TB
    subgraph CP["Control Plane"]
        direction LR
        POL["Policy engine"]
        BUD["Budgets"]
        HITL["HITL gates"]
        MR["Model router"]
        COST["Cost ledger"]
        TR["Tracing (OTel)"]
    end

    START(["START"]) --> PLAN["Planner (strong LLM)<br/>goal to PlanDAG"]
    PLAN --> SCH["Scheduler<br/>DAG frontier, concurrent"]

    SCH --> A["Step A"]
    SCH --> B["Step B"]
    SCH --> C["Step C"]

    A --> VER
    B --> VER
    C --> VER

    subgraph VERIFY["Verifier (two tiers)"]
        direction TB
        VER["Tier 1: deterministic gates<br/>schema, URLs, quotes, tests, recompute"]
        JUDGE["Tier 2: LLM judge<br/>different model family"]
        VER --> JUDGE
    end

    JUDGE --> ROUTE{"Failure router"}

    ROUTE -- "pass" --> SYN["Synthesize / Reporter"]
    SYN --> END(["END"])
    ROUTE -- "tool_error: retry with backoff" --> SCH
    ROUTE -- "bad_output: re-run with critique" --> SCH
    ROUTE -- "bad_plan: replan subtree only" --> PLAN
    ROUTE -- "budget exhausted / repeated failure" --> HUMAN["Escalate to human"]

    CP -.governs.- SCH

    subgraph GW["Tool / MCP Gateway"]
        direction LR
        G1["Schema validation"]
        G2["Authz"]
        G3["Rate limit"]
        G4["Cache"]
        G5["Approval"]
        G6["Audit"]
    end

    A --> GW
    B --> GW
    C --> GW

    GW --> APIS["APIs"]
    GW --> DBS["DBs"]
    GW --> SRCH["Search / Retrieval"]
```

## 2. Core loop (arc view)

Components on one line; each arc is a handoff. `->` marks direction.

```text
CORE LOOP
  Planner -> Scheduler -> Executor -> Verifier -> Router
  Router -> Scheduler   (retry step / re-run with critique)
  Router -> Planner     (replan subtree)
  Executor -> Gateway   (every tool call)

SUPPORT LAYER
  Budget     -> Planner      (limits on replans)
  Budget     -> Router       (exhaustion escalates to human)
  Checkpoint -> Scheduler    (resume, replay, fork)
  Verifier   -> Memory       (write only after pass)
  Gateway    -> Telemetry    (audit, spans, cost)
```

```mermaid
flowchart LR
    P[Planner] --> S[Scheduler] --> E[Executor] --> V[Verifier] --> R[Router]
    R -- retry / rerun --> S
    R -- replan --> P
    E --> GWY[Gateway]
    BUD[Budget] -.-> P
    BUD -.-> R
    CK[Checkpoint] -.-> S
    V -.-> MEM[Memory]
    GWY -.-> TEL[Telemetry]
```

## 3. Failure routing

```mermaid
flowchart LR
    F{"Verdict"} -->|"Timeout / 5xx"| R1["Same call, backoff + jitter, max 3<br/>cost: ~0"]
    F -->|"Schema invalid"| R2["Re-prompt step with validator error<br/>cost: low"]
    F -->|"Ungrounded output"| R3["Re-run step with critic feedback<br/>cost: medium"]
    F -->|"Wrong approach"| R4["Replan affected subtree only<br/>cost: high"]
    F -->|"Budget exhausted / same hash twice"| R5["Escalate to human<br/>stops the bleed"]
```

Loop detection: hash `(step_id, args, error)`. The same hash seen twice means no further retry.

## 4. Model routing

| Tier | Used for |
|---|---|
| strong | Planner, Critic |
| strong_alt | Judge (different family from producer) |
| mid | Analysis, coding, reporting |
| small | Routing, classification, extraction, formatting |

## 5. Deployment stack

```mermaid
flowchart TB
    CLIENT["Client"] -->|"POST /runs, GET /runs/{id}, SSE"| API["FastAPI"]
    API --> RT["LangGraph runtime"]
    RT --> PG[("Postgres<br/>checkpoints + cost ledger")]
    RT --> VEC[("pgvector<br/>long-term memory")]
    RT --> ART[("S3 / Azure Blob<br/>artifact store")]
    RT --> MCP["MCP gateway"]
    RT --> OTEL["OpenTelemetry + Langfuse"]
    MCP --> EXT["APIs / DBs / Search"]
```

## 6. Repo layout

```text
agent-harness/
├── README.md
├── pyproject.toml
├── workflows/        market_research_report.yaml
├── harness/
│   ├── state.py      typed State, PlanDAG, Step
│   ├── planner.py
│   ├── scheduler.py
│   ├── executor.py
│   ├── verifier/     gates.py, judge.py
│   ├── router.py     failure taxonomy + loop detection
│   ├── budget.py
│   ├── models.py     model router
│   ├── memory.py
│   ├── gateway/      policy.py, approval.py, mcp.py
│   ├── checkpoint.py
│   └── telemetry.py
├── api/main.py
├── evals/golden/
└── tests/
```

## 7. Build order

1. State schema, tool gateway, checkpointing
2. Planner, DAG scheduler, deterministic verifier
3. Failure router, budgets, loop detection
4. LLM critic, model router, caching
5. OTel tracing, cost ledger, eval harness
6. Human-approval UI
