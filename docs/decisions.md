# Decision Log

Locked decisions with rationale, derived from the project handoff ([handoff-trajectory-eval-harness.md](handoff-trajectory-eval-harness.md) §2). **Read D8/D9 before proposing RAGAS/DeepEval, RAG, MCP, or fine-tuning** — those are recorded "knowing what not to build" decisions. Later decisions and explicit phase-skips append to the log at the bottom.

## D1 — Python 3.12 + uv, typer CLI, filesystem-only storage

**Decision:** Python 3.12 + uv; typer CLI; JSON / JSONL / YAML on the filesystem; no database service; no frontend. Clarification: LangGraph's single-file SQLite checkpointer does not violate this (no server, no schema management); a custom JSON checkpointer is an acceptable alternative.
**Rationale:** Single user, small data; the product is a CLI plus a reproducible eval report.

## D2 — LangGraph for the agent

**Decision:** The host agent is built on LangGraph.
**Rationale:** Real HITL need — assessment pauses at the gate and resumes after human review; interrupts/checkpointing are the framework's actual value. Contrast on record: the owner's stock project hand-writes a linear loop; knowing when a framework earns its keep is the point.

## D3 — OpenAI-compatible client, provider by env config

**Decision:** Dev = DeepSeek (cost), delivery = OpenAI. The switch is configuration, not code. Compatibility-layer hard requirements land in P1.
**Rationale:** Provider specifics isolated in one config/client module keep agent/eval code provider-agnostic — which the P2 cross-model table then proves empirically.

## D4 — Ground truth is layered and honestly framed

**Decision:** Public resume–JD datasets as the base + owner rubric-labeled subset + mentor light review of a sample. Treated as a **noisy reference standard**, never "authoritative gold truth"; the framework includes disagreement analysis. Banned phrases: "train the eval agent", "gold-standard ground truth".
**Rationale:** Any single annotation source is noisy; quantifying and classifying disagreement is research depth, not a weakness.

## D5 — Data policy

**Decision:** Public resume–JD datasets are the primary data source; committable **only if the dataset license permits use and redistribution** — otherwise the repo carries a download script + checksum, never the data. Resumes of real NUS-ISS students/applicants or anyone personally known to the owner are **never committed and never transit an API without explicit consent** — optional local demo material only.
**Rationale:** Public web datasets keep the repo reproducible; license compliance is the legal floor for a public repo. Data from identifiable people around the owner carries a categorically different risk and stays out.

## D6 — Rubric is YAML

**Decision:** Dimensions (e.g. skills coverage, experience level, hard requirements, education/domain fit), weights, criteria, anchor examples — all in versioned YAML.
**Rationale:** Machine-readable, human-editable, and anchor examples fight score instability.

## D7 — Evidence citation is mandatory

**Decision:** Every dimension score cites the resume/JD span it rests on; uncited claims render as flagged.
**Rationale:** Feeds the faithfulness spot-check; kills "right score, fabricated reasoning".

## D8 — Eval = pytest + hand-written trajectory scorers; no RAGAS/DeepEval

**Decision:** No off-the-shelf eval frameworks.
**Rationale:** Trajectory-level metrics don't exist off-the-shelf; building them IS the differentiation.

## D9 — No RAG · no MCP here · no fine-tuning

**Decision:** No RAG (rubric + one resume + one JD fit in context; nothing to retrieve). No MCP in this project (story separation — MCP belongs to the stock project). No fine-tuning (sample size two orders of magnitude short; reliability/explainability is the goal and fine-tuning blackboxes it).
**Rationale:** "Knowing what not to build" entries — read before proposing any of these.

## D10 — Fairness/ethics posture (hiring domain)

**Decision:** This is an evaluation-research demo, NOT a production hiring tool. Mitigations by design: structured rubric only (no free-form vibes scoring), no protected-attribute inputs, mandatory evidence citation, human holds the final decision via the gate.
**Rationale:** Hiring AI draws fairness grilling; face it head-on with a prepared, honest answer.

## D11 — Trajectory JSONL is the eval's source of truth

