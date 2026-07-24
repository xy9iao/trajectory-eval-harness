# P2 eval design — the research core

Working design document for Phase 2. Decisions are made by the owner in the design workshop
(options + tradeoffs → ratified with rationale) before the code that depends on them is written
— the P1 pattern. This doc is also the roadmap-mandated home for the two-tier scorer split.

## Two tiers

- **Structural scorers** — no human annotation; run on every case from the trajectory alone.
  Each is the maturation of a `eval/trajectory.py` invariant into a measured metric:
  gate-integrity confusion matrix (ground truth = P0 `gate_expected`) · tool-call structural
  correctness · error recovery · **pass^k** stability · ledger consistency (finding 008).
- **Semantic checks** — human-verified samples: per-dimension agreement vs the reference set
  (stratified by divergence root cause — findings 009/010) · faithfulness spot-check (5–10
  manual: cited evidence exists and supports the score) · semantic tool-call correctness.

## Execution order (owner reorder, 2026-07-22)

**workshop → pass^k → structural scorers → semantic + variants → cross-model → p2 report.**

pass^k comes FIRST by dependency, not taste: every later single-run number (gate-integrity
matrix, agreement) is only interpretable once we know its error bar, and skills already flashed
13→7→9 across three single-run batches — single runs may be dice. pass^k measures the
per-dimension run-to-run variance that sets the error bar on everything downstream; running it
last would force re-interpretation of every table it retroactively puts inside the noise band.
Cost (the dev-model reruns) is pulled earlier — accepted: that spend was always coming, and
paying it now buys the error bars for every subsequent figure.

## Decisions

### 1. pass^k — k value + output structure — DECIDED (owner, 2026-07-22: k=5)

**k = 5.** Cost on the dev model is a rounding error at any k (30 pairs × k × ~560k in ≈
$0.6/$1.0/$2.0 for k=3/5/10); the real tradeoff is statistical df vs the delivery-model token
budget. k=3 gives df=2 (a too-crude variance estimate); k=5 gives df=4 (the credible-stability
floor); k=10's marginal precision isn't worth the tokens, which are better kept for the
required cross-model run. k=5 is the sweet spot.

**Output structure:** a **per-dimension run-to-run variance table** — this is the settlement
site for the "skills 13→7→9: drift or variance?" account (findings 009/010). Consumption
rule, written into the design now: if a dimension's run-to-run variance is natively wide, its
cross-batch score movements fall inside the noise band and the calibration-round "misses" are
re-read as noise; if narrow, the movement is real drift. The variance table is what every other
single-run metric's error bar is read from.

**Model split:** the primary pass^k runs on **dev (DeepSeek)** to build the variance floor
cheaply; the cross-model stage runs a **lighter pass^k on delivery (OpenAI)** only to check
whether stability transfers across providers — not a full repeat.

### 2. Scorer architecture — DECIDED (owner, 2026-07-22: option A + three sub-decisions)

**Uniform signature `(corpus, reference) -> ScorerResult`.** Every scorer receives all runs
(grouped by pair) + the reference and slices what it needs (per-run / per-pair-group /
per-corpus arity lives INSIDE the scorer). The runner is a dumb pipe —
`for scorer in REGISTRY: scorer(corpus, ref)` — and all intelligence lives in single-testable,
planted-defect-verifiable pure functions. This is the mirror of P1 decision 3 (graph owns
flow, model owns judgment): here the runner owns iteration, the scorer owns slicing. B/C
(arity-typed interfaces / OO classes) rejected — three dispatch paths buy a "precision" that 6
scorers don't need; **framework thickness scales with managed diversity, not below it** (the
architectural form of YAGNI), and OO fights `eval/trajectory.py`'s pure-function idiom (2c).

**2a — relation to `eval/trajectory.py` + the exclusion contract:** structural scorers REUSE
the validator's invariant functions (e.g. tool-call correctness calls the same
"each dimension assessed once" check), never re-implement. Scorers assume a validated
trajectory — and that assumption is backed by an assertion, not left to trust: **the runner
validates every case first (`validate_trajectory`); any case that fails is excluded from ALL
scorers' inputs and listed prominently in the report header ("N cases excluded: validation
failures").** A scorer silently computing statistics over an illegal trajectory is the worst
outcome (contaminated report, discovered late); exclusion makes the guarantee real and the
problem visible — the hygiene-discipline posture (surface, don't drown).

**2b — self-verification, incl. a semantic-boundary defect per scorer:** each scorer ships
planted-defect synthetic trajectories under `tests/scorers/` + a test asserting it catches
them. The defect set is **a declaration of each scorer's capability boundary**, so it must
include at least one *semantic-boundary* defect, not only structural ones (missing event,
wrong dimension): e.g. gate-integrity gets a "gate fired but the trigger reason is wrong"
case (the synthetic form of P1's 596 fired-right-for-wrong-reason). If a scorer can't catch
it, it IS the binary-matrix version that masks wrong-reason firing — the P1 blind spot must
not reappear in P2's self-verification. A scorer that can't catch its planted defect is not
done.

**2c — report + figures:** `eval/reports/p2_report.py` is the single reproducible command —
runs the whole REGISTRY, emits markdown with ≥1 figure/table per metric. **Figures use
matplotlib** (chosen: text tables can't carry the two imminent consumption scenarios —
pass^k's per-dimension variance wants error bars, cross-model wants grouped bars; the report's
end consumers are interviewers and README readers, for whom figure information-density IS the
project's information-density). Two constraints: **matplotlib default styles only** (no color
work — styling is this project's purest gilding; the value is the data) and PNGs land in
`docs/phase-reports/figures/` as **re-runnable output of p2_report.py** (figures are generated,
never hand-made — the "one command" acceptance covers them). Dependency (`matplotlib`) is added
with the first stage that generates a figure (pass^k), not in this docs-only PR.

### 3. Negative-class variants — DECIDED (owner, 2026-07-22)

**Perturb existing pairs; do NOT synthesize from scratch.** Take reference pairs and apply a
controlled perturbation to the target variable only (e.g. raise the hard-relevant experience
years; inject a missing must-have skill), preserving the real corpus's text distribution — so a
TN measured on a variant is a real negative in-distribution, not "a true negative measured on
fake data." Every variant carries metadata: **what was changed + the expected gate behavior
after the change.** The variant set is therefore a suite of unit tests with expected answers,
not another batch of data — it populates the negative class (finding 004's TN=0) with cases
whose correct gate outcome is known by construction.

### 4. Cross-model protocol — DECIDED (owner, 2026-07-22)

D12 permits one calibration round on the delivery model. **That round is spent on
prompt/pipeline compatibility only** (OpenAI function-calling behavior differences, malformed
rate) — **never on semantics.** finding 009's hypothesis needs the delivery model as an
uncontaminated second data point: whether the 596-class semantic-prior divergence persists on
OpenAI MUST be a raw observation, so no semantic calibration may precede the delivery run. This
constraint sits at the same level as the config-digest reproducibility rule in the cross-model
protocol.

### 5. Two-tier split formalization — this document (§ "Two tiers")
