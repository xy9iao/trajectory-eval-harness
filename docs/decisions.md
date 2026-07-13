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

- **2026-07-10** — Repository created **public** at the owner's explicit instruction, overriding the handoff preamble's "start private until P0 closes" default. Data handling was designed for public visibility from the start; the initial commit contains no data, no secrets (scan in CI), and no license-restricted material.
- **2026-07-13** — **P0 dataset selected (owner decision): `cnamuangtoun/resume-job-description-fit`, script + checksum route.** Rationale: the most realistic text among all candidates — evidence citation (D7) and P3 injection need real material to work on, and the survey showed every fully-redistributable pair dataset is synthetic (survey + selection record: `data/README.md`). Accepted risks recorded there: no declared license (research use is a gray zone; nothing redistributed — raw text is gitignored and hygiene-tested), possible upstream removal (pinned revision + sha256 checksums). The 30-pair reference file stores indices/labels/spans, never text.
