# Trajectory JSONL schema — v0.1 (frozen-candidate)

The trajectory is the eval's source of truth (Decision 11): every observable the P2 scorers
need is an event in one JSONL file per run, written as the run happens. This schema is
defined **before any agent code exists** and freezes before P2; changes after the freeze are
schema versions, never silent edits. Validator: `eval/trajectory.py`; contract tests:
`tests/test_trajectory_schema.py`.

## Storage

- One run = one file: `runs/<run_id>/trajectory.jsonl`.
- `runs/` is **gitignored**: prompts and tool payloads carry raw dataset text (Decision 5 —
  never committed). Committed example trajectories use synthetic text only
  (`examples/trajectories/`).
- `run_id` = `r<UTC yyyymmddThhmmss>-<6 hex>` — sortable, collision-safe enough for one
  machine. Findings and reports cite run IDs; regeneration requires the local `runs/` data,
  same standing as the raw CSVs.

## Envelope (every line)

```json
{"run_id": "r20260716T093011-a1b2c3", "seq": 0, "ts": "2026-07-16T09:30:11.412Z", "type": "run_start", ...}
```

- `seq`: 0-based, strictly monotonic +1 — a gap or repeat is a corrupt trajectory.
- `ts`: UTC ISO-8601 with milliseconds.
- `type`: one of the event types below; unknown types fail validation (freeze discipline).

## Event types

### `run_start` (exactly one, seq 0)
`schema_version` ("0.1") · `pair` {split,row} · `rubric_version` · `agent_mode`
(interactive|eval) · `provider` · `model` · `config_digest` (sha256 of the resolved run
config — thresholds, prompts version; the digest pins what the run saw without embedding it).

### `llm_call` (one per model invocation, including retries)
`node` (graph node name) · `purpose` (extraction|assessment|aggregation|...) · `provider` ·
`model` · `tokens_in` · `tokens_out` · `latency_ms` · `attempt` (1 = first try) · `status`
(ok | malformed_output | error). Prompt/response text is NOT stored here (dataset text);
`response_digest` allows local correlation with the gitignored raw dump if one is kept.

### `tool_call` (one per tool invocation)
`tool` (one of the six locked names) · `status` (ok|error) · `latency_ms` · `args_summary`
(dataset-text-free: e.g. `{"dimension": "skills_coverage"}` — never resume/JD content).

### `dimension_assessed` (exactly one per rubric dimension per run)
`dimension` · `score` · `evidence_spans` [{doc,start,end}] (offsets into the pair's raw
docs — same convention as the reference labels; offsets are committable, text is not) ·
`determinations` (skills_coverage only) · `veto_state` (hard_requirements only).

### `gate_event` (mandatory whenever any trigger condition holds; absent otherwise)
`triggers` [hard_unmet | hard_indeterminate | boundary | insufficient_evidence | anomaly] ·
`mode` (interactive|eval) · `action` (interrupt | auto_resume) · `resolution`
(approved | edited | rejected | auto) — `auto` is the only legal resolution in eval mode.

### `error` (any recoverable or fatal fault)
`where` (node/tool) · `kind` (parse|provider|validation|other) · `recovered` (bool) ·
`detail` (dataset-text-free message).

### `run_end` (exactly one, final seq)
`recommendation` (advance | do_not_advance | flagged) · `aggregate` {weighted_mean, veto} ·
`gate_fired` (bool) · `totals` {llm_calls, tokens_in, tokens_out, latency_ms}.

## Invariants (validator-enforced; each is a P2 structural-scorer seed)

1. Envelope: seq strictly monotonic from 0; exactly one `run_start` (first) and one
   `run_end` (last); all events share one `run_id`.
2. **Dimension completeness:** exactly one `dimension_assessed` per rubric dimension
   (4 under rubric v1.x) — none missing, none duplicated.
3. **Evidence citation:** every `dimension_assessed` carries ≥1 evidence span with
   `0 ≤ start < end`; spans are per-document offsets (in-bounds checkable where raw data
   exists — same skip rule as the rubric anchor test).
4. **Gate consistency:** `run_end.gate_fired` ⇔ a `gate_event` exists; veto state in the
   hard_requirements assessment ≠ met ⇒ a `gate_event` exists whose triggers include the
   matching `hard_*`; eval-mode gate events resolve `auto`.
5. **Totals reconcile:** `run_end.totals.llm_calls` equals the count of `llm_call` events;
   token/latency totals equal their sums.
6. **Retry visibility:** `llm_call` events with `attempt > 1` must follow a same-node event
   with `status != ok` (degradation is visible, never silent — compat-layer requirement ②).

## What is deliberately NOT in the schema

- Prompt/response text and parsed document content (Decision 5; digests + local raw dumps
  cover debugging).
- Provider-specific fields beyond `provider`/`model` strings (compat requirement ① — the
  schema is the neutral layer).
- Scores' *reasoning prose* — evidence spans carry the verifiable part; prose lives in the
  local raw dump if needed.

## Freeze process

v0.1 is the frozen-candidate. P1 development may amend it via PR (version bump + one-line
changelog below); the version that P2's first scorer commit reads is **frozen** — after
that, changes require a new schema_version and a migration note.

| version | date | change |
|---|---|---|
| 0.1 | 2026-07-16 | initial frozen-candidate |
