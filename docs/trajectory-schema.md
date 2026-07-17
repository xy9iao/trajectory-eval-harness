# Trajectory JSONL schema — v0.2 (frozen-candidate)

The trajectory is the eval's source of truth (Decision 11): every observable the P2 scorers
need is an event in one JSONL file per run, written as the run happens. Designed in the P1
design workshop (docs/p1-design.md, decision 4 — owner-ratified deltas over the v0.1 draft);
freezes before P2. Changes after the freeze are schema versions, never silent edits.
Validator: `eval/trajectory.py`; contract tests: `tests/test_trajectory_schema.py`.

## Storage

- One run = one file: `runs/<run_id>/trajectory.jsonl`.
- `runs/` is **gitignored**: prompts, checkpoints, and raw dumps carry dataset text
  (Decision 5 — never committed). Committed example trajectories are synthetic only
  (`examples/trajectories/`).
- `run_id` = `r<UTC yyyymmddThhmmss>-<6 hex>` — sortable, collision-safe for one machine.
  Findings and reports cite run IDs; regeneration requires the local `runs/` data, same
  standing as the raw CSVs.

## Envelope (every line)

```json
{"run_id": "r20260717T093011-a1b2c3", "seq": 0, "ts": "2026-07-17T09:30:11.412Z", "type": "run_start", ...}
```

- `seq`: 0-based, strictly monotonic +1 — a gap or repeat is a corrupt trajectory.
- `ts`: UTC ISO-8601 with milliseconds.
- `type`: one of the seven event types; unknown types fail validation (freeze discipline).

## Event types

### `run_start` (exactly one, seq 0)
Join keys, explicit by design (scorer consumption map): `pair` {split,row} · `provider` ·
`model` · `rubric_version` · `config_digest` (sha256 of resolved run config) · `agent_mode`
(interactive|eval) · `schema_version` ("0.2"). pass^k joins on (pair, provider, model,
config_digest); agreement joins pair → `data/reference/labels-v1.jsonl`; the cross-model
table groups by (provider, model).

### `llm_call` (one per model invocation, including retries)
`node` · `purpose` (extraction|assessment|...) · `provider` · `model` · `tokens_in` ·
`tokens_out` · `latency_ms` · `attempt` (1 = first try) · `status`
(ok | malformed_output | error). No prompt/response text (invariant 7); `response_digest`
optional for local correlation with gitignored raw dumps.

### `tool_call` (one per orchestration-contract tool invocation — the six locked names)
`tool` · `status` (ok|error) · `latency_ms` · `args_summary` per the decision-3 signature
table (dataset-text-free by construction).

### `dimension_assessed` (exactly one per rubric dimension per run; degraded counts)
`dimension` · `score` (int 0–5, or **null iff degraded**) · `degraded` (bool) ·
`evidence_spans` [{doc,start,end}] — **tool-side-resolved raw offsets** (the model submits
verbatim quotes; `assess_dimension` resolves them; quotes themselves never enter the
trajectory) · `resolution_failures` (int — quote-resolution failures for this dimension;
citation-quality signal, P2 faithfulness precursor) · `determinations` (skills_coverage
only) · `veto_state` (hard_requirements only: met|indeterminate|unmet).

### `gate_event` (mandatory whenever any trigger condition holds; absent otherwise)
`triggers` [hard_unmet | hard_indeterminate | boundary | insufficient_evidence | anomaly] ·
`mode` (interactive|eval) · `action` (interrupt | auto_resume) · `resolution`
(approved | edited | rejected | auto) — `auto` is the only legal resolution in eval mode.
Anomaly fires only on the closed deterministic list (design decision 5b: empty doc ·
doc < 200 chars · load/decode failure — nothing else in P1).

### `error` (any recoverable or fatal fault)
`where` · `kind` (parse|provider|validation|other) · `recovered` (bool) · `detail` —
**dataset-text-free; failed quotes must never be logged here** (invariant 7's named
high-risk path: counts yes, text no).

