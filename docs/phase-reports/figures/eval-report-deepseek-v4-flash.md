# Eval report — `passk-r20260728T035619-2d6bcd.json`

- **batch kind**: batch
- **provider / model**: deepseek / deepseek-v4-flash
- **runs in manifest**: 150
- **cases scored**: 150
- **excluded (validation)**: 0

### gate integrity

- **pairs_scored**: `30`
- **runs_scored**: `150`
- **confusion_across_all_runs_PRIMARY**: 
  - **TP**: 139
  - **FN**: 6
  - **FP**: 5
- **confusion_by_pair_majority_SECONDARY**: 
  - **TP**: 28
  - **FP**: 1
  - **FN**: 1
- **trigger_attribution_ok**: `21/28`
- **fired_for_wrong_reason**: `7`

- **stability (across-k)**: 4/30 pairs flip their gate decision across the k repeats. PRIMARY = across-all-runs (one run per decision, what the system does); SECONDARY = by-pair majority (the ceiling under a k=5 vote this system never performs). Reporting the majority figure alone would describe a fictional configuration (finding 011).
- **unstable pairs**: train:596, train:970, train:5084, train:6220

*7 pair(s) fired without matching the reference's gate reason: train:400 (ref ['hard_unmet'] vs agent ['hard_indeterminate', 'hard_unmet', 'insufficient_evidence']); train:596 (ref ['hard_unmet'] vs agent ['boundary', 'hard_indeterminate', 'hard_unmet']); train:970 (ref ['anomaly', 'hard_indeterminate', 'insufficient_evidence'] vs agent ['boundary', 'hard_indeterminate', 'hard_unmet']); train:3148 (ref ['boundary', 'hard_indeterminate'] vs agent ['boundary', 'hard_unmet']); train:3590 (ref ['boundary', 'hard_indeterminate'] vs agent ['boundary', 'hard_indeterminate', 'hard_unmet']); train:3773 (ref ['hard_unmet'] vs agent ['boundary', 'hard_indeterminate', 'hard_unmet']); train:6220 (ref ['boundary', 'hard_unmet'] vs agent ['hard_unmet'])*

<details><summary>rows (30 of 30)</summary>

- `{"pair": "train:175", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_unmet"]}`
- `{"pair": "train:400", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:596", "expected": true, "fired_across_k": "4/5", "cell": "TP", "stable": false, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:901", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet"]}`
- `{"pair": "train:935", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["hard_unmet", "insufficient_evidence"]}`
- `{"pair": "train:970", "expected": true, "fired_across_k": "4/5", "cell": "TP", "stable": false, "reference_reasons": ["anomaly", "hard_indeterminate", "insufficient_evidence"]}`
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
- `{"pair": "train:5084", "expected": true, "fired_across_k": "2/5", "cell": "FN", "stable": false, "reference_reasons": ["boundary", "hard_indeterminate"]}`
- `{"pair": "train:5699", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_unmet"]}`
- `{"pair": "train:5707", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_unmet"]}`
- `{"pair": "train:5798", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["boundary", "hard_unmet"]}`
- `{"pair": "train:6220", "expected": true, "fired_across_k": "4/5", "cell": "TP", "stable": false, "reference_reasons": ["boundary", "hard_unmet"]}`
- `{"pair": "train:6236", "expected": true, "fired_across_k": "5/5", "cell": "TP", "stable": true, "reference_reasons": ["anomaly", "hard_unmet"]}`

</details>

### agreement (vs human reference)

- **comparisons**: `595`
- **overall_by_dimension**: 
  - `{"dimension": "skills_coverage", "exact": "43/150", "rate": 0.287}`
  - `{"dimension": "experience_level", "exact": "85/149", "rate": 0.57}`
  - `{"dimension": "education_domain_fit", "exact": "87/147", "rate": 0.592}`
  - `{"dimension": "hard_requirements", "exact": "119/149", "rate": 0.799}`
