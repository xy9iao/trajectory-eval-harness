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
  malformed output).
  **SUPERSEDED at Stage E (owner ruling, 2026-07-17): strict raise, NO carve-out.**
  Implementation exposed the structural fact: retries live inside `assess_dimension`
  (client layer, decision 7), so one dimension pass produces exactly one state write —
  "legitimate duplicate write" is a category with no members at the state layer; any
  duplicate reaching the reducer is a bug (cursor stalled, loop misrouted). The
  legitimate-rewrite concept sinks to the layer it belongs to: trajectory invariant 6.
  The two layers' contracts are now independent and each stronger — no cross-layer
  reference. Direction matters: design→implementation TIGHTENED the contract
  (loosening would be decay; tightening is health). Reserving today's hole for a
  hypothetical future architecture change is exactly the error being deleted — if retry
  logic ever leaves the client layer, that is an architecture change and the reducer's
  contract gets renegotiated then, not pre-weakened now.
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

**Signatures (ratified 2026-07-17):**

| tool | caller | signature | trajectory args_summary (dataset-text-free) |
|---|---|---|---|
| `parse_resume` | parse node | `(pair: PairRef) -> str` | `{split, row}` |
| `parse_jd` | parse node | `(pair: PairRef) -> str` | `{split, row}` |
| `get_rubric` | assess node, once per dimension | `(dimension: str) -> RubricSlice` | `{dimension}` |
| `assess_dimension` | assess node (issues the llm_call) | `(dimension, extraction, rubric_slice, resume_text, jd_text) -> Assessment` | `{dimension, attempt}` |
| `submit_assessment` | the MODEL (forced function call) | schema: `{dimension, score 0-5, evidence_quotes: required ≥1 verbatim, determinations (skills only), notes}` | validation ok/malformed → llm_call.status |
| `flag_for_review` | gate node | `(triggers, assessments, aggregate) -> GateOutcome` | `{triggers, mode, action}` |

Sub-decisions, ratified:

