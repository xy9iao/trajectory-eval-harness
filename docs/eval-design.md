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

### 2. Scorer architecture — PENDING

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