- **by_stratum**: 
  - `{"stratum": "adjacency_axis", "pairs": 11, "interpretable": true, "skills_coverage": "16/55", "experience_level": "36/54", "education_domain_fit": "19/55", "hard_requirements": "43/55"}`
  - `{"stratum": "skills_band_0_1", "pairs": 7, "interpretable": true, "skills_coverage": "3/35", "experience_level": "33/35", "education_domain_fit": "30/35", "hard_requirements": "35/35"}`
  - `{"stratum": "relevant_years_prior", "pairs": 1, "interpretable": false, "skills_coverage": "2/5 [insufficient for interpretation]", "experience_level": "1/5 [insufficient for interpretation]", "education_domain_fit": "4/5 [insufficient for interpretation]", "hard_requirements": "2/5 [insufficient for interpretation]"}`
  - `{"stratum": "experience_proximity", "pairs": 9, "interpretable": true, "skills_coverage": "15/45", "experience_level": "10/45", "education_domain_fit": "33/45", "hard_requirements": "35/45"}`
  - `{"stratum": "other", "pairs": 5, "interpretable": true, "skills_coverage": "10/25", "experience_level": "15/25", "education_domain_fit": "10/22", "hard_requirements": "19/24"}`
- **min_stratum_n_for_interpretation**: `5`

- **stability (across-k)**: one comparison per RUN (not per majority vote), so the rate is what the deployed single-run system achieves; read against finding 011's per-dimension variance floor — e.g. skills self-consistency 0.400 bounds how much of any agreement movement can be attributed to anything but variance.

*Strata are p0 §5b's first-pass classification, inherited not re-derived. Strata with fewer than 5 pairs are marked insufficient for interpretation: stratification exists to give low numbers an explanatory structure, not to produce more comparable numbers out of the same 30 pairs. 'Agreement' here always means agent vs human reference — never the model against itself (self-consistency).*

<details><summary>rows (30 of 120)</summary>

- `{"pair": "train:175", "dimension": "skills_coverage", "reference": 0, "agent_across_k": [1, 1, 0, 1, 1], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:175", "dimension": "experience_level", "reference": 1, "agent_across_k": [1, 3, 1, 1, 1], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:175", "dimension": "education_domain_fit", "reference": 1, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:175", "dimension": "hard_requirements", "reference": 0, "agent_across_k": [0, 0, 0, 0, 0], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:400", "dimension": "skills_coverage", "reference": 3, "agent_across_k": [1, 1, 1, 0, 1], "strata": ["other"]}`
- `{"pair": "train:400", "dimension": "experience_level", "reference": 1, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["other"]}`
- `{"pair": "train:400", "dimension": "education_domain_fit", "reference": 3, "agent_across_k": [3, 1, 1, 3, 3], "strata": ["other"]}`
- `{"pair": "train:400", "dimension": "hard_requirements", "reference": 0, "agent_across_k": [0, 0, 0, 0, null], "strata": ["other"]}`
- `{"pair": "train:596", "dimension": "skills_coverage", "reference": 1, "agent_across_k": [1, 3, 3, 1, 0], "strata": ["relevant_years_prior"]}`
- `{"pair": "train:596", "dimension": "experience_level", "reference": 1, "agent_across_k": [3, 3, 3, 3, 1], "strata": ["relevant_years_prior"]}`
- `{"pair": "train:596", "dimension": "education_domain_fit", "reference": 3, "agent_across_k": [3, 1, 3, 3, 3], "strata": ["relevant_years_prior"]}`
- `{"pair": "train:596", "dimension": "hard_requirements", "reference": 0, "agent_across_k": [0, 3, 5, 0, 5], "strata": ["relevant_years_prior"]}`
- `{"pair": "train:901", "dimension": "skills_coverage", "reference": 0, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:901", "dimension": "experience_level", "reference": 1, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:901", "dimension": "education_domain_fit", "reference": 1, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:901", "dimension": "hard_requirements", "reference": 0, "agent_across_k": [0, 0, 0, 0, 0], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:935", "dimension": "skills_coverage", "reference": 0, "agent_across_k": [1, 1, 3, 3, 1], "strata": ["skills_band_0_1", "experience_proximity"]}`
- `{"pair": "train:935", "dimension": "experience_level", "reference": 3, "agent_across_k": [3, 3, 3, 3, 3], "strata": ["skills_band_0_1", "experience_proximity"]}`
- `{"pair": "train:935", "dimension": "education_domain_fit", "reference": 3, "agent_across_k": [3, 3, 3, 3, 3], "strata": ["skills_band_0_1", "experience_proximity"]}`
- `{"pair": "train:935", "dimension": "hard_requirements", "reference": 0, "agent_across_k": [0, 0, 0, 0, 0], "strata": ["skills_band_0_1", "experience_proximity"]}`
- `{"pair": "train:970", "dimension": "skills_coverage", "reference": 5, "agent_across_k": [3, 3, 5, 3, 3], "strata": ["other"]}`
- `{"pair": "train:970", "dimension": "experience_level", "reference": 3, "agent_across_k": [4, 3, 3, 4, 3], "strata": ["other"]}`
- `{"pair": "train:970", "dimension": "education_domain_fit", "reference": 3, "agent_across_k": [3, 1, 3, 1, 1], "strata": ["other"]}`
- `{"pair": "train:970", "dimension": "hard_requirements", "reference": 3, "agent_across_k": [5, 3, 5, 0, 5], "strata": ["other"]}`
- `{"pair": "train:1050", "dimension": "skills_coverage", "reference": 1, "agent_across_k": [1, 2, 3, 1, 1], "strata": ["experience_proximity"]}`
- `{"pair": "train:1050", "dimension": "experience_level", "reference": 5, "agent_across_k": [3, 3, 3, 3, 3], "strata": ["experience_proximity"]}`
- `{"pair": "train:1050", "dimension": "education_domain_fit", "reference": 3, "agent_across_k": [3, 3, 3, 3, 3], "strata": ["experience_proximity"]}`
- `{"pair": "train:1050", "dimension": "hard_requirements", "reference": 0, "agent_across_k": [0, 0, 0, 0, 0], "strata": ["experience_proximity"]}`
- `{"pair": "train:1089", "dimension": "skills_coverage", "reference": 0, "agent_across_k": [1, 0, 1, 1, 1], "strata": ["skills_band_0_1"]}`
- `{"pair": "train:1089", "dimension": "experience_level", "reference": 1, "agent_across_k": [1, 1, 1, 1, 1], "strata": ["skills_band_0_1"]}`