### `run_end` (exactly one, final seq)
`recommendation` (advance | do_not_advance | flagged) ·
`aggregate` {`weighted_mean`: number|**null when partial**, `capped`: number|null (post-veto
cap, = weighted_mean when no cap; the machine's conclusion reads capped, the human sees
raw — decision 5c), `veto`: the hard_requirements soft-veto state (met|indeterminate|unmet —
the rubric's cap+gate wiring, NOT a fifth score), `partial`: bool (true iff any scoring
dimension degraded), `missing`: [dim]} ·
`gate_fired` (bool) · `totals` {llm_calls, tokens_in, tokens_out, latency_ms}.

## Invariants (validator-enforced; each seeds a P2 structural scorer)

1. **Envelope:** seq strictly monotonic from 0; exactly one `run_start` (first) and one
   `run_end` (last); single `run_id`; known event types; schema_version "0.2".
2. **Dimension completeness:** exactly one `dimension_assessed` per rubric dimension —
   **degraded counts as assessed** (event present, score null); score consistency:
   `degraded=false ⇒ score ∈ 0..5`, `degraded=true ⇒ score null`.
3. **Evidence citation (forked):** non-degraded assessments carry ≥1 well-formed span
   (`0 ≤ start < end`); degraded may carry 0 (failed resolution is why they degraded);
   any span present must be well-formed.
4. **Gate consistency:** `run_end.gate_fired` ⇔ a `gate_event` exists · veto state ≠ met ⇒
   a `gate_event` whose triggers include the matching `hard_*` · eval-mode gate events
   resolve `auto` · **any degraded dimension ⇒ a `gate_event` with trigger
   `insufficient_evidence`** (decision 3-ii as assertable contract) · `aggregate.veto`
   equals the hard_requirements assessment's `veto_state` · `partial=true ⇔
   weighted_mean=null ⇔ missing nonempty`.
5. **Totals reconcile:** `run_end.totals.llm_calls` = count of `llm_call` events;
   token totals = their sums.
6. **Retry visibility:** `llm_call` with `attempt > 1` requires a prior same-node event
   with `status ≠ ok`. This is the trajectory layer's own contract, independent of the
   state layer's (which is stricter: exactly one assessment write per dimension, no
   exceptions — retries never surface as state writes because they live inside
   `assess_dimension`). Superseded the earlier "one shared definition" framing at Stage E
   (p1-design.md decision 2b supersede).
7. **Data hygiene:** no event field, on any status branch, contains dataset text — pinned
   by test: no string value anywhere in any event contains a ≥20-character verbatim
   substring of either raw document. Runs where the raw data exists (CI-skipped, same rule
   as the anchor in-bounds test). `error.detail` is the named high-risk path.

## What is deliberately NOT in the schema

- Prompt/response text, verbatim evidence quotes, parsed document content (Decision 5 +
  invariant 7; digests and gitignored local dumps cover debugging).
- Provider-specific fields beyond `provider`/`model` strings (D3-① — the schema is the
  neutral layer; a hygiene test enforces the module boundary).
- Reasoning prose — evidence spans carry the verifiable part.

## Freeze process

v0.2 is the frozen-candidate. P1 development may amend via PR (version bump + changelog
line); the version P2's first scorer commit reads is **frozen** — after that, changes
require a new schema_version and a migration note.

| version | date | change |
|---|---|---|
| 0.1 | 2026-07-16 | initial draft (closed PR #6; reverted, kept as raw material) |
| 0.2 | 2026-07-17 | design-workshop revision (p1-design.md decision 4): explicit join keys · degraded representation (nullable score, `degraded`, `resolution_failures`) · evidence = tool-side-resolved offsets, quotes never logged · aggregate gains `capped`/`partial`/`missing`, `veto` semantics documented · invariant 2 counts degraded as assessed · invariant 3 forks · invariant 4 extends (degraded ⇒ insufficient_evidence; veto/aggregate coherence) · invariant 6 unified with the reducer carve-out · NEW invariant 7 (data hygiene) |
