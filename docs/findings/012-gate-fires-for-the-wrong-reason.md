# 012 — The gate fires for the wrong reason: 7/28 on the live corpus, and one fully diagnosed case

**Status:** open — Observation quantified (2026-07-28), one instance diagnosed end to end
(2026-08-02), Change deliberately deferred. · **Phase:** P2

**Reproduction:** `gate_integrity_scorer` over the k=5 pass^k corpus
(`runs/passk-r20260728T035619-2d6bcd.json`, 150 runs, deepseek-chat), reference =
`data/reference/labels-v1.jsonl`. Variant evidence:
`runs/variants-r20260801T111846-936b6d.json` (variant numbers are never merged with
live-corpus numbers — eval-design 3c gate 4).

## Observation A — the rate (2026-07-28)

Of the 28 pairs the confusion matrix counts as true positives, **21 fired for a reason the
reference lists; 7 did not** (`trigger_attribution_ok: 21/28`). Those 7 are scored as perfect
successes by any binary should-gate × did-gate matrix: the gate fired, the reference said it
should, cell = TP. The disagreement is entirely in *why*.

Example — train 400: reference reason `hard_unmet`; the agent fired with
`hard_indeterminate`, `hard_unmet`, `insufficient_evidence` across its runs. The pair is
gated either way, but the stated cause differs between runs and from the reference.

This is a **capability-boundary statement about the gate-integrity scorer itself**: the binary
matrix measures *whether* the gate fires; trigger attribution measures *why*. They are two
distinct measurements of the same event and must never be collapsed into one number — the
same vocabulary discipline as *self-consistency* vs *agreement* (finding 011 §2). Reporting
28/30 alone is misleading; the report presents the two figures side by side, always.

## Observation B — one instance, diagnosed end to end (2026-08-02)

P1 raised this qualitatively on train 596 and never root-caused it. The variant batch produced
the first case where the entire chain is established.

Variant `gn-01` perturbs train 5063 to satisfy both items its human ledger records as unmet.
The perturbation worked exactly as specified — the two targeted items (`R4` Java/Spring
Boot/SQL/Hibernate, `R6` DevOps CI/CD) both resolved to `covered`, and the weighted mean rose
to 3.5, clear of the advance floor. The gate fired anyway, on `hard_unmet`, driven by a tenth
ledger item:

> **R9 — "Ability to work flexible schedule including nights/weekends"** → judged `absent`

Every other item was `covered` or `partial`. This one item, alone, forced the veto to unmet
and the recommendation to `flagged`.

## Hypothesis

Two, addressing the two observations.

**For A (unchanged, still untested):** the wrong-reason firings likely overlap finding 011
§3's veto instability — `hard_indeterminate` is itself the product of an unstable ledger
determination, so a pair whose veto swings between runs also swings its stated trigger. See
also [finding 015](015-extraction-ledger-size-is-pair-dependent-unstable.md), which supplies a
concrete candidate mechanism for that instability (the ledger's *size* is a draw on some
pairs).

**For B (tested below):** the agent's judgment is **internally correct** — no resume states
weekend availability, so `absent` is right *given the item is in the ledger*. The defect is
one step earlier: the item should never have entered it. The rubric's ledger categories are
skills, years, degrees, certifications, licenses, visas and location. Availability and
physical-capability requirements sit outside all of them, and the human ledger for train 5798
states the exclusion and its reason: such items are not resume-evidenceable, so ledgering them
would fire a veto on every applicant alive. The extractor has no corresponding exclusion rule.

Predicted signature: a **permanently unsatisfiable** ledger item — not one the candidate
fails, but one no candidate can pass and no perturbation can repair.

## Verification (for B)

**The chain:**

1. The trajectory records `R9` = `absent`, veto `unmet`, every other item covered or partial.
2. Local id re-resolution returns the R9 text above. Required because trajectories carry
   requirement **ids and never requirement text** ([finding 007](007-hygiene-invariant-first-live-catch.md)'s
   data boundary); recorded as an out-of-trajectory diagnosis under eval-design 3c gate 5.
3. The rubric's written convention excludes exactly this category, with the reason stated.
4. The item is unsatisfiable in principle: `append_resume_segment` cannot make a resume
   evidence a scheduling disposition.

**Exposure — hand-checked pair by pair, not estimated.** Re-running extraction across all 30
reference pairs and inspecting every candidate item:

- **2/30** pairs have the extractor emit an availability or physical-capability must:
  train 5063 (1 item) and train 5798 (2 items).
