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

### 1. Graph shape (nodes and edges) — PENDING

### 2. State schema — PENDING

### 3. Tool surface (6 locked names: parse_resume, parse_jd, get_rubric, assess_dimension, submit_assessment, flag_for_review) — signatures PENDING

### 4. Trajectory event types + invariants — PENDING

### 5. Gate triggers + initial thresholds — PENDING
Design input on record: finding 004 — gate ground truth is 29/30 positive on the reference
set (veto fires 24/30); thresholds must be chosen knowing this base rate.

### 6. Checkpointer + two-mode wiring (D15) — PENDING

### 7. Provider compatibility + degradation policy (D3) — PENDING