**Decision:** Every LLM call logs provider, model, tokens, latency. The trajectory schema is defined at the very start of P1, **before any tool code is written**, and frozen before P2. All figures in phase reports must be regenerable from trajectory JSONL (generation scripts in `eval/reports/`).
**Rationale:** Offline replay beats parsing a vendor's trace format; schema-first prevents discarding early logs; regenerable figures are a research-reproducibility norm.

## D12 — Final numbers on the delivery model; calibration capped

**Decision:** Final eval numbers are produced on the delivery model (OpenAI); DeepSeek runs are dev iteration. The cross-model comparison table is a required P2 deliverable. **At most one documented round of prompt calibration is permitted on the delivery model.**
**Rationale:** Prompts/thresholds tuned on one model drift on another; the table is empirical proof the harness is provider-agnostic, and capping calibration keeps that proof honest.

## D13 — Research artifacts are public repo content

**Decision:** `docs/findings/` and `docs/phase-reports/` are tracked and committed. Each finding follows the five-part format: **Observation → Hypothesis → Verification → Change → Result** (with before/after numbers and run IDs). `interview-defense.md` holds interview phrasing only (gitignored) and carries no research-record duty.
**Rationale:** The research process must be visible to anyone opening the repo — advisors, interviewers, the owner's future self — not locked in private notes.

## D14 — Secrets hygiene

**Decision:** API keys live in `.env` (gitignored) with a committed `.env.example`; keys never appear in code or logs; CI includes a secrets scan (gitleaks).
**Rationale:** The owner has personally experienced the key-leak failure mode; a public repo gets scanning from day one.

## D15 — HITL gate runs in two modes

**Decision:** *Interactive mode* — gate interrupts and waits for human review (demos and real use). *Eval mode* — gate triggers are recorded as trajectory events but auto-resumed under a default policy (batch evaluation always runs in eval mode). Gate-integrity scoring reads the recorded events; recording and blocking are independent concerns.
**Rationale:** pass^k and 30-case batch runs are impossible if every gate trigger suspends execution; eval mode preserves the research signal (did it gate?) without the operational block.

---

## Log

