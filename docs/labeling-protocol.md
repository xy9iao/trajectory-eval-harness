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

## 7. Appendix — operator walkthrough (the detailed per-pair workflow)

§5 is the normative sequence; this appendix is the keystroke-level version. Budget ~20 min/pair
for the first few, ~10 once fluent. Work in `sample-v1.json` order.

### One-time setup

```bash
uv run python data/download_dataset.py     # verifies the pinned CSVs + checksums
```

### The cockpit (primary path)

`data/label_pairs.py` drives steps 1–9 interactively and appends the JSONL line itself:

```bash
uv run python data/label_pairs.py              # next unlabeled sample pair
uv run python data/label_pairs.py --row 596    # a specific sampled pair
uv run python data/label_pairs.py --mentor     # mentor subset -> labels-v1-mentor.jsonl
```

Division of labor (the tool's legitimacy boundary, stated once): the cockpit automates
**rendering** (pair display with `<<<` candidate-requirement highlights from the recorded
`profile_jd_requirements` patterns — candidates only, never a must-item decision),
**span capture** (search → pick → verified offsets, the `--find`/`--span` loop inline), and
**rubric-defined arithmetic** (band geometry, ledger → score, weighted mean, veto, and the
`hard_unmet`/`hard_indeterminate` gate reasons — all unit-tested in
`tests/test_label_cockpit.py`). Every judgment is typed by the annotator: must items,
determinations, evidence strengths, manual scores, the other gate reasons, hesitations.
Derived values require explicit confirmation; **overriding a derived value records the reason
as a hesitation automatically** — overrides are rubric-revision material, not friction.
Blind by construction: the cockpit reads only its own output file, so a `--mentor` session
never sees the owner's labels.

The steps below remain normative — they are what the cockpit walks you through, and the
manual `view_pair` path (worksheet first, JSONL last) stays valid as a fallback.

### Rubric map — what to have open at each step

Before the **first session** (once, ~15 min): read `rubrics/rubric-v1.yaml` top to bottom —
especially `scale.meaning` (what 0/3/5 mean generically) and the `aggregation` comment (why
hard_requirements never enters the mean). After that, you consult sections, not the whole file:

| Step | You are deciding | Open this section of rubric-v1.yaml |
|---|---|---|
| 1 JD pass | what is a must item; is this a bundle; which dimension owns it | `skills_coverage.scope_notes` — years→experience_level, degrees→education_domain_fit, preferred never moves the band (stance A); `coverage_determination` intro — a bundle is ONE determination |
| 2 resume pass | evidence strength: hands-on / keyword / adjacent / none | `skills_coverage.criteria` bands "5" vs "3" — hands-on = used in a project/work entry, keyword = skills-list mention; adjacency defined in `design_notes` (transferable capability, never top band); bootcamp evidence counts here (`scope_notes`) |
| 3 skills_coverage | determination covered/partial/absent, then the band | `coverage_determination` (three discrete values; partial caps at 2; majority-absent = absent); the band-geometry comment above `criteria` (5/4/3/2/1/0); calibrate against the score-1 anchor (train 4699) |
| 4 experience_level | which resume segments count; how close is close | `experience_level.scope_notes` — evidenced years only, Summary self-claims never count, role-matching segments only; proximity not pass/fail (the ledger lives in hard_requirements); calibrate against the score-3 anchor (train 4699) |
| 5 education_domain_fit | the JD's occupation; level + field fit | `education_domain_fit.scope_notes` — occupation-relative, industry verticals excluded, bootcamps are not degrees; `criteria` band 3 — related-rather-than-core is ALWAYS a 3, no sub-grading (`design_notes`, rule isomorphism); score-3 anchor (train 4699) |
| 6 hard_requirements | met / indeterminate / unmet per must item | `hard_requirements.criteria` — 3 means "the text cannot settle it", never partial credit; 4-of-5 met still scores 0 (the ledger has no ratio); both score-0 anchors (train 4699, train 3143) |
| 7 aggregate + gate | veto handling; gate reasons | `aggregation` + `soft_veto` wiring (0 → cap+gate, 3 → gate-only, 5 → nothing); then §4 of this protocol for the reason codes |
| 8 hesitations | is my discomfort a rubric problem? | the dimension's `design_notes` — if your hesitation contradicts a recorded design decision, say so explicitly: that is a rubric-revision candidate, the most valuable line you can write |

**When a band call is genuinely unclear, escalate in this order** (stop at the first rung that
settles it):

1. **criteria** — the band texts themselves;
2. **scope_notes** — does the ambiguity actually belong to another dimension?
3. **design_notes** — the recorded *why*; often resolves "spirit vs letter" calls;
4. **anchors** — put your pair next to the anchor's facts and reasoning: is your case stronger
   or weaker than the anchored score?
5. still torn → score the band you could best defend out loud, write the hesitation, move on.
   **Never redesign the rubric mid-pair** — revisions happen between sessions, versioned, with
   already-labeled pairs re-checked (§1).

**Step 1 — JD pass (resume stays closed).**
`view_pair {split} {row} --doc jd`. Write down:
- the JD's occupation (sanity-check against the sample's `occupation` bucket);
- every **must/required item**, one worksheet row each — tag it `skills` / `years` / `degree` /
  `other`; a bundle ("Docker, Kubernetes, Microservices") is ONE row. Preferred/nice-to-have
  items are noted but never move any band (stance A);
