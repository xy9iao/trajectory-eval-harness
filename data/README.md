# data/

Primary data source: public resume–JD matching datasets (Decision 5).

Rules:

- A dataset is committed here **only if its license permits use and redistribution**. Where the license is unclear or restrictive, this directory carries a download script + checksum instead of the data.
- Resumes of real NUS-ISS students/applicants or anyone personally known to the owner are **never committed and never sent to an API without explicit consent**.

## P0 dataset survey — 2026-07-13

Method: HuggingFace API (license from dataset metadata; split sizes from `datasets-server`) + Kaggle dataset pages read in-browser (license as declared on page, read 2026-07-13). Every cell below is traceable to the linked source page.

### Pair datasets (resume + JD + match label)

| Dataset | Source | Size | Label type | License | Redistributable? | Verdict / notes |
|---|---|---|---|---|---|---|
| [cnamuangtoun/resume-job-description-fit](https://huggingface.co/datasets/cnamuangtoun/resume-job-description-fit) | HF | 8,000 pairs (6,241 train / 1,759 test); only **280 unique JDs** in train | 3-class fit label (`No Fit` confirmed in rows; documented classes No/Potential/Good Fit — re-verify on download) | **None declared** → all-rights-reserved default | **No** | Best text realism: multi-section real-style resumes, real-company JDs. Most adopted (1,039 downloads / 79 likes). Usable only via download-script + checksum route; even *use* is a legal gray zone — record honestly if selected |
| [AzharAli05/Resume-Screening-Dataset](https://huggingface.co/datasets/AzharAli05/Resume-Screening-Dataset) | HF | 10,174 rows | Binary `Decision` (select/reject) + free-text `Reason_for_decision` | **MIT** | **Yes** | Labels map directly onto advance/do-not-advance + rationale. Text appears synthetic/templated — weakens evidence-citation depth and P3 injection realism |
| [jainishkumar/resume-job-description-matching-dataset](https://www.kaggle.com/datasets/jainishkumar/resume-job-description-matching-dataset) | Kaggle | 500 pairs, 10 domains | Continuous `match_score` (0.05–0.98, well spread) **and** 3-class `match_label` | **CC0** | **Yes** | Purpose-built synthetic (creator chose synthetic explicitly for redistributability). Structured multi-section resumes/JDs. Dual label types suit agreement analysis (kappa on classes, correlation on scores). New & unproven (53 downloads); labels are programmatic (domain/skill overlap), not human judgment |
| [netsol/resume-score-details](https://huggingface.co/datasets/netsol/resume-score-details) | HF | 1,031 samples | Rich macro/micro criterion scores + justifications | "cc" — **variant unspecified** | Unclear | Fully GPT-4o synthetic *including the scores* → LLM-labeled reference would be circular for evaluating an LLM agent. Schema is worth reading as rubric-design inspiration regardless |
| [surendra365/recruitement-dataset](https://www.kaggle.com/datasets/surendra365/recruitement-dataset) | Kaggle | ~10k rows | Binary `Best Match` (≈5,150 / 4,850) | **ODbL + DbCL** | Yes (attribution + share-alike) | **Rejected:** carries protected-attribute input columns (Age, Gender, Race, Ethnicity) — conflicts with Decision 10; resumes are one-line templates ("Proficient in X, Y, Z…") — nothing for evidence citation to cite |
| [batuhanmtl/job_resume_fit](https://huggingface.co/datasets/batuhanmtl/job_resume_fit) | HF | 2,385 rows, 23 categories | Continuous machine-made scores (`ai_match_score`, string/fuzzy match) | **"other"** — unspecified | **No** | Rejected: license unusable without clarification; labels are machine-generated similarity scores, not judgments |

### Component corpora (build pairs ourselves; no pre-existing pair labels)

| Dataset | Source | Size | Content | License | Redistributable? | Notes |
|---|---|---|---|---|---|---|
| [snehaanbhawal/resume-dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset) | Kaggle | 2,400+ resumes, 24 categories | Real resumes (livecareer.com), string + HTML + PDF | **CC0** (uploader-declared) | Yes, with caveat | The standard resume corpus (usability 10.0, 74k downloads). Caveat: CC0 is declared by the scraper, not livecareer — provenance not airtight; texts are real people's public resume samples |
| [ravindrasinghrana/job-description-dataset](https://www.kaggle.com/datasets/ravindrasinghrana/job-description-dataset) | Kaggle | 480 MB CSV (row count TBC) | Synthetic job postings (Faker + ChatGPT-assisted), 23 fields incl. JD/skills/responsibilities | **CC0** | Yes | Huge quantity, templated realism; usable as a JD pool if pairing ourselves |
| [jacob-hugging-face/job-descriptions](https://huggingface.co/datasets/jacob-hugging-face/job-descriptions) | HF | <1k JDs | Job descriptions | **Llama 2 license** (atypical for data) | Conditional | Rejected as JD pool: license is a model license applied to data — terms unclear |

### Seen, not shortlisted

- `shamimhasan8/resume-vs-job-description-matching-dataset`, `shreya2k3/resume-job-description-matching` (Kaggle) — **404 / removed**; stale search results
- `med2425/resume-job-fit-merged-v1`, `votanthanh32004/resume-job-fit-cleaned`, and ~8 other HF re-uploads of `cnamuangtoun` — derivatives; inherit the missing license
- `pranavvenugo/resume-and-job-description` (Kaggle) — page exposes no documentation; no match labels apparent from listing
- `opensporks/resumes` (HF, CC0) — resumes-only; superseded by snehaanbhawal for the component route (richer formats/categories)

### The structural tension (owner should weigh this)

Every fully-redistributable pair dataset found is **synthetic**; the one with genuinely realistic text is **unlicensed**. This is structural, not bad luck: real resumes carry privacy/copyright weight, so uploaders who share them can't or don't license them. Selection is therefore a realism-vs-license-cleanliness tradeoff:

- **Option A — cnamuangtoun via script + checksum (realism-first).** Commit a download script pinned to a HF revision hash + checksum; the 30-pair reference file stores **IDs, labels, and span offsets — never the raw text**. Residual risk: unlicensed use is gray; dataset could vanish (mitigated by pinned revision + checksum). Labeling protocol must sample across the 280 unique JDs.
- **Option B — AzharAli05 (MIT, committable).** Clean license, 10k rows, decision+reason labels; pay in text realism.
- **Option C — jainishkumar (CC0, committable).** Cleanest license, dual label types; only 500 pairs (enough — the reference set is ~30); newest and least proven.
- **Option D — component route: snehaanbhawal resumes (CC0) × a JD pool.** Maximum control: engineer the 30 pairs to exercise every rubric dimension and the gate boundary; real resume text; fully committable subset. Cost: no pre-existing pair labels, so the "public dataset base layer" of the layered ground truth (Decision 4) is thinner.

**Owner selection: PENDING** — rejected rows keep their reasons; this table moves into the p0 phase report.
