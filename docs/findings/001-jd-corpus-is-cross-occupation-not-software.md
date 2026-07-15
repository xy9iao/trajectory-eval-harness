# 001 — The JD corpus is cross-occupation, not software-centric; "domain fit" cannot mean a technical sub-field

**Status:** open — Change recorded (rubric v1 `education_domain_fit`, 2026-07-14); Result pending labeling observation. Owner writes the interpretive judgment; this file records the evidence.

**Date:** 2026-07-14 · **Phase:** P0 (rubric v1)

**Reproduction:** `python data/profile_jd_domains.py` — deterministic over `train.csv` at pinned dataset revision `08978e21714984bb417547d2c0f9b477f5298163` (checksum-verified by `data/download_dataset.py`). No trajectory JSONL exists yet (this is pre-agent corpus profiling); the script is the regenerable source for every number below.

## Observation

While defining the `education/domain fit` dimension for rubric v1, the working assumption was that the host dataset is a software-role matching corpus, so "domain fit" would mean a technical sub-field (backend vs frontend vs data). Profiling the 280 unique JDs in `train.csv` contradicts this: the single largest occupational bucket is **accounting/finance (108/280)**, larger than **software engineering (65/280)**. The corpus spans accounting, hardware/electrical engineering (23), business/PM (36), sales/marketing (37), and HR/admin (26) — it is cross-occupation, not software-centric.

## Hypothesis

Two hypotheses about where the "domain" signal lives:

1. **Occupational/functional field** (accountant vs software engineer vs electrical engineer) is a near-universal signal — nearly every JD names an occupation.
2. **Industry/sector** (finance vs education vs healthcare) is present but not universal, and is often orthogonal to whether a candidate can do the job (an accountant is an accountant across industries).

The prior assumption — "domain = technical sub-field within software" — is expected to be false, because software roles are a minority of the corpus.

## Verification

Ran `data/profile_jd_domains.py` over the 280 unique JDs (6,241 train rows collapse to 280 unique JDs — the survey's reuse figure, independently confirmed here).

- **Occupational field:** accounting/finance 108, software eng 65, sales/marketing 37, business/PM 36, data/ML 33, HR/admin 26, hardware eng 23, healthcare 1. Software-family roles (software + data + devops = 115) are under half the corpus; software sub-fields alone (65) cover <1/4. The prior assumption is falsified.
- **Industry/sector:** 208/280 JDs mention ≥1 industry word (72 mention none). Top sectors: financial 94, finance 66, education 63, insurance 49, medical 45, federal 31, bank/banking 30, manufacturing 22, healthcare 21. Industry signal is strong but not universal.

**Measurement caveat (recorded honestly):** keyword matching is coarse, and cross-axis terms confound the two counts — `financial` matches both the finance *occupation* ("financial analyst") and the finance *industry* ("financial services"), so the occupational "accounting/finance 108" and the industry "financial 94" overlap. Counts are directional signposts, not exact partitions; precise separation would require manual coding of a JD sample.

## Change

*Decision recorded 2026-07-14 (owner; transcribed from rubric v1 `education_domain_fit` scope_notes and design_notes — CC transcription, owner to confirm wording).* The evidence-supported options were:

- **(a)** Define `domain` primarily as **occupational/functional field match** — covers 280/280, most universal signal; a clear cross-occupation mismatch (e.g. accountant → software role) is exactly what the gate should flag. → **Adopted:** the dimension is occupation-relative (degree level + field judged against the JD's occupation).
- **(b)** Treat **industry/sector** as a secondary signal or a separate dimension — present in 208/280 but absent in 72, and frequently orthogonal to competence. → **Excluded from rubric v1 (option A)**; recorded as a P2 future experiment (industry as secondary signal).
- **(c)** Defining `domain` as a software sub-field (backend/frontend/data) — applies to <1/4 of the corpus. → **Rejected by the evidence.**

## Result

*Pending.* This was a pre-rubric baseline observation; the `education_domain_fit` dimension is now defined per the Change. The Result closes during P0 labeling: how many of the ~30 labeled pairs turn on occupational vs industry mismatch, and whether the occupation-relative definition survives labeling or needs a v1→v1.x revision.
