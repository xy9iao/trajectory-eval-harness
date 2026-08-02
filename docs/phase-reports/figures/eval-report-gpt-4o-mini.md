# Eval report — `passk-r20260802T144149-e8d83a.json`

- **batch kind**: batch
- **provider / model**: openai / gpt-4o-mini
- **runs in manifest**: 150
- **cases scored**: 150
- **excluded (validation)**: 0

### gate integrity

- **pairs_scored**: `30`
- **runs_scored**: `150`
- **confusion_across_all_runs_PRIMARY**: 
  - **TP**: 145
  - **FP**: 5
- **confusion_by_pair_majority_SECONDARY**: 
  - **TP**: 29
  - **FP**: 1
- **trigger_attribution_ok**: `14/29`
- **fired_for_wrong_reason**: `15`

- **stability (across-k)**: 0/30 pairs flip their gate decision across the k repeats. PRIMARY = across-all-runs (one run per decision, what the system does); SECONDARY = by-pair majority (the ceiling under a k=5 vote this system never performs). Reporting the majority figure alone would describe a fictional configuration (finding 011).

*15 pair(s) fired without matching the reference's gate reason: train:175 (ref ['anomaly', 'hard_unmet'] vs agent ['hard_indeterminate', 'hard_unmet', 'insufficient_evidence']); train:596 (ref ['hard_unmet'] vs agent ['hard_indeterminate', 'hard_unmet']); train:901 (ref ['hard_unmet'] vs agent ['hard_indeterminate', 'hard_unmet', 'insufficient_evidence']); train:970 (ref ['anomaly', 'hard_indeterminate', 'insufficient_evidence'] vs agent ['boundary', 'hard_indeterminate', 'hard_unmet', 'insufficient_evidence']); train:2980 (ref ['hard_unmet'] vs agent ['hard_indeterminate', 'hard_unmet', 'insufficient_evidence']); train:3148 (ref ['boundary', 'hard_indeterminate'] vs agent ['boundary', 'hard_indeterminate', 'hard_unmet']); train:3559 (ref ['hard_unmet'] vs agent ['hard_indeterminate', 'hard_unmet', 'insufficient_evidence']); train:3590 (ref ['boundary', 'hard_indeterminate'] vs agent ['hard_indeterminate', 'hard_unmet', 'insufficient_evidence']); train:3769 (ref ['anomaly', 'hard_unmet'] vs agent ['boundary', 'hard_indeterminate', 'hard_unmet', 'insufficient_evidence']); train:3773 (ref ['hard_unmet'] vs agent ['hard_indeterminate', 'hard_unmet', 'insufficient_evidence']); train:3978 (ref ['hard_unmet'] vs agent ['hard_indeterminate', 'hard_unmet', 'insufficient_evidence']); train:4890 (ref ['boundary', 'hard_indeterminate'] vs agent ['boundary', 'hard_indeterminate', 'hard_unmet', 'insufficient_evidence']); train:4928 (ref ['anomaly', 'hard_unmet'] vs agent ['hard_indeterminate', 'hard_unmet', 'insufficient_evidence']); train:5063 (ref ['hard_unmet'] vs agent ['hard_indeterminate', 'hard_unmet', 'insufficient_evidence']); train:5084 (ref ['boundary', 'hard_indeterminate'] vs agent ['boundary', 'hard_indeterminate', 'hard_unmet', 'insufficient_evidence'])*

<details><summary>rows (30 of 30)</summary>

- `{"pair": "train:175", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_unmet"]}`
- `{"pair": "train:400", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:596", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:901", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:935", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet", "insufficient_evidence"]}`
- `{"pair": "train:970", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_indeterminate", "insufficient_evidence"]}`
- `{"pair": "train:1050", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:1089", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_unmet"]}`
- `{"pair": "train:2189", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_unmet"]}`
- `{"pair": "train:2980", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:3148", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["boundary", "hard_indeterminate"]}`
- `{"pair": "train:3229", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_unmet"]}`
- `{"pair": "train:3559", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:3590", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["boundary", "hard_indeterminate"]}`
- `{"pair": "train:3769", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_unmet"]}`
- `{"pair": "train:3773", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:3800", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:3861", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:3978", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:4160", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["boundary", "hard_unmet"]}`
- `{"pair": "train:4715", "expected": false, "fired_across_k": "5/5", "cell": "FP", "stable": true, "reference_reasons": []}`
- `{"pair": "train:4890", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["boundary", "hard_indeterminate"]}`
- `{"pair": "train:4928", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_unmet"]}`
- `{"pair": "train:5063", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:5084", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["boundary", "hard_indeterminate"]}`
- `{"pair": "train:5699", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_unmet"]}`
- `{"pair": "train:5707", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_unmet"]}`
- `{"pair": "train:5798", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["boundary", "hard_unmet"]}`
- `{"pair": "train:6220", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["boundary", "hard_unmet"]}`
- `{"pair": "train:6236", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_unmet"]}`

