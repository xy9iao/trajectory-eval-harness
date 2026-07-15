# Labeling protocol — P0 reference set (v1)

Reproducible procedure for producing the ~30-pair labeled reference set (roadmap P0 item 4).
The owner labels; CC never fills in a score (owner-judgment work, CLAUDE.md §Role). The
resulting file is the ground truth for P2's per-dimension agreement analysis and the
gate-integrity confusion matrix.

## 1. Conventions

- **Row identity is 0-based iloc**: index 0 is the first *data* row of the pinned CSV (the
  header row is not counted) — the same convention as `data/view_pair.py` and the rubric's
  anchors. An index is only meaningful against the byte-identical CSVs that
  `data/download_dataset.py` pins and checksums (dataset revision `08978e2…`).
- **No raw text ever enters the reference file** (Decision 5: the dataset is unlicensed).
  Pairs are referenced by `split + row`; evidence is referenced by character offsets into the
  raw document string, verified with `view_pair --find` / `--span`.
- Reading/verification tool: `python data/view_pair.py {split} {row} [--doc jd|resume]
  [--find TEXT | --span START:END]`.
- Rubric: `rubrics/rubric-v1.yaml` at `status: active`. If labeling forces a rubric change,
  the change lands as a versioned revision (v1 → v1.x) with a revision-log entry *before*
  affected pairs are relabeled — never silently.

## 2. Sampling (stratified, seeded)

30 pairs from `train.csv`, selected by `data/sample_reference_pairs.py` (fixed seed recorded
in the script; output is deterministic):

- **Stratum axis 1 — dataset label:** 10 pairs each from No Fit / Potential Fit / Good Fit.
  The dataset label is *not* our ground truth (see the row-4699 disagreement sample); it is a
  stratification device so the reference set spans the dataset's own difficulty range.
- **Stratum axis 2 — occupation bucket:** within each label class, round-robin across the
  occupation buckets of the 001 corpus scan (`data/profile_jd_domains.py` keyword lists), so
  the set is cross-occupation like the corpus (accounting/fin is the largest bucket; software
  is a minority — finding 001). A pair's bucket is the first bucket whose term list matches
  its JD; JDs matching no bucket are eligible and recorded as `occupation: none`.
- **No two sampled pairs share a JD** (280 unique JDs across 6,241 rows — reuse is heavy;
  sampling across JDs is a roadmap requirement).
- **Rubric anchor pairs are excluded** (train 4699, train 3143): they defined the scale, so
  scoring them against it is circular — they can't measure whether the rubric transfers.
  *(CC-proposed rule — owner ratifies with this PR.)*

## 3. Per-pair record (JSONL, one line per pair)

File: `data/reference/labels-v1.jsonl` (committed — indices and offsets only). Fields:

```json
{
  "pair": {"split": "train", "row": 0},
  "dataset_label": "Good Fit",
  "occupation": "software eng",
  "dimensions": {
    "skills_coverage": {
      "score": 3,
      "determinations": [
        {"requirement": "short paraphrase", "value": "covered|partial|absent"}
      ],
      "evidence_spans": [{"doc": "jd", "start": 0, "end": 0}],
      "notes": ""
    },
    "experience_level": {"score": 3, "evidence_spans": [], "notes": ""},
    "hard_requirements": {"score": 0, "evidence_spans": [], "notes": ""},
    "education_domain_fit": {"score": 3, "evidence_spans": [], "notes": ""}
  },
  "aggregate": {"weighted_mean": 3.0, "veto": "unmet"},
  "gate_expected": true,
  "gate_reasons": ["hard_unmet"],
  "hesitations": "",
  "labeled_at": "2026-07-15"
}
```

Rules:

- Every dimension score cites ≥1 evidence span (the same discipline the agent is held to);
  a score with no locatable span is itself a `hesitations` entry.
- `determinations` is required for `skills_coverage` (the discrete covered/partial/absent
  judgment per must-have requirement); other dimensions use `notes`.
- `aggregate.weighted_mean` runs over the three scoring dimensions only (0.5/0.3/0.2);
  `aggregate.veto` mirrors hard_requirements: `unmet` (0) / `indeterminate` (3) / `met` (5).

## 4. `gate_expected` — ground truth for the P2 gate-integrity scorer

`gate_expected` answers: *should a correctly designed gate flag this pair for human review?*
It is owner judgment against the rubric, not a prediction of the P1 gate's thresholds (those
are tuned later — against exactly this field). `gate_reasons` is a list (several can apply):

| code | meaning | source |
|---|---|---|
| `hard_unmet` | hard_requirements = 0 → soft veto fires (cap + gate) | veto wiring, sub-class 1 |
| `hard_indeterminate` | hard_requirements = 3 → cannot decide from the text → gate | veto wiring, sub-class 2 |
| `boundary` | aggregate sits where advance/reject could defensibly go either way | roadmap "boundary score" |
| `insufficient_evidence` | some dimension was scored on thin or missing evidence | roadmap |
| `anomaly` | empty/garbled document, suspected injection, structurally broken pair | roadmap |

The `hard_unmet` / `hard_indeterminate` sub-classification is deliberate: the two veto
triggers are distinct gate behaviors (cap+gate vs gate-only), so P2's confusion matrix can be
decomposed by trigger type.

`gate_expected: false` requires all of: veto `met`, no boundary call, evidence adequate, no
anomaly.

## 5. Procedure (per pair)

1. `view_pair {split} {row}` — read the JD first; list its must/required items before
   opening the resume (prevents anchoring on the candidate).
2. Read the resume; for each must item record the discrete determination with spans
   (`--find` to locate, `--span` to verify).
3. Score the four dimensions in rubric order, spans first, score second.
4. Compute `weighted_mean` and `veto`; set `gate_expected` + `gate_reasons` per §4.
5. Anything that made you hesitate — ambiguous band, criteria gap, unbandable case — goes in
   `hesitations` *the same session*. Hesitations are the raw feed for the rubric revision log
   and the P0 report's "rubric problems surfaced during labeling" section.
6. Append the JSONL line; never edit an already-committed line except through a versioned
   correction (new commit, reason in the message).

## 6. Mentor review subset (touchpoint 1)

10 of the 30, selected by the same script (seeded sub-sample; 3/3/4 across label classes,
occupation-spread). The mentor receives pair references + rubric only — **not** the owner's
scores (blind review; otherwise agreement numbers measure persuasion, not the rubric). Mentor
labels go in `data/reference/labels-v1-mentor.jsonl`, same schema; the agreement analysis
(which pairs diverged, on which dimensions, how resolved) is p0 report §5.

## 7. Reproducibility statement

A second annotator with this document, the pinned CSVs, and rubric v1 must be able to (a)
regenerate the same 30-pair sample (seeded script), (b) locate every cited span
(`view_pair --span`), and (c) follow the same determination rules. Divergence in (c) is
signal, not failure — it feeds the disagreement analysis.