</details>

### pass^k

- **pairs_scored**: `30`
- **k_seen**: `[5]`
- **gate_identical_across_k**: `26/30`
- **gate_self_consistency_rate**: `0.867`
- **recommendation_identical_across_k**: `26/30`
- **recommendation_self_consistency_rate**: `0.867`

- **stability (across-k)**: This scorer IS the stability measurement — every figure it reports is already an across-k self-consistency rate, so there is no separate spread to declare. The note is stated rather than omitted because the contract is 'declare the basis', and silence is indistinguishable from having forgotten (the report runner flags a missing note for exactly that reason).
- **unstable pairs**: train:596, train:400, train:2189, train:175, train:935, train:2980, train:970, train:1089, train:1050, train:3229, train:3590, train:3861, train:3978, train:3559, train:3773, train:3769, train:4160, train:3800, train:3148, train:5063, train:6220, train:4890, train:5798, train:5699, train:4928, train:5084, train:5707, train:4715

*28 pair(s) flipped at least one dimension or the gate across runs; 0 case(s) excluded at load (validation failures).*

<details><summary>rows (4 of 4)</summary>

- `{"dimension": "skills_coverage", "identical_across_k": "12/30", "self_consistency_rate": 0.4, "mean_within_pair_stdev": 0.445, "max_within_pair_stdev": 1.2, "pairs_with_a_degraded_run": 0, "per_pair_stdevs": [1.2, 0.0, 0.4, 0.0, 0.4, 0.98, 0.0, 0.8, 0.4, 0.8, 0.8, 0.0, 0.4, 0.0, 0.8, 0.98, 0.4, 0.8, 0.0, 0.0, 0.8, 0.98, 0.0, 0.8, 0.8, 0.0, 0.8, 0.0, 0.0, 0.0]}`
- `{"dimension": "experience_level", "identical_across_k": "17/30", "self_consistency_rate": 0.567, "mean_within_pair_stdev": 0.345, "max_within_pair_stdev": 1.6, "pairs_with_a_degraded_run": 1, "per_pair_stdevs": [0.8, 0.0, 0.0, 0.0, 0.8, 0.0, 0.0, 0.49, 0.0, 0.0, 0.8, 0.8, 1.6, 0.0, 0.0, 0.0, 0.0, 0.8, 0.98, 0.0, 0.0, 0.4, 0.0, 0.4, 0.98, 0.0, 0.707, 0.8, 0.0, 0.0]}`
- `{"dimension": "education_domain_fit", "identical_across_k": "7/30", "self_consistency_rate": 0.233, "mean_within_pair_stdev": 0.643, "max_within_pair_stdev": 1.0, "pairs_with_a_degraded_run": 1, "per_pair_stdevs": [0.8, 0.0, 0.98, 1.0, 0.0, 0.0, 0.8, 0.98, 0.98, 0.0, 0.8, 0.49, 0.0, 0.8, 0.98, 0.8, 0.4, 0.0, 0.98, 0.8, 0.8, 0.98, 0.98, 0.8, 0.98, 0.98, 0.98, 0.4, 0.8, 0.0]}`
- `{"dimension": "hard_requirements", "identical_across_k": "20/30", "self_consistency_rate": 0.667, "mean_within_pair_stdev": 0.592, "max_within_pair_stdev": 2.449, "pairs_with_a_degraded_run": 1, "per_pair_stdevs": [2.245, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.96, 0.0, 0.0, 0.0, 1.47, 0.0, 0.0, 0.0, 1.2, 0.0, 0.0, 0.0, 2.0, 0.0, 2.0, 0.0, 2.0, 0.0, 0.0, 2.449, 0.0, 2.449, 0.0]}`