</details>

### agreement (vs human reference)

- **comparisons**: `575`
- **overall_by_dimension**: 
  - `{"dimension": "skills_coverage", "exact": "78/149", "rate": 0.523}`
  - `{"dimension": "experience_level", "exact": "85/149", "rate": 0.57}`
  - `{"dimension": "education_domain_fit", "exact": "69/147", "rate": 0.469}`
  - `{"dimension": "hard_requirements", "exact": "110/130", "rate": 0.846}`
- **by_stratum**: 
  - `{"stratum": "adjacency_axis", "pairs": 11, "interpretable": true, "skills_coverage": "22/54", "experience_level": "36/54", "education_domain_fit": "6/54", "hard_requirements": "38/42"}`
  - `{"stratum": "skills_band_0_1", "pairs": 7, "interpretable": true, "skills_coverage": "22/35", "experience_level": "35/35", "education_domain_fit": "20/33", "hard_requirements": "28/28"}`
  - `{"stratum": "relevant_years_prior", "pairs": 1, "interpretable": false, "skills_coverage": "5/5 [insufficient for interpretation]", "experience_level": "0/5 [insufficient for interpretation]", "education_domain_fit": "5/5 [insufficient for interpretation]", "hard_requirements": "4/5 [insufficient for interpretation]"}`
  - `{"stratum": "experience_proximity", "pairs": 9, "interpretable": true, "skills_coverage": "22/45", "experience_level": "9/45", "education_domain_fit": "33/43", "hard_requirements": "31/41"}`
  - `{"stratum": "other", "pairs": 5, "interpretable": true, "skills_coverage": "11/25", "experience_level": "15/25", "education_domain_fit": "9/25", "hard_requirements": "18/23"}`
- **min_stratum_n_for_interpretation**: `5`

- **stability (across-k)**: one comparison per RUN (not per majority vote), so the rate is what the deployed single-run system achieves; read against finding 011's per-dimension variance floor — e.g. skills self-consistency 0.400 bounds how much of any agreement movement can be attributed to anything but variance.

*Strata are p0 §5b's first-pass classification, inherited not re-derived. Strata with fewer than 5 pairs are marked insufficient for interpretation: stratification exists to give low numbers an explanatory structure, not to produce more comparable numbers out of the same 30 pairs. 'Agreement' here always means agent vs human reference — never the model against itself (self-consistency).*

<details><summary>rows (30 of 120)</summary>

