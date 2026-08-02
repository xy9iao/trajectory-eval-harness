# 014 — The "meets every must, still uncompetitive" negative is structurally unconstructible

**Status:** closed · **Phase:** P2 (variant stage) · **Date:** 2026-07-31
**Supersedes nothing; supplies the missing mechanism for [finding 004](004-gate-truth-imbalance.md).**

## Observation

The variant batch needed gate negatives by two routes. The **high road** — perturb a pair
until it meets its musts *and* scores well, so the gate correctly stays shut and the
recommendation is `advance` — built easily: four of four attempts produced a clean spec.

The **low road** — meets every stated must, still scores below the 2.5 floor, so the gate
stays shut and the recommendation is `do_not_advance` — failed twice, on two unrelated
pairs, in the same direction. Both failures were caught at spec review before any run
(recorded as `cf-01`, `cf-02` in `data/variants/variants-v1.json`):

| attempt | base | what the perturbation covered | what the ledger actually required |
|---|---|---|---|
| cf-01 | train 901 | degree + 1 year data analysis (2 items) | **7** clear unmet items — the five skills items were untouched — plus a work-authorization item no resume edit can resolve |
| cf-02 | train 2980 | 2.5-year configuration-analyst segment + 1 certification | a four-component skills bundle, **10 years progressive**, 5 years customer-facing — 2.5 years cannot evidence 10 |

Two failures on unrelated pairs, both understating what the ledger demanded, is a pattern
rather than two authoring slips. That is what made it worth explaining instead of retrying.

## Hypothesis

Initial (mine, wrong in its stated form): *satisfying all musts forces `skills_coverage` to
band ≥ 3, and 0.5·3 + 0.3·3 = 2.4 already, so any non-zero education pushes the mean into
the [2.5, 3.5) boundary band and the gate fires anyway.*

The arithmetic holds but the premise "musts met ⇒ skills ≥ 3" is not a rubric rule, and the
reference set does not support it as stated: pairs scoring `hard_requirements` = 3 carry
skills bands as low as 2. Revised hypothesis, which is the one the data supports:

**The veto and the scoring dimensions are not independent measurements.** The ledger is
built by *reusing* the determinations that produced `skills_coverage` and
`experience_level`. So the low road asks two structurally coupled variables to move in
opposite directions — musts up, skills down — and a perturbation that satisfies a skills
must necessarily supplies the evidence that lifts the skills band.

## Verification

Three independent checks, all against `data/reference/labels-v1.jsonl` (n=30):

**1. The coupling is explicit in the ledgers, not inferred.** 28/30 hard-requirement ledgers
state in prose that an item's judgment *reuses* a scoring-dimension determination — 22/30
reuse `skills_coverage`, 14/30 reuse `experience_level`. The veto does not read the
documents independently; it re-reads the same determinations under a different rule.

**2. The eligible corner of band space is small and awkwardly shaped.** Enumerating all 216
band combinations (weights 0.5/0.3/0.2; `hard_requirements` is a veto, not a weighted term —
confirmed against recorded means):

- 104/216 combinations score below 2.5 — so the region is *not* empty in the abstract;
- but only **16/216** do so with skills ≥ 3, and every one of those additionally requires
  experience ≤ 3 **and** education ≤ 4, with the two tightly traded off: at experience 3 the
  only survivor is education 0.

So the low road is not merely rare — it demands a candidate strong enough to clear every
stated must while scoring near-bottom on two of three dimensions at once.

**3. The empirical frequency matches.** In the reference set, `hard_requirements` = 5 occurs
**1/30**, and that single pair carries skills = 5 (mean well above the floor). 24/30 pairs
are vetoed to 0. There is no pair in the reference set on the low road, and the one pair
that meets its ledger fully is nowhere near the region.

## Change

1. **The low road was dropped, not re-based.** The gate-negative batch is 6 variants, all
   high road. Counts stay inside the ratified 6–8 range (eval-design 3c gate 1), so no
   ruling was bent to accommodate this.
2. **`docs/eval-design.md` §3c gained a fifth binding gate:** a variant whose result
   contradicts its expectation defaults to *"the construction is wrong"*, not *"the agent is
   wrong"*. Failed constructions are recorded with (expected, actual, cause) and **never
   enter the negative set** — a mislabelled negative manufactures a phantom true-negative in
   the confusion matrix, corrupting the exact metric the batch exists to un-degenerate.
   Under both failed constructions the agent would have been **correct** and scored as a
   false positive.
3. **`tests/scorers/test_variants.py` pins the absence to the record** — a test asserts the
   negative set is high-road-only and that the failed constructions stay documented, so a
   later reader cannot quietly "fix" the gap by adding a low-road variant back.
4. **One base swap, on separate grounds** (recorded as such, not as a construction failure):
   gn-04 moved from train 1050 (reference mean 2.6) to train 6220 (3.0, experience and
   education both 5). The 1050 construction was sound; a correct perturbation could still
   have landed inside the boundary band and fired the gate for a reason unrelated to what
   the variant tests. A variant that can fail for the wrong reason is a weak test.

## Result

No before/after metric — this finding's product is a **mechanism for finding 004**, plus two
errors kept out of the numbers.

Finding 004 recorded TN = 0 in the reference set and left it as an imbalance to be repaired
by construction. This finding says the imbalance is **not a sampling accident**: the rubric's
score geometry makes "meets everything, still uncompetitive" a near-empty region, because
the veto re-reads the same determinations that drive the scores (28/30 ledgers), and the
band corner that would permit it is 16/216 with punishing constraints on the other two
dimensions. The gate's negative class is intrinsically thin *by design of the rubric*, and
the honest report line is:

> The negative class is constructed by the high road only. The low road — meeting every
> stated must while remaining below the advance floor — is near-impossible to construct
> under this rubric's score geometry (finding 014), because the hard-requirement ledger
> reuses the determinations that produce the scoring bands rather than reading the documents
> independently.

**Cost of catching it here:** two specs rewritten before any API call. **Cost of catching it
after the batch ran:** two phantom true-negatives in the headline confusion matrix, and a
false-positive rate reported against an agent that was right both times.

## Open question (not chased)

Whether the coupling is a *defect* of the rubric or a correct property of the task. An
argument exists for each: reusing determinations keeps the veto consistent with the scores
(a candidate cannot be simultaneously judged skilled and unqualified on the same evidence),
but it also means the veto carries no information the scores did not already carry, which
weakens the case for it being a separate dimension at all. Deciding this needs the
cross-model results — recorded here so the question is not lost, and left open on purpose.
