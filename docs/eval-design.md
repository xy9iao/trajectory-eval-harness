# P2 eval design — the research core

Working design document for Phase 2. Decisions are made by the owner in the design workshop
(options + tradeoffs → ratified with rationale) before the code that depends on them is written
— the P1 pattern. This doc is also the roadmap-mandated home for the two-tier scorer split.

## Two tiers

- **Structural scorers** — no human annotation; run on every case from the trajectory alone.
  Each is the maturation of a `eval/trajectory.py` invariant into a measured metric:
  gate-integrity confusion matrix (reference standard = P0 `gate_expected`) · tool-call structural
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
project's information-density). Two constraints: **matplotlib defaults unless a default causes information loss** (see
Figure conventions below for the admission test — preference is gilding, visibility is
function) and PNGs land in
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

### 3b. Variant-stage acceptance (added 2026-07-28, structural-scorer stage)

The variant set must carry **two separate batches**, because the gate's negative class and the
error-recovery failure path are different failure routes and one does not cover the other:

1. **Gate negatives** (finding 004's TN=0): perturbations that flip a pair to a legitimate
   no-gate outcome, with the expected gate behavior recorded per variant.
2. **Fault/recovery samples** (this stage's coverage caveat): malformed model output,
   truncated documents, encoding damage — inputs that exercise the retry → degrade →
   escalate chain. The live corpus exercised it on only 20/150 runs, so error recovery's
   real coverage depends entirely on this batch existing.

### 3c. Variant-stage scope gates (owner, 2026-07-28; gate 5 added 2026-07-31) — five, all binding

1. **Counts, deliberately small:** gate negatives **6–8**, fault samples **5–6**. The goal is
   to un-degenerate the confusion matrix (finding 004's TN=0) and to give each failure route
   1–2 exemplars — NOT to build a balanced dataset. Beyond that the return on hand-built
   distribution collapses.

   **Precedence, ruled 2026-08-02: when gate 1 and gate 5 conflict, GATE 5 WINS.** Gate 1 is
   a sufficiency heuristic about how many exemplars are enough; gate 5 is a data-correctness
   rule. Padding the negative set with a broken construction to reach a count would
   manufacture exactly the plausible-looking wrong number this project exists to catch. An
   under-populated negative set is recorded as under-populated — the count is a target, never
   a quota. **As built: 2 live gate negatives, below this range, by this precedence.**
2. **Closed perturbation types:** only those listed in 3b. A new type needs a new ruling —
   this is what stops the set from growing a third and fourth category mid-build.
3. **One-sentence expectation or it isn't built:** every variant states *what changed* and
   *what gate behavior is expected after the change*. If that sentence can't be written, the
   variant isn't a test with an answer and doesn't belong.
4. **Variant numbers NEVER merge with live-corpus numbers in the report.** TNs are
   constructed; TP/FP/FN come from the real 30 pairs. A single combined confusion matrix
   would let hand-built samples contaminate the credibility of the whole table. Two tables,
   or one table with a source column — decided now, not at report time.
5. **Divergence defaults to "my construction is wrong" — and resolves into exactly one of
   three states.** When a variant's observed result contradicts its expectation, the first
   hypothesis is that the perturbation failed to do what the spec claims, because a variant
   is a test with a *known* answer and the answer is only known if the construction is
   sound. The default holds until a diagnosis overturns it, and the diagnosis must land in
   one of:

   | state | meaning | where it goes |
   |---|---|---|
   | **construction error** | the perturbation did not satisfy what the spec claims | `construction_failures`; **never** the negative set |
   | **agent–rubric divergence** | the construction is sound; the agent's behavior departs from a written rubric convention | stays a live variant, tagged with the divergence and the finding that owns it |
   | **undiagnosable** | the cause cannot be established even after local re-resolution | recorded against **neither** side |

   **`undiagnosable` must state why it could not be diagnosed and what was attempted** —
   specifically whether local re-resolution of the trajectory's opaque ids was run. Without
   that requirement the category degrades into a bin for "did not bother to look."

   **A diagnosis that needed information outside the trajectory is still a diagnosis** — it
   is recorded as such (*"this attribution depends on out-of-trajectory information"*), not
   downgraded to undiagnosable. The distinction matters because trajectories deliberately
   carry requirement **ids, never requirement text** (the data boundary from finding 007),
   so id resolution is a normal diagnostic step rather than a failure of the record.

   Repeated same-direction failures are finding material, not noise to retry past.

   *Provenance:* the rule was written because two low-road variants (`cf-01` on train 901,
   `cf-02` on train 2980) were built with perturbations that did not satisfy their pairs'
   must-ledgers. Both would have been scored as agent false-positives when the agent was in
   fact correct. Both were caught at spec review, before any run — which is where this class
   of error is cheap to catch and after which it is not.

### 3d. Faithfulness sampling — STRATIFIED, not random (owner, 2026-07-28)

10 samples, drawn to interrogate known weak spots rather than to estimate a population rate:

| stratum | n | why |
|---|---|---|
| education_domain_fit | 3 | lowest self-consistency (finding 011 §2) — if faithfulness also degrades here, §2's hypothesis gains a third independent evidence path |
| hard_requirements veto-swing pairs (596/970/5084/6220) | 3 | scores jump between poles; do the citations jump too? tests whether the stated reason is post-hoc rationalization of the score |
| degraded / nonzero resolution_failures | 2 | the floor of evidence quality where quote resolution already struggled |
| random | 2 | a baseline, so stratification doesn't exclude the normal case entirely |

**Sampling-pool upgrade (2026-07-28):** from the next spot-check onward, one stratum is
drawn from the **evidence-coverage sentinel's over-threshold pool**
(`eval/scorers/evidence_coverage.py`) instead of being guessed at. This converts a
one-off manual discovery into a standing mechanism that aims scarce human minutes at the
likeliest failures — the role `resolution_failures` plays for degradation. The sentinel
does not replace the other strata: it has known misses (finding 013's train 5798 sits
below threshold yet failed human review), so it narrows where to look without defining
what counts.

**Reporting constraint:** a stratified sample answers "how does faithfulness behave on known
weak spots", NOT "what is the overall faithfulness rate". The report states the sampling
design next to the number and never presents it as a population estimate.

Judgment scale: supports / partially supports / does not support. **"Partially supports"
requires a one-line reason** (quote insufficient for the band? quote correct but pointing the
wrong way?) — without it the middle category is unanalyzable.

### 4. Cross-model protocol — DECIDED (owner, 2026-07-22)

D12 permits one calibration round on the delivery model. **That round is spent on
prompt/pipeline compatibility only** (OpenAI function-calling behavior differences, malformed
rate) — **never on semantics.** finding 009's hypothesis needs the delivery model as an
uncontaminated second data point: whether the 596-class semantic-prior divergence persists on
OpenAI MUST be a raw observation, so no semantic calibration may precede the delivery run. This
constraint sits at the same level as the config-digest reproducibility rule in the cross-model
protocol.

### Figure conventions (general rules for every P2 chart script)

- **Regenerable exactly:** any randomness in a figure (jitter, sampling) uses a fixed seed —
  a chart that renders differently on re-run breaks the "figures are generated output, never
  hand-made" contract.
- **Styling admission test:** matplotlib defaults, EXCEPT where the default causes information
  loss. The bar is "without this change, a real feature of the data becomes invisible" (e.g.
  same-color bars swallow an overlaid strip and hide a bimodal shape) — never "this looks
  nicer". Preference is gilding; visibility is function.
- **Parameterize model + output path** so the cross-model counterpart renders from the same
  script and the two figures sit side by side without hand-editing.
- **Vocabulary discipline:** *agreement* is reserved for scores vs the human reference;
  model-vs-itself is *self-consistency*. The two are distinct measurements and the P2
  cross-validation argument depends on not conflating them.

### 5. Two-tier split formalization — this document (§ "Two tiers")