- `{"pair": "train:175", "dimension": "skills_coverage", "reference": 0, "agent_across_k": [0, 0, 0, 0, 0], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:175", "dimension": "experience_level", "reference": 1, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:175", "dimension": "education_domain_fit", "reference": 1, "agent_across_k": [3, 3, 3, 3, 1], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:175", "dimension": "hard_requirements", "reference": 0, "agent_across_k": [0, null, 0, 0, 0], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:400", "dimension": "skills_coverage", "reference": 3, "agent_across_k": [1, 1, 0, 1, 1], "strata": ["other"]}`
- `{"pair": "train:400", "dimension": "experience_level", "reference": 1, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["other"]}`
- `{"pair": "train:400", "dimension": "education_domain_fit", "reference": 3, "agent_across_k": [3, 3, 3, 3, 3], "strata": ["other"]}`
- `{"pair": "train:400", "dimension": "hard_requirements", "reference": 0, "agent_across_k": [0, 0, 0, 0, 0], "strata": ["other"]}`
- `{"pair": "train:596", "dimension": "skills_coverage", "reference": 1, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["relevant_years_prior"]}`
- `{"pair": "train:596", "dimension": "experience_level", "reference": 1, "agent_across_k": [3, 3, 3, 3, 3], "strata": ["relevant_years_prior"]}`
- `{"pair": "train:596", "dimension": "education_domain_fit", "reference": 3, "agent_across_k": [3, 3, 3, 3, 3], "strata": ["relevant_years_prior"]}`
- `{"pair": "train:596", "dimension": "hard_requirements", "reference": 0, "agent_across_k": [3, 0, 0, 0, 0], "strata": ["relevant_years_prior"]}`
- `{"pair": "train:901", "dimension": "skills_coverage", "reference": 0, "agent_across_k": [1, 0, 0, 0, 0], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:901", "dimension": "experience_level", "reference": 1, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:901", "dimension": "education_domain_fit", "reference": 1, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:901", "dimension": "hard_requirements", "reference": 0, "agent_across_k": [0, null, 0, 0, null], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:935", "dimension": "skills_coverage", "reference": 0, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["skills_band_0_1", "experience_proximity"]}`
- `{"pair": "train:935", "dimension": "experience_level", "reference": 3, "agent_across_k": [3, 3, 3, 3, 3], "strata": ["skills_band_0_1", "experience_proximity"]}`
- `{"pair": "train:935", "dimension": "education_domain_fit", "reference": 3, "agent_across_k": [3, 3, null, 3, 3], "strata": ["skills_band_0_1", "experience_proximity"]}`
- `{"pair": "train:935", "dimension": "hard_requirements", "reference": 0, "agent_across_k": [0, 0, 0, 0, 0], "strata": ["skills_band_0_1", "experience_proximity"]}`
- `{"pair": "train:970", "dimension": "skills_coverage", "reference": 5, "agent_across_k": [3, 3, 3, 3, 1], "strata": ["other"]}`
- `{"pair": "train:970", "dimension": "experience_level", "reference": 3, "agent_across_k": [3, 3, 3, 3, 3], "strata": ["other"]}`
- `{"pair": "train:970", "dimension": "education_domain_fit", "reference": 3, "agent_across_k": [3, 1, 3, 3, 3], "strata": ["other"]}`
- `{"pair": "train:970", "dimension": "hard_requirements", "reference": 3, "agent_across_k": [3, null, 0, 0, null], "strata": ["other"]}`
- `{"pair": "train:1050", "dimension": "skills_coverage", "reference": 1, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["experience_proximity"]}`
- `{"pair": "train:1050", "dimension": "experience_level", "reference": 5, "agent_across_k": [3, 3, 3, 3, 3], "strata": ["experience_proximity"]}`
- `{"pair": "train:1050", "dimension": "education_domain_fit", "reference": 3, "agent_across_k": [3, 3, 3, 3, 3], "strata": ["experience_proximity"]}`
- `{"pair": "train:1050", "dimension": "hard_requirements", "reference": 0, "agent_across_k": [0, 0, 0, 0, 0], "strata": ["experience_proximity"]}`
- `{"pair": "train:1089", "dimension": "skills_coverage", "reference": 0, "agent_across_k": [0, 0, 0, 0, 0], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:1089", "dimension": "experience_level", "reference": 1, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["skills_band_0_1"]}`

</details>

### pass^k

- **pairs_scored**: `30`
- **k_seen**: `[5]`
- **gate_all_agree**: `30/30`
- **gate_stability_rate**: `1.0`
- **recommendation_all_agree**: `30/30`
- **recommendation_stability_rate**: `1.0`

- **stability (across-k)**: This scorer IS the stability measurement — every figure it reports is already an across-k agreement rate, so there is no separate spread to declare. The note is stated rather than omitted because the contract is 'declare the basis', and silence is indistinguishable from having forgotten (the report runner flags a missing note for exactly that reason).
- **unstable pairs**: train:596, train:901, train:400, train:2189, train:175, train:935, train:2980, train:970, train:3229, train:3590, train:3861, train:3978, train:3559, train:3773, train:3769, train:3800, train:3148, train:5063, train:6220, train:4890, train:5798, train:4928, train:5084, train:4715, train:6236

*25 pair(s) flipped at least one dimension or the gate across runs; 0 case(s) excluded at load (validation failures).*

<details><summary>rows (4 of 4)</summary>

