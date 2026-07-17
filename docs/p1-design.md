# P1 design — agent + HITL gate

Working design document for Phase 1. Every decision below is made by the owner in the design
workshop (options + tradeoffs discussed, choice recorded with rationale) **before the code
that depends on it is written**. Stage A (standalone LangGraph study) was skipped by owner
preference — learning folds into the implementation stages, taught at point of contact.

**P1 stage map** (each stage = one checkpoint PR; this doc is PR-1):

| Stage | PR branch | Deliverable |
|---|---|---|
| B | `p1/design` | this document, all decisions ratified |
| C | `p1/trajectory-schema` | schema doc + validator + planted-defect tests (D11: precedes agent code; freezes before P2) |
| D | `p1/compat-layer` | provider module: env-driven DeepSeek/OpenAI, output validation + one retry + visible degradation |
| E | `p1/graph-skeleton` | graph wired end-to-end with deterministic tool stubs, no LLM — emits a schema-valid trajectory |
| F | `p1/llm-nodes` | extraction + per-dimension assessment prompts (evidence spans mandatory), first real trajectories |
| G | `p1/gate` | gate triggers + both D15 modes (interactive interrupt/resume · eval auto-resume) |
| H | `p1/p1-report` | phase report: graph diagram, gate rationale, annotated trajectories, malformed-output results |

---

## Decisions

### 1. Graph shape (nodes and edges) — DECIDED (owner, 2026-07-17: option A)

```
parse → extract → assess ⟲ (conditional edge, once per dimension) → aggregate → gate → recommend
```

One `assess` node executed sequentially per dimension via a conditional edge over a
dimensions-remaining cursor; **fixed order with hard_requirements last** (it re-reads the
other dimensions' determinations — the rubric itself forces sequential). Alternatives
recorded: parallel fan-out (Send API) rejected — nondeterministic event ordering pollutes
trajectory replay and pass^k comparison, and the hard_requirements dependency forces a hybrid
anyway; single mega-call rejected — destroys per-dimension trajectory granularity, which is
the eval's protagonist. Rationale: trajectory legibility and deterministic replay outrank
wall-clock at n=30.

### 2. State schema — DECIDED (owner, 2026-07-17)

`TypedDict` state: identity/config (pair ref, mode, rubric_version) · documents by value
(resume_text, jd_text) · working products (extraction, dimensions_remaining cursor,
assessments dict under a merge reducer) · downstream (aggregate, gate, recommendation).

- **2a — documents by value.** An interrupted run is hermetic, and the deeper purchase is
  **pass^k internal validity**: with by-reference inputs, k runs could straddle a re-download/
  re-normalization of the raw files, making score drift unattributable (model instability vs
  input change). By-value freezes the input in state so pass^k variance attributes to model
  behavior only. Recorded boundary (owner L3): if inputs outgrow a few KB (e.g. PDFs),
  switch to content-hash-in-state + content-addressed storage — hash preserves hermeticity,
  storage handles size. Not needed at current scale.
- **2b — assessments under a merge reducer**, each assess pass returning only its own
  `{dimension: result}`. Key-conflict semantics: the default (dict-union, right wins) is a
  **silent overwrite** — it would mask assess-loop cursor bugs and disarm the
  exactly-once-per-dimension invariant. Owner leaning, to be finalized when the reducer is
  written in Stage E: **raise on existing key** ("blow up in development rather than pollute
  a trajectory"), with a defined carve-out for legitimate rewrites (retry after
  malformed output). Decision + rationale to be logged when implemented.
- **2c — TypedDict over dataclasses.** Framework idiom beats object aesthetics; principle on
  record: a "better design" that fights the framework's data model is not a better design.
- **Trajectory events stay OUT of state** (logger-side, append-only, written as events
  happen): the trajectory is observational evidence and evidence must not depend on the
  observed party surviving — a crashed run keeps its trajectory up to the crash, which is
  exactly what the P2 error-recovery scorer needs.

### 3. Tool surface — architecture DECIDED (owner, 2026-07-17: option C); signatures pending below

**Graph-orchestrated scheduling + LLM structured output through function calling.** The graph
(decision 1's topology) decides when tools run; `assess_dimension`/`submit_assessment` are
exposed to the model as schema-enforced function calls — the model must return each
assessment AS a `submit_assessment(...)` call with `evidence_spans` required.

Pinned rationale:
- **Rejecting model-driven scheduling (option A) reapplies decision 1's principle** — eval
  measurability constrains agent freedom: monotonic-seq schema rejected parallel fan-out;
  contract-execution scorers reject free scheduling. Giving the model "control" over a flow
  with no branch points is **fake agency** — freedom the task cannot use, returned as noise.
- **Over plain orchestration (option B): tool calling is redefined as the output contract's
  enforcement mechanism.** Provider function-calling makes the schema structural:
  `evidence_spans: required` upgrades D7 (mandatory evidence citation) from a prompt-level
  request the model can ignore to an API-level guarantee it cannot — mechanism over
  instruction.
- **Agency allocation rule (owner):** where the flow has no choice, the graph owns it; where
  the output is non-enumerable judgment (per-dimension evidence assessment), the model owns
  it. If the task later grows a real branch (e.g. autonomous evidence supplementation), a
  model-routed conditional edge is added — the architecture does not change.

### 4. Trajectory event types + invariants — PENDING

### 5. Gate triggers + initial thresholds — PENDING
Design input on record: finding 004 — gate ground truth is 29/30 positive on the reference
set (veto fires 24/30); thresholds must be chosen knowing this base rate.

### 6. Checkpointer + two-mode wiring (D15) — PENDING

### 7. Provider compatibility + degradation policy (D3) — PENDING