- **if the JD states no must-have skills**: derive skill requirements from the duties section
  (rubric v1.1 derived-musts rule, `skills_coverage.scope_notes`) — one `skills` row per
  duties sentence naming concrete tools/technologies, note "derived" in the paraphrase;
- the JD span for each item (`--find "..."` → offsets; `--span` to verify).

**Step 2 — resume pass.** Read the whole resume once (`--doc resume`), then per must item:
locate evidence (`--find`), verify the slice (`--span`), and classify its strength —
**hands-on** (dated work/project entry showing use) / **keyword** (skills-list mention) /
**adjacent** (transferable, e.g. PostgreSQL for MySQL) / **none**. Search synonyms before
concluding "none" (K8s/Kubernetes, BS/Bachelor, GCP/Google Cloud).

**Step 3 — skills_coverage.** Per skills row: determination `covered` (every component ≥
keyword or adjacent) / `partial` (some components present, some absent) / `absent` (majority of
components missing). Then the band is mechanical: 5 all-covered-all-hands-on · 4 all-covered-
majority-hands-on · 3 all-covered-keyword-dominant · 2 any partial · 1 any absent · 0 broadly
absent. Adjacency caps its requirement's contribution at mid-band.

**Step 4 — experience_level.** List the resume's dated, role-matching segments (Summary
self-claims never count); sum evidenced years against the JD's ask. 5 meets/exceeds · 3 real
experience, real gap · 1 no role-matching dated segments. Proximity, not pass/fail — a
veto-firing gap can still be a 3.

**Step 5 — education_domain_fit.** Degree level + field vs the JD's occupation. 5 both fit ·
3 one clean + one adjacent (related-rather-than-core is always a 3 — no sub-grading) · 1
neither. Bootcamps are not degrees here.

**Step 6 — hard_requirements ledger.** Re-walk every must item reusing steps 3–5's
determinations: all met → 5 · any that the text cannot settle → 3 (indeterminate — never
partial credit) · any clearly unmet → 0.

**Step 7 — aggregate + gate.**
`weighted_mean = 0.5·skills + 0.3·experience + 0.2·education` (hard_requirements never enters);
`veto` = unmet/indeterminate/met. Then `gate_expected` per §4 — reason codes in worksheet
order: veto first (`hard_unmet`/`hard_indeterminate`), then `boundary`, `insufficient_evidence`,
`anomaly`.

**Step 8 — hesitations, same session.** Anything you re-read twice, any band you could defend
two ways, any criteria gap — one line each. An empty `hesitations` on a hard pair is a smell.

**Step 9 — transcribe to JSONL** (schema §3) and validate before moving on:

```bash
uv run python - <<'EOF'
import json
from pathlib import Path
REQUIRED = {"pair", "dataset_label", "occupation", "dimensions", "aggregate",
            "gate_expected", "gate_reasons", "hesitations", "labeled_at"}
lines = Path("data/reference/labels-v1.jsonl").read_text(encoding="utf-8").splitlines()
for n, line in enumerate(lines, 1):
    rec = json.loads(line)
    missing = REQUIRED - rec.keys()
    assert not missing, f"line {n}: missing {missing}"
print(f"{len(lines)} records OK")
EOF
```

**Cadence:** commit at the end of each labeling session (message: which rows). After the first
3 pairs, pause for a schema/rubric-application review before continuing.

## 8. Reproducibility statement

A second annotator with this document, the pinned CSVs, and rubric v1 must be able to (a)
regenerate the same 30-pair sample (seeded script), (b) locate every cited span
(`view_pair --span`), and (c) follow the same determination rules. Divergence in (c) is
signal, not failure — it feeds the disagreement analysis.
