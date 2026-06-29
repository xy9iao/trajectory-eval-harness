# Trajectory-Level Reliability Evaluation for Stateful LLM Agents

A production-style **consumer support/abuse triage agent** built on **LangGraph**, wrapped in a
**trajectory-level evaluation & reliability harness**. The agent classifies an incoming user
issue, gathers context through **MCP** tools, decides on an action, and **pauses at a
human-in-the-loop (HITL) gate** before any consequential action (refund / ban / escalate).
The harness then measures not just *whether the final answer was right*, but *how the agent got
there*: tool-call correctness, gate integrity, recovery after errors, and **pass^k reliability**.

> **Why this exists.** Most agent demos score the last message and call it done. For a stateful
> LangGraph agent, the interesting failures live in the intermediate state — a router taking the
> expensive branch, a retry loop that never recovers, a consequential action that slipped past the
> gate. This project builds the agent *and* the instrument that catches those failures.

---

## The two layers

| Layer | What it is | Why it's here |
|---|---|---|
| **Product layer** — the agent | A LangGraph state machine: `classify → gather_context → decide_action → [HITL gate] → execute`, tools via MCP, checkpointed state | Gives a real, demoable system. Exercises routing, tool use, error recovery, and a HITL interrupt. |
| **Eval layer** — the harness | Trajectory extraction + scorers (gate integrity, tool-call correctness, recovery, efficiency, loop detection) + `pass@k`/`pass^k` reliability + failure clustering + a report | The differentiating, "RA-worthy" core. Methodology you design and own, not a tutorial you followed. |

**The differentiator is action + gate, not answer retrieval.** This is deliberately *not* a RAG
Q&A bot. The agent *decides and acts under a safety gate*; the harness measures whether it does so
*correctly and reliably*.

---

## Build plan (phased)

Each phase ends in something runnable. Implement in order; do not start a phase before the
previous one's deliverable runs.

### Phase 0 — Scaffold & smoke test
- Set up env, dependencies, repo structure.
- Get a trivial 2-node LangGraph running end-to-end against the cloud API.
- **Deliverable:** `python scripts/run_agent.py --smoke` prints a model response through the graph.

### Phase 1 — The triage agent (product layer)
- Typed state (`src/agent/state.py`).
- Nodes: `classify`, `gather_context`, `decide_action`, `gate`, `execute` (`src/agent/nodes.py`).
- MCP server exposing mock tools — `get_account`, `get_order`, `get_ticket_history`, `get_policy` (`src/mcp/server.py`) — and the agent wired as an MCP client (`src/agent/tools.py`).
- Checkpointer (in-memory → SQLite) and a **HITL interrupt at the gate**; resume on approve/reject.
- **Deliverable:** `python scripts/run_agent.py --case refund_double_charge` runs a full triage, pauses at the gate, and completes after a simulated human decision.

### Phase 2 — The eval dataset (RA core, part 1)
- Dataset schema + loader + validation (`src/eval/dataset.py`).
- Hand-build **30–50 labeled cases** spanning categories + adversarial/edge cases (`data/eval_set.jsonl`).
- Ground truth per case: expected category, expected action, `gate_required` flag, expected tool calls.
- **Deliverable:** `python scripts/run_eval.py --stats` prints dataset coverage by category/difficulty.

### Phase 3 — The eval harness (RA core, part 2) — *the differentiator*
- Trajectory extraction from graph execution — nodes visited, tool calls + args, per-step state, errors, recovery (`src/eval/trajectory.py`).
- Scorers (`src/eval/scorers.py`): final-answer, classification accuracy, action correctness, **gate integrity**, tool-call correctness, step efficiency, loop detection, recovery rate.
- Reliability (`src/eval/reliability.py`): `pass@k` and `pass^k` over k runs/case; the *reliability gap*.
- State-machine checks: routing determinism + reducer determinism under fixed (mocked) LLM outputs.
- **Deliverable:** `python scripts/run_eval.py --k 5` produces a full metrics table.

### Phase 4 — Analysis, report & (stretch) dashboard
- Failure clustering by mode (`src/eval/report.py`).
- A written report with metrics + findings — the artifact that backs the RA title (`reports/REPORT.md`).
- **Stretch:** HTML trace dashboard or LangSmith integration.
- **Deliverable:** `reports/REPORT.md` filled with real numbers and 3–5 concrete findings.

---

## Quickstart

```bash
# 1. Python 3.11+ recommended
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure your cloud model provider
cp .env.example .env
# edit .env: set ANTHROPIC_API_KEY (or OPENAI_API_KEY) and MODEL

# 3. Smoke test (Phase 0)
python scripts/run_agent.py --smoke

# 4. Run one triage case (Phase 1+)
python scripts/run_agent.py --case refund_double_charge

# 5. Run the eval harness (Phase 3+)
python scripts/run_eval.py --k 5
```

---

## Repo layout

```
triage-agent-eval/
├── README.md                 # this file — plan, phases, quickstart
├── GUIDE.md                  # deep design + eval methodology (read this)
├── requirements.txt
├── .env.example
├── src/
│   ├── config.py             # model + paths config
│   ├── agent/
│   │   ├── state.py          # TypedDict state + reducers
│   │   ├── graph.py          # StateGraph: nodes, edges, gate interrupt, checkpointer
│   │   ├── nodes.py          # node implementations
│   │   ├── tools.py          # MCP client wiring → LangGraph tools
│   │   └── prompts.py        # prompt templates
│   ├── mcp/
│   │   └── server.py         # minimal MCP server w/ mock tools
│   └── eval/
│       ├── dataset.py        # case schema + loader
│       ├── trajectory.py     # extract trajectory from a graph run
│       ├── scorers.py        # the metrics
│       ├── reliability.py    # pass@k / pass^k
│       ├── runner.py         # orchestrates eval over the dataset
│       └── report.py         # failure clustering + report generation
├── data/
│   └── eval_set.jsonl        # hand-built labeled cases
├── scripts/
│   ├── run_agent.py          # run the agent (demo / single case)
│   └── run_eval.py           # run the harness
├── reports/
│   └── REPORT.md             # the RA artifact (filled in Phase 4)
└── tests/
    └── test_smoke.py
```

---

## Résumé bullets this unlocks

Use these *after* you have real numbers from Phase 3–4. Keep them metric-led.

- Built a **trajectory-level evaluation harness** for a LangGraph triage agent, scoring tool-call
  correctness, error-recovery rate, and **pass^k reliability** across a 50-case labeled suite —
  surfacing N classes of silent state-machine failures invisible to final-answer scoring.
- Designed a **human-in-the-loop safety gate** for consequential actions (refund/ban/escalate) and
  a **gate-integrity metric** verifying 0 unauthorized auto-executions, including under adversarial
  prompt-injection cases.
- Integrated agent tools over **MCP**, decoupling the tool layer from the orchestration layer and
  enabling tool reuse across runs.

---

## Things to keep straight (so you can defend it)

- **You own the methodology.** The metric definitions, the dataset design, and the `pass@k` vs
  `pass^k` choice are the soul of the project — and exactly what an interviewer will probe. If you
  used Claude Code to implement, you still must be able to re-derive each decision on a whiteboard.
- **The framework is the vehicle, the concepts are the cargo.** LangGraph here is chosen because it
  exposes the state machine explicitly (which the harness needs to instrument). The same patterns
  map onto ADK / Strands / OpenAI Agents SDK / internal frameworks.
- See `GUIDE.md` for the full rationale behind every design decision.