- `{"dimension": "skills_coverage", "all_agree": "18/30", "all_agree_rate": 0.6, "mean_within_pair_stdev": 0.252, "max_within_pair_stdev": 0.98, "pairs_with_a_degraded_run": 1, "per_pair_stdevs": [0.0, 0.4, 0.4, 0.0, 0.0, 0.0, 0.0, 0.8, 0.0, 0.0, 0.0, 0.8, 0.4, 0.0, 0.0, 0.0, 0.98, 0.0, 0.0, 0.0, 0.8, 0.8, 0.0, 0.98, 0.0, 0.0, 0.0, 0.0, 0.8, 0.4]}`
- `{"dimension": "experience_level", "all_agree": "25/30", "all_agree_rate": 0.833, "mean_within_pair_stdev": 0.113, "max_within_pair_stdev": 0.98, "pairs_with_a_degraded_run": 1, "per_pair_stdevs": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.98, 0.0, 0.0, 0.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.8, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}`
- `{"dimension": "education_domain_fit", "all_agree": "23/30", "all_agree_rate": 0.767, "mean_within_pair_stdev": 0.107, "max_within_pair_stdev": 0.8, "pairs_with_a_degraded_run": 3, "per_pair_stdevs": [0.0, 0.0, 0.0, 0.8, 0.8, 0.0, 0.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}`
- `{"dimension": "hard_requirements", "all_agree": "13/30", "all_agree_rate": 0.433, "mean_within_pair_stdev": 0.31, "max_within_pair_stdev": 1.47, "pairs_with_a_degraded_run": 12, "per_pair_stdevs": [1.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.414, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.2, 0.0, 1.47, 1.2, 0.0, 0.0, 1.299, 0.0, 1.2, 0.0]}`

</details>

### ledger consistency

- **runs_scored**: `150`
- **pairs_scored**: `30`
- **contradictions_total**: `7`
- **pairs_with_any_contradiction**: `6/30`
- **contradictions_per_run**: `0.047`

- **stability (across-k)**: contradiction counts vary across the k repeats on 6/30 pairs; the headline is the total over all runs, not a single-run snapshot.
- **unstable pairs**: train:1050 ([1, 0, 0, 0, 0]), train:3229 ([1, 1, 0, 0, 0]), train:3773 ([0, 0, 0, 0, 1]), train:4715 ([0, 0, 0, 0, 1]), train:4890 ([0, 0, 1, 0, 0]), train:5084 ([1, 0, 0, 0, 0])

*Consistency is not correctness: a run can be clean here by being consistently wrong (finding 008, train 596 after the consistency prompt). Pair with the agreement scorers; never merge them. COMPARABILITY: totals here are over ALL runs in the corpus, while finding 008's figures (8 contradictions / 7 pairs pre-calibration, 2 / 1 pair post) came from single 30-run batches — the two are only comparable as per-run rates (008 post-calibration: 2/30 = 0.067 per run), never as raw counts.*

<details><summary>rows (7 of 7)</summary>

- `{"pair": "train:1050", "run_id": "r20260802T141525-d6daf1", "requirement": "R1", "source_dimension": "skills_coverage", "source_value": "covered", "ledger_value": "absent"}`
- `{"pair": "train:3229", "run_id": "r20260802T141706-244993", "requirement": "R1", "source_dimension": "skills_coverage", "source_value": "partial", "ledger_value": "absent"}`
- `{"pair": "train:3229", "run_id": "r20260802T141720-6683b3", "requirement": "R1", "source_dimension": "skills_coverage", "source_value": "partial", "ledger_value": "absent"}`
- `{"pair": "train:3773", "run_id": "r20260802T142435-1b01d9", "requirement": "R1", "source_dimension": "skills_coverage", "source_value": "partial", "ledger_value": "absent"}`
- `{"pair": "train:4715", "run_id": "r20260802T144054-c340a6", "requirement": "R6", "source_dimension": "skills_coverage", "source_value": "covered", "ledger_value": "absent"}`
- `{"pair": "train:4890", "run_id": "r20260802T143216-0b69f0", "requirement": "R11", "source_dimension": "skills_coverage", "source_value": "covered", "ledger_value": "absent"}`
- `{"pair": "train:5084", "run_id": "r20260802T143709-6400de", "requirement": "R4", "source_dimension": "skills_coverage", "source_value": "covered", "ledger_value": "absent"}`

</details>

### tool-call correctness

- **runs_scored**: `150`
- **structurally_correct**: `150/150`
- **rate**: `1.0`

- **stability (across-k)**: computed per run over all repeats; no single-run snapshot is involved.

*Reuses the trajectory validator's invariants; measures rate, not legality.*

### evidence coverage (sentinel)

- **assessments_with_determinations**: `278`
- **over_threshold**: `22/278`
- **threshold**: `5.0x determinations per evidence span`
- **over_threshold_by_dimension**: 
  - **skills_coverage**: 15
  - **hard_requirements**: 7
- **assessments_with_zero_spans**: `0`

- **stability (across-k)**: computed per assessment over all repeats; a pair may be flagged in some runs and not others, which is itself informative — the flag list carries run_ids.