</details>

### ledger consistency

- **runs_scored**: `150`
- **pairs_scored**: `30`
- **contradictions_total**: `15`
- **pairs_with_any_contradiction**: `8/30`
- **contradictions_per_run**: `0.1`

- **stability (across-k)**: contradiction counts vary across the k repeats on 8/30 pairs; the headline is the total over all runs, not a single-run snapshot.
- **unstable pairs**: train:596 ([4, 0, 0, 1, 0]), train:3148 ([0, 0, 1, 1, 0]), train:3229 ([0, 0, 0, 0, 1]), train:3559 ([0, 3, 0, 0, 0]), train:3978 ([0, 0, 0, 1, 0]), train:4715 ([0, 0, 0, 1, 0]), train:5699 ([0, 0, 1, 0, 0]), train:5798 ([0, 0, 0, 0, 1])

*Consistency is not correctness: a run can be clean here by being consistently wrong (finding 008, train 596 after the consistency prompt). Pair with the agreement scorers; never merge them. COMPARABILITY: totals here are over ALL runs in the corpus, while finding 008's figures (8 contradictions / 7 pairs pre-calibration, 2 / 1 pair post) came from single 30-run batches — the two are only comparable as per-run rates (008 post-calibration: 2/30 = 0.067 per run), never as raw counts.*

<details><summary>rows (15 of 15)</summary>

- `{"pair": "train:596", "run_id": "r20260728T030245-2c495c", "requirement": "R4", "source_dimension": "skills_coverage", "source_value": "partial", "ledger_value": "absent"}`
- `{"pair": "train:596", "run_id": "r20260728T030245-2c495c", "requirement": "R8", "source_dimension": "skills_coverage", "source_value": "partial", "ledger_value": "absent"}`
- `{"pair": "train:596", "run_id": "r20260728T030245-2c495c", "requirement": "R9", "source_dimension": "skills_coverage", "source_value": "partial", "ledger_value": "absent"}`
- `{"pair": "train:596", "run_id": "r20260728T030245-2c495c", "requirement": "R15", "source_dimension": "skills_coverage", "source_value": "partial", "ledger_value": "absent"}`
- `{"pair": "train:596", "run_id": "r20260728T030345-bcecdb", "requirement": "R2", "source_dimension": "skills_coverage", "source_value": "covered", "ledger_value": "absent"}`
- `{"pair": "train:3148", "run_id": "r20260728T033526-c189e9", "requirement": "R2", "source_dimension": "skills_coverage", "source_value": "partial", "ledger_value": "absent"}`
- `{"pair": "train:3148", "run_id": "r20260728T033550-f64230", "requirement": "R1", "source_dimension": "skills_coverage", "source_value": "covered", "ledger_value": "partial"}`
- `{"pair": "train:3229", "run_id": "r20260728T032039-1b6f13", "requirement": "R1", "source_dimension": "skills_coverage", "source_value": "partial", "ledger_value": "absent"}`
- `{"pair": "train:3559", "run_id": "r20260728T032623-592821", "requirement": "R5", "source_dimension": "skills_coverage", "source_value": "partial", "ledger_value": "absent"}`
- `{"pair": "train:3559", "run_id": "r20260728T032623-592821", "requirement": "R11", "source_dimension": "skills_coverage", "source_value": "partial", "ledger_value": "absent"}`
- `{"pair": "train:3559", "run_id": "r20260728T032623-592821", "requirement": "R13", "source_dimension": "skills_coverage", "source_value": "partial", "ledger_value": "absent"}`
- `{"pair": "train:3978", "run_id": "r20260728T032519-df7a7c", "requirement": "R1", "source_dimension": "skills_coverage", "source_value": "absent", "ledger_value": "partial"}`
- `{"pair": "train:4715", "run_id": "r20260728T035411-473b32", "requirement": "R1", "source_dimension": "skills_coverage", "source_value": "absent", "ledger_value": "covered"}`
- `{"pair": "train:5699", "run_id": "r20260728T034542-28b36a", "requirement": "R1", "source_dimension": "skills_coverage", "source_value": "partial", "ledger_value": "absent"}`
- `{"pair": "train:5798", "run_id": "r20260728T034432-a5448a", "requirement": "R1", "source_dimension": "skills_coverage", "source_value": "covered", "ledger_value": "absent"}`