- **3-i — what counts as a "tool" (criterion on record):** the tool list is the GRAPH'S
  orchestration contract (what P2's tool-call correctness scorer asserts against), not a
  registry of every function-calling use. Extraction's schema rides the same
  function-calling mechanism but is the extract node's internal output contract — same
  mechanism, different contract tier. `parse_resume`/`parse_jd` stay separate: P2's error
  recovery scorer needs single-sided-failure granularity (garbled resume + intact JD must be
  two distinguishable parse events) — the fourth instance of eval needs determining
  interface design (after: no parallel fan-out, no free scheduling, by-value state).
- **3-ii — malformed output escalates, never drowns:** `assess_dimension` retries once
  (D3's one-retry-visible-degradation lands here); second failure → Assessment marked
  degraded with `score: null` → `insufficient_evidence` auto-triggers the gate (D15).
  Degraded dimensions contribute NO score; `aggregate.weighted_mean` is **null** when any
  scoring dimension is degraded (a partially-computed mean looks complete downstream; null
  forces consumers to check the `partial` flag) with missing dimensions listed. The gate
  thus guards three classes: boundary scores, evidence divergence, and degradation of the
  assessment process itself (the system's meta-state is a gating condition).
- **Evidence as verbatim quotes, offsets resolved tool-side:** models are unreliable at
  character-offset arithmetic, so `submit_assessment` takes verbatim quotes;
  `assess_dimension` resolves each quote to raw offsets via deterministic search
  (`corpus.find_offsets`); an unresolvable quote = the quote does not exist in the document
  = validation failure → malformed path. Side effect: fabricated evidence is structurally
  unable to pass (a hallucinated quote fails resolution) — D7 upgraded from spot-check to
  mechanism. Raw `resume_text`/`jd_text` are in the signature BECAUSE quote resolution
  requires them (docstring must say so — do not "optimize" them away); prompt layout puts
  invariant content (docs + extraction) in a shared prefix and per-dimension content in the
  suffix, so provider prefix caching amortizes the raw-doc cost across the four assess calls.

### 4. Trajectory event types + invariants — DECIDED (owner, 2026-07-17: schema v0.2)

Base: the v0.1 draft (closed PR #6), revised under decisions 1–3 and owner review. Full spec
lands in `docs/trajectory-schema.md` (Stage C / PR-2); binding deltas and additions:

**Seven event types** (unchanged): `run_start / llm_call / tool_call / dimension_assessed /
gate_event / error / run_end`.

**Join keys explicit in `run_start`** (owner check): `pair{split,row} · provider · model ·
rubric_version · config_digest · agent_mode · schema_version` — the scorer consumption map
starts here: pass^k joins on (pair, provider, model, config_digest); agreement joins pair →
`labels-v1.jsonl`; the cross-model table groups by (provider, model).

**Revisions vs v0.1:**
1. `dimension_assessed.evidence_spans` = tool-side-resolved raw offsets (same convention as
   reference labels); adds `degraded: bool`, nullable `score` (degraded only), and
   `resolution_failures: int` (per-dimension citation-quality signal; P2 faithfulness
   precursor).
2. `run_end.aggregate` = `{weighted_mean: number|null, veto, partial: bool, missing: [dim]}`;
   `veto` documented as the hard_requirements soft-veto state (unmet/indeterminate/met — the
   rubric's cap+gate wiring, not a fifth score).
3. Invariant 2 (dimension completeness) clarified: degraded COUNTS as assessed (event
   present, score null) — completeness scoring must not misreport degradation as absence.
4. Invariant 3 (evidence) forks: non-degraded requires ≥1 well-formed span; degraded may
   carry 0 (failed resolution is why it degraded).
5. Invariant 4 (gate consistency) extended: any degraded dimension ⇒ a `gate_event` with
   trigger `insufficient_evidence` (decision 3-ii, now an assertable contract).
6. Invariant 6 (retry visibility): `llm_call.attempt > 1` requires a prior same-node
   non-ok attempt. **Superseded framing (Stage E, owner ruling):** originally specified as
   "one definition shared with the state reducer's rewrite carve-out"; the carve-out was
   deleted (see decision 2b supersede) — the two layers now carry independent contracts:
   state = exactly one write per dimension, no exceptions; trajectory = retries visible
   with failure precedent. Not shared: separate and each stronger.
7. **NEW invariant 7 — data hygiene:** no event field, on any status branch, carries dataset
   text; `error.detail` explicitly named as the high-risk path (failed quotes must not be
   logged "for debugging" — counts yes, text no). Pinned by test: no event string value
   contains a ≥20-char verbatim substring of either document (runs where raw data exists;
   CI-skipped like the anchor in-bounds test).

Invariants 1 (envelope monotonic) and 5 (totals reconcile) unchanged; `args_summary`
conventions are those of the decision-3 signature table.

### 5. Gate triggers + initial thresholds — DECIDED (owner, 2026-07-17)

Design input: finding 004 (gate ground truth 29/30 positive; veto 24/30).

- **5a — boundary band [2.5, 3.5)**: `advance ≥ 3.5` (veto met, not partial) ·
  `do_not_advance < 2.5` · in-band → `boundary` trigger. **One ruler, three places:** the
  same operationalization defines the gate's boundary trigger, label_stats' divergence, and
  P2 gate-integrity's revision starting point — when P2 revises, ONE definition moves and
  all three stay aligned (no eval-says-good/gate-says-bad drift). Empirical calibration: 8
  of the 30 reference pairs fall in-band; the owner hand-flagged 7 as boundary — the ruler
  already tracks human judgment. Defense chain (Q7): rubric passing floor → half-band
  tolerance → alignment check against 30 labels → P2 numeric revision loop.
- **5b — anomaly is a CLOSED deterministic list (exactly three, exhaustive):**
  A1 document empty · A2 document < 200 chars (post whitespace-strip, per document) ·
  A3 document load/decode failure (encoding errors are A3 — a deterministic exception, not
  a judgment). **Nothing else triggers anomaly in P1** — garble heuristics, all-caps,
  repetition, injection markers are explicitly out (P3's threat model; adding them here
  as "obviously deterministic" is how the layering leaks). The agent's anomaly triggers are
  by construction more conservative than the owner's 10/30 hand labels; the gap is P2
  stratified-analysis material, not a defect to erase.
- **5c — veto cap_value = 2.4** (one tick below the boundary floor: a veto-unmet pair can
  never present as boundary-or-better). Trajectory records BOTH `aggregate.weighted_mean`
  (raw) and `aggregate.capped` (equal when no cap): the machine's recommendation reads
  capped; the human at the gate sees the uncapped score — "the cap constrains the machine's
  conclusion, not the human's information" (a vetoed pair showing raw 4.1 is key input for
  judging whether the veto itself misfired). Schema addition rides PR-2. Consumption-map
  note (owner leaning, to be confirmed in the P2 scorer design doc, not defaulted):
  gate-integrity asserts on **capped**; agreement-vs-labels compares on **raw** (the
  owner/mentor labels had no cap mechanism — like with like).
- **No threshold gymnastics for negatives (finding 004 discipline):** the high trigger rate
  is a true property of this corpus; the negative class comes from P2's controlled variants,
  never from loosening thresholds to make the rate look nice.

### 6. Checkpointer + two-mode wiring (D15) — DECIDED (owner, 2026-07-17)

- **6a — `SqliteSaver`** (framework checkpointer) over hand-rolled JSON: resume semantics
  ride the framework's battle-tested path (decision 2c's principle, reapplied); D1 permits
  explicitly. Lives at `runs/checkpoints.db` — gitignored because by-value state (2a)
  carries raw document text: the data discipline closes its loop.
- **6b — dynamic `interrupt()` inside the gate node**, called only when
  `mode=interactive AND triggers nonempty` — not static `interrupt_before` (which stops
  every run regardless). "Stop only when there is something to review" IS the gate's
  semantics: mechanism and meaning isomorphic.
- **6c — review artifact:** on interrupt, write `review/<run_id>.md` — triggers,
  per-dimension scores WITH evidence text (review/ is gitignored; raw text legal there),
  raw + capped aggregates side by side (5c's information-preservation landing), machine
  conclusion draft. Human edits one decision field (approve / edit / reject);
  `resume <run_id>` CLI validates and resumes the thread; `gate_event.resolution` records
  approved/edited/rejected — **human adjudication becomes evaluable data** (post-P2 the
  system can answer "how often and in what pattern do humans overturn the machine").
- **6d — eval mode:** never interrupts; `gate_event{action: auto_resume, resolution: auto}`;
  batch runs proceed with the machine conclusion (flagged) and full trajectories.

### Calibration round 1 (owner-ratified, 2026-07-21)

Evidence base: the 30-pair dev batch (`eval/reports/batch_vs_reference.py`; before-numbers:
ledger contradictions 8/7 pairs · education degradations 4 (3 quote-resolution, 2 extraneous
determinations incl. one experience) · gate confusion TP27/FN2/FP1/TN0 · exact agreement
skills 13/30 · exp 19/29 · edu 15/26 · hard 23/30 · cost 742k in / 96k out).

**Ruled classification:** #1 ledger contradictions → prompt debt (consistency instruction;
scorer shifts from bug-catcher to regression guard) · #2 education degradations → prompt debt
(quote-precision guidance + non-skills/hard dimensions carry no determinations, prompt +
tool-side drop) · #3 "relevant experience" → rubric debt (v1.2 scope_note: relevant =
role-matching; codifies the reading the reference labels already used — no relabel) ·
#4 band-0/1 boundary → **deferred entirely** (see discipline below) · #5 central tendency +
per-dimension agreement spread → honest P2 numbers, untouched · #6 TN=0 → finding 004's
variant plan, thresholds untouched.

**Attribution discipline (owner rule): one calibration round, one attributable change per
mechanism.** #1/#2/#3 may share a round because their metrics are independent (contradiction
count · resolution_failures/degradations · hard-dimension divergence pattern). #4 would stack
a second rubric change on the same dimension family as #3, making the before/after
unattributable — it waits for the post-v1.2 rerun; if 0/1 divergence persists, v1.3 opens
separately. The credibility of every before/after table rests on this rule.

**Cost ledger (running):** dev full-batch round 1 (2026-07-20/21, deepseek-chat): 742,420 in
/ 95,970 out. Calibration rerun and delivery-model final run append here — "what does one
full eval round cost" gets a measured answer.

### P2 scorer candidates discovered during P1 (running list)

- **Ledger consistency (internal-coherence class — finding 008):** hard_requirements
  determinations must agree with the prior dimensions' determinations they claim to reuse;
  intra-run contradiction is detectable with zero annotation. Donated by the first live
  run's gate miss (r20260720T094231-3ae875), not designed a priori.

### 7. Provider compatibility + degradation policy (D3) — DECIDED (owner, 2026-07-17)

- **7a — single module `agent/client.py`** on the openai SDK; base_url/key/model entirely
  env-driven (`LLM_PROVIDER=deepseek|openai`; `.env.example` updated). **Enforced by
  hygiene test:** grep-style CI test fails on any provider string in `agent/` or `eval/`
  outside the client module — D3-① upgraded from convention to assertion.
- **7b — pydantic single-source types** (`agent/types.py`: Assessment, EvidenceSpan,
  Determination, GateOutcome, Aggregate, PairRef; `extra="forbid"`, score `int|None` with
  0–5 bounds). One definition, three imports: client validation
  (`Assessment.model_validate`), state annotation, scorer assertion. **The provider-facing
  `submit_assessment` function schema is generated from the same models
  (`model_json_schema()`)** — the contract the model is forced to obey and the validator
  that checks it are one object; prompt-side/validation-side schema drift is structurally
  impossible. (First proposal — hand-written validation "to keep deps light" — was blocked
  by owner: pydantic is already in the tree via langgraph, the saving was zero, and
  hand-rolled validators are exactly where holes pollute degraded-determination accuracy;
  same principle as 6a, initially misapplied. Recorded as a Problems & Fixes episode.)
- **7c — malformed-output tests:** mocked transport, zero live calls/keys in CI; one test
  per provider config asserting the full chain retry → degraded → insufficient_evidence →
  gate, with correct trajectory events — the executable contract of decision 3-ii.
- Dependencies land at Stages D/E via uv: `langgraph`, `langgraph-checkpoint-sqlite`,
  `openai`, `pydantic` (explicit, though already transitive).