- **2026-08-03** — **P3 closes with the p3 report PR.** Three rounds in a fixed order (baseline -> instruction-class -> mechanism-class), the prose sentence deliberately REMOVED in round 3 so the mechanism's effect stays attributable. Result recorded as partial, not as success: structural demarcation closed the role-forgery path (skills and experience stopped moving, mean 3.8 -> 1.8) while the content-contamination path stayed open on `education_domain_fit`, the one dimension with no determination ledger. The standing conclusion is the layered one — **structural demarcation closes role forgery, item-by-item ledger reconciliation closes content contamination, and a dimension with neither is open to both** — and it is what makes `education_domain_fit`'s five independent indictments one defect rather than five. One construction failure (`cf-ai-04-v1`) recorded rather than counted: the original carrier obfuscation destroyed its own payload, so its L3 was never evidence of a defense.
- **2026-08-02** — **P2 closes with the p2 report PR.** Acceptance walk in the report §8; findings 011-015 archived; interview-defense updated per the closure ritual. **One criterion is recorded as met-in-substance, unmet-in-form rather than ticked:** `tool-call correctness` is the one scorer with no numbered finding — its result (fault batch 5/5 across two independent batches, the standing error-recovery coverage caveat resolved) lives in the p2 report §5, because the research surface was deliberately closed to finish the deliverable. Two known defects are frozen rather than fixed (issue #26, findings 012/015): the extractor emits requirement categories the rubric excludes, and its ledger size is unstable. Both are single-variable calibrations whose value is research-side, and the extractor feeds every hard-requirement verdict, so changing it would invalidate every baseline recorded since P0.
- **2026-08-02** — **Direction correction (owner ruling), recorded because it changed what got built.** Fifteen findings against an unwritten report and an undefined entry point was judged the wrong ratio for a three-week project whose target is an engineering role: the harness is the product, findings are its output. Standing consequence from here: stop expanding the research surface, invest the remainder in the deliverable. Concretely — the variant stage produced no new finding beyond those already open, the cross-model stage produced one report section rather than three findings, and the extractor fixes were frozen. What the correction bought, immediately: building the one-command report runner surfaced two real defects that no amount of further analysis would have (all 11 variant trajectories were schema-invalid while the console output looked correct; the pass^k scorer shipped without the stability note its own contract mandates).
- **2026-07-10** — Repository created **public** at the owner's explicit instruction, overriding the handoff preamble's "start private until P0 closes" default. Data handling was designed for public visibility from the start; the initial commit contains no data, no secrets (scan in CI), and no license-restricted material.
- **2026-07-13** — **Workflow (owner instruction): no direct commits to `main`; all work lands via checkpoint-scoped PRs.** Granularity settled the same day: one PR per deliverable (≈ one roadmap acceptance item), branch-named `p<n>/<deliverable>` — phase-wide PRs were judged too wide to review, per-commit PRs too noisy. A phase closes when its final PR (the phase report) merges. The two survey/selection commits initially made directly to `main` were rewound and recommitted through the first checkpoint PR so the rule holds from the first commit after init.
- **2026-07-28** — **Evidence-coverage sentinel adopted (owner ruling, P2).** `determinations / evidence_spans > 5x` flags an assessment for human inspection. Threshold rationale: corpus medians are 1.2 (skills) / 2.0 (hard), so 3x still sits in the normal tail (32/149 hard assessments) and would drown the signal; 5x targets the 10:1-14:1 structural mismatches (finding 013). **Semantics are binding: this is a SENTINEL, not a faithfulness metric** — a flag means 'warrants human inspection', never 'is unfaithful'; the raw ratio is never reported as a score, only the flag count and its clustering. Known miss: it does not catch every human-verified failure (013's train 5798 sits at 3.0, below threshold), which is precisely why it is a sampling aid rather than a detector. Primary use: the draw pool for faithfulness spot-check strata.
- **2026-07-21** — **P0 closes (mentor touchpoint complete).** Mentor blind-labeled the 10 pairs (v1.3): 90% exact dimension agreement, 10/10 gate agreement, all divergence on the adjacency axis (finding 010); p0 report §5 filled; disagreements recorded not adjudicated (imperfect-rubric stance, D4). P0 + P1 both closed → P2 may begin.
- **2026-07-21** — **P1 closes with the p1 report PR** (acceptance walk in the report §8; findings 007–009 archived; interview-defense updated per the closure ritual). P0 remains open, gated only on the mentor touchpoint; P2 begins after BOTH closures.
- **2026-07-17** — **P1 opened before P0 closure (owner decision, recorded overlap — not a skip).** P0's sole remaining dependency is the mentor touchpoint; every other acceptance item is merged. P1 runs owner-led under the design-workshop workflow (docs/p1-design.md: options → owner ratifies → recorded with rationale); P0 closes with full ritual the moment the mentor data lands.
- **2026-07-16** — **Rubric maintenance delegated to CC; imperfect-rubric stance adopted (owner decision).** The owner's goals are the eval framework and the agent, not rubric science. Standing division of labor from here: CC authors and maintains the rubric (v1.1+), findings, and all documentation without per-item owner ratification — the owner ratifies in bulk via PR merge; the owner's irreducible work is the 30 reference labels (cockpit runs — human judgment is what makes the reference set a human reference). Recorded stance: the rubric does not need to be perfect and should not chase perfection — different HR = different rubrics; what the reference standard must be is *written and self-consistent*, so that between-rater and rubric-induced variance are measured quantities in P2 rather than silent noise. First act under the delegation: rubric v1.1 derived-musts rule (skills requirements derived from duties when a JD states no skill musts) — closes the session-1 gap (train 596) by CC's call, option (a) of the finding draft.
- **2026-07-13** — **P0 dataset selected (owner decision): `cnamuangtoun/resume-job-description-fit`, script + checksum route.** Rationale: the most realistic text among all candidates — evidence citation (D7) and P3 injection need real material to work on, and the survey showed every fully-redistributable pair dataset is synthetic (survey + selection record: `data/README.md`). Accepted risks recorded there: no declared license (research use is a gray zone; nothing redistributed — raw text is gitignored and hygiene-tested), possible upstream removal (pinned revision + sha256 checksums). The 30-pair reference file stores indices/labels/spans, never text.