*SENTINEL, NOT A FAITHFULNESS METRIC: a flag means 'this assessment warrants human inspection', never 'this assessment is unfaithful'. A high ratio can be legitimate (one passage genuinely covering many must-items) and a normal ratio can still be unfaithful (right count, wrong category of evidence — finding 013). Report the flag count and where they cluster; never report the raw ratio as a score. Primary use: the sampling pool for faithfulness spot-checks (eval-design 3d).*

<details><summary>rows (22 of 22)</summary>

- `{"run_id": "r20260802T141101-b6d2e5", "pair": "train:2189", "dimension": "skills_coverage", "determinations": 6, "evidence_spans": 1, "ratio": 6.0}`
- `{"run_id": "r20260802T141720-6683b3", "pair": "train:3229", "dimension": "skills_coverage", "determinations": 12, "evidence_spans": 1, "ratio": 12.0}`
- `{"run_id": "r20260802T141736-5c68fd", "pair": "train:3229", "dimension": "skills_coverage", "determinations": 11, "evidence_spans": 2, "ratio": 5.5}`
- `{"run_id": "r20260802T141806-2ebf4c", "pair": "train:3229", "dimension": "skills_coverage", "determinations": 11, "evidence_spans": 2, "ratio": 5.5}`
- `{"run_id": "r20260802T142107-cfa142", "pair": "train:3978", "dimension": "skills_coverage", "determinations": 12, "evidence_spans": 2, "ratio": 6.0}`
- `{"run_id": "r20260802T142133-624c3b", "pair": "train:3978", "dimension": "skills_coverage", "determinations": 12, "evidence_spans": 2, "ratio": 6.0}`
- `{"run_id": "r20260802T142207-3ee2d2", "pair": "train:3978", "dimension": "skills_coverage", "determinations": 11, "evidence_spans": 2, "ratio": 5.5}`
- `{"run_id": "r20260802T142446-75d3bf", "pair": "train:3769", "dimension": "hard_requirements", "determinations": 6, "evidence_spans": 1, "ratio": 6.0}`
- `{"run_id": "r20260802T142526-e52c34", "pair": "train:3769", "dimension": "skills_coverage", "determinations": 10, "evidence_spans": 1, "ratio": 10.0}`
- `{"run_id": "r20260802T142723-024c73", "pair": "train:3800", "dimension": "skills_coverage", "determinations": 11, "evidence_spans": 2, "ratio": 5.5}`
- `{"run_id": "r20260802T142735-68b339", "pair": "train:3800", "dimension": "skills_coverage", "determinations": 12, "evidence_spans": 2, "ratio": 6.0}`
- `{"run_id": "r20260802T142750-a950f9", "pair": "train:3800", "dimension": "skills_coverage", "determinations": 12, "evidence_spans": 2, "ratio": 6.0}`
- `{"run_id": "r20260802T142803-94c075", "pair": "train:3800", "dimension": "skills_coverage", "determinations": 11, "evidence_spans": 2, "ratio": 5.5}`
- `{"run_id": "r20260802T143306-e30a04", "pair": "train:5798", "dimension": "hard_requirements", "determinations": 7, "evidence_spans": 1, "ratio": 7.0}`
- `{"run_id": "r20260802T143324-f1621b", "pair": "train:5798", "dimension": "hard_requirements", "determinations": 7, "evidence_spans": 1, "ratio": 7.0}`
- `{"run_id": "r20260802T143425-cf1a83", "pair": "train:5798", "dimension": "hard_requirements", "determinations": 6, "evidence_spans": 1, "ratio": 6.0}`
- `{"run_id": "r20260802T143436-43ef36", "pair": "train:5699", "dimension": "skills_coverage", "determinations": 11, "evidence_spans": 1, "ratio": 11.0}`
- `{"run_id": "r20260802T143516-fd2f6a", "pair": "train:5699", "dimension": "hard_requirements", "determinations": 13, "evidence_spans": 2, "ratio": 6.5}`
- `{"run_id": "r20260802T143658-4ab3ac", "pair": "train:4928", "dimension": "hard_requirements", "determinations": 6, "evidence_spans": 1, "ratio": 6.0}`
- `{"run_id": "r20260802T143829-ad9dc8", "pair": "train:5707", "dimension": "skills_coverage", "determinations": 11, "evidence_spans": 2, "ratio": 5.5}`
- `{"run_id": "r20260802T143849-34bb49", "pair": "train:5707", "dimension": "skills_coverage", "determinations": 12, "evidence_spans": 2, "ratio": 6.0}`
- `{"run_id": "r20260802T144149-e8d83a", "pair": "train:6236", "dimension": "hard_requirements", "determinations": 10, "evidence_spans": 1, "ratio": 10.0}`

</details>