</details>

### tool-call correctness

- **runs_scored**: `150`
- **structurally_correct**: `150/150`
- **rate**: `1.0`

- **stability (across-k)**: computed per run over all repeats; no single-run snapshot is involved.

*Reuses the trajectory validator's invariants; measures rate, not legality.*

### evidence coverage (sentinel)

- **assessments_with_determinations**: `299`
- **over_threshold**: `12/299`
- **threshold**: `5.0x determinations per evidence span`
- **over_threshold_by_dimension**: 
  - **hard_requirements**: 10
  - **skills_coverage**: 2
- **assessments_with_zero_spans**: `0`

- **stability (across-k)**: computed per assessment over all repeats; a pair may be flagged in some runs and not others, which is itself informative — the flag list carries run_ids.

*SENTINEL, NOT A FAITHFULNESS METRIC: a flag means 'this assessment warrants human inspection', never 'this assessment is unfaithful'. A high ratio can be legitimate (one passage genuinely covering many must-items) and a normal ratio can still be unfaithful (right count, wrong category of evidence — finding 013). Report the flag count and where they cluster; never report the raw ratio as a score. Primary use: the sampling pool for faithfulness spot-checks (eval-design 3d).*

<details><summary>rows (12 of 12)</summary>

- `{"run_id": "r20260728T030759-c95b79", "pair": "train:2189", "dimension": "hard_requirements", "determinations": 12, "evidence_spans": 1, "ratio": 12.0}`
- `{"run_id": "r20260728T031243-b5e60c", "pair": "train:2980", "dimension": "skills_coverage", "determinations": 8, "evidence_spans": 1, "ratio": 8.0}`
- `{"run_id": "r20260728T031541-340ba7", "pair": "train:970", "dimension": "hard_requirements", "determinations": 7, "evidence_spans": 1, "ratio": 7.0}`
- `{"run_id": "r20260728T032246-9e8263", "pair": "train:3861", "dimension": "hard_requirements", "determinations": 14, "evidence_spans": 1, "ratio": 14.0}`
- `{"run_id": "r20260728T032339-3e188d", "pair": "train:3861", "dimension": "hard_requirements", "determinations": 17, "evidence_spans": 3, "ratio": 5.7}`
- `{"run_id": "r20260728T033407-cc705b", "pair": "train:3800", "dimension": "hard_requirements", "determinations": 10, "evidence_spans": 1, "ratio": 10.0}`
- `{"run_id": "r20260728T034340-3a1350", "pair": "train:5798", "dimension": "skills_coverage", "determinations": 13, "evidence_spans": 2, "ratio": 6.5}`
- `{"run_id": "r20260728T034340-3a1350", "pair": "train:5798", "dimension": "hard_requirements", "determinations": 13, "evidence_spans": 2, "ratio": 6.5}`
- `{"run_id": "r20260728T034848-134431", "pair": "train:5084", "dimension": "hard_requirements", "determinations": 10, "evidence_spans": 1, "ratio": 10.0}`
- `{"run_id": "r20260728T034912-3f0d5e", "pair": "train:5084", "dimension": "hard_requirements", "determinations": 10, "evidence_spans": 1, "ratio": 10.0}`
- `{"run_id": "r20260728T035128-ca8b5b", "pair": "train:5707", "dimension": "hard_requirements", "determinations": 20, "evidence_spans": 3, "ratio": 6.7}`
- `{"run_id": "r20260728T035540-b9f1a7", "pair": "train:6236", "dimension": "hard_requirements", "determinations": 12, "evidence_spans": 2, "ratio": 6.0}`

</details>