- Both are pairs whose **human ledger explicitly recorded excluding such an item.** The
  annotator and the extractor read the same JD lines; the annotator excluded them, the
  extractor did not.

An earlier automated scan of the same question returned 5/30. Three were regex false positives
— the pattern `shift` matching **Openshift** and **Redshift** inside technology names. The
numerator above is the hand-checked one. The discarded 5/30 is recorded because the error is
the instructive part: a keyword scan cannot produce a finding's numerator on its own, and a
2.5× overstatement would have survived into the report unchallenged.

## Reproducibility caveat — added 2026-08-02, and it bounds the claim above

The variant batch was re-run after a trajectory-validity bug was fixed
(`runs/variants-r20260802T085523-ab0cf0.json`). **On the second batch `gn-01` did not fire the
gate at all** — mean 4.0, `advance`, a clean match. The availability item was extracted and
judged `absent` in two of three observed runs of the same variant, not three of three.

Two consequences, both stated rather than resolved:

- **The defect is intermittent, not deterministic.** The chain in the Verification section is
  correct about what happens *when* the item is extracted; it is not evidence that the item is
  always extracted. This is [finding 015](015-extraction-ledger-size-is-pair-dependent-unstable.md)
  acting on 012's evidence — the ledger's contents vary run to run, so a defect that lives in
  the ledger inherits that variance.
- **The 2/30 exposure figure rests on single draws** and therefore carries unstated variance of
  its own. Read it as "at least 2 pairs can produce this", not as a rate.

**Methodological point worth keeping:** a variant is a unit test with a known answer, but the
system under test is stochastic, so **one run per variant is an underpowered test**. The fault
batch reproduced exactly across both batches (5/5 twice) because its triggers are deterministic —
anomaly rules on document length, injected malformed responses. The gate negatives sit near
decision boundaries, which is precisely where finding 011's variance lives: gn-06 matched in
batch 1 and diverged in batch 2, gn-01 the reverse. Any future variant stage should run each
variant k times and report the distribution, exactly as the live corpus does.

## Why 150 live runs never surfaced this

The defect changes an outcome only when it is the **sole** driver. On the unperturbed corpus
both affected pairs already have genuine unmet requirements, so the gate fires for real
reasons and the spurious item hides behind them. It took a variant that repaired every
legitimate failure to leave the boilerplate item standing alone.

**A degenerate positive class does not merely skew a metric — it makes a whole class of
defects unobservable.** All 30 reference pairs deserved a gate, so no run could ever
demonstrate the gate firing for the wrong reason. This is the third-layer consequence of
[finding 004](004-gate-truth-imbalance.md)'s TN=0, and the strongest available argument for
why constructing negatives was worth the trouble even though the batch yielded only one.

## Change — NOT MADE

The fix for B is a **mechanism-class** intervention: a category exclusion in the extractor's
schema or prompt, rejecting availability and physical-capability items at extraction rather
than instructing the model to reason about what belongs in a ledger. Per
[finding 009](009-prose-binds-process-not-judgment.md), mechanism-class interventions have
held 3/3 against 0/2 for prose; this becomes the 6th intervention on that table and the 4th
mechanism-class one.

Deferred deliberately, and the ordering is the point: the extractor feeds **every**
`hard_requirements` verdict, not just the variants. Changing it before the batch ran would
have put two variables into every number at once — the perturbation and the exclusion rule —
leaving any anomaly unattributable, and would have invalidated every hard-related baseline
recorded since P0. It runs after the variant stage, as an independent single-variable
calibration with before/after, in the same window as finding 015's fix.

## Result — PENDING

Closes when the exclusion rule lands with its before/after numbers, and when A's overlap with
011 §3 is tested at the cross-model stage. Recorded now: `gn-01` stays a **live variant**
tagged `known_divergence` (agent–rubric divergence, not a construction failure), because its
construction was verified sound before the divergence was attributed to the agent.

## Design tension worth stating

The data boundary (trajectories carry no document text) and diagnosability (a trajectory
should explain its own verdict) are in direct conflict here. This project chose the boundary,
and the price is that a `hard_unmet` gate cannot say which item failed without going outside
the record.

A candidate resolution, **recorded as a change candidate and not implemented**: log the
requirement id together with a `(doc, start, end)` span reference into the JD, never the text.
Diagnosis slices the span from the local corpus; committed artifacts still carry no document
text. The evidence-span mechanism the assessment step already uses would extend to the ledger
unchanged.
