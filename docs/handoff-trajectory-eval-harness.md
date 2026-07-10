# Handoff: Initialize `trajectory-eval-harness` — Resume–JD Matching Evaluation Agent (NUS-ISS Capstone)

> **Instruction for Claude Code:** Initialize this repository per the spec below, then organize `docs/roadmap.md`, `docs/decisions.md`, and the gitignored `interview-defense.md` from it. Today is scaffolding + P0 kickoff only — no agent code. Where this doc says TBD, leave the placeholder. Repo may become **public** (data handling designed for it), but start private until P0 closes.
>
> **You are also the research advisor for this project.** The owner has no prior research training and no human supervisor for day-to-day work. Follow §9 (Research Mentorship Protocol) strictly — especially finding-sniffing and phase closure rituals. Process discipline is your responsibility, not the owner's.

---

## 1. Mission & Framing

**The evaluation framework is the protagonist; the agent is its host.** README's first sentence, verbatim:

> *An evaluation framework for AI-agent reliability — trajectory-level scoring of intermediate agent behavior — demonstrated on a resume–JD matching agent with a human-in-the-loop gate.*

Host task (single, locked): given one resume + one job description, assess match quality per a structured rubric and output {per-dimension scores with cited evidence, aggregate score, advance / do-not-advance recommendation}. Serves the real NUS-ISS context (screening applicants; helping students judge fit) — but the research contribution is the eval layer, and the topic-selection rule is recorded: the host task has **no famous commercial product as a reference frame**, so attention lands on the framework, not on a comparison we'd lose.

**Focus discipline:** one host task, depth goes into evaluation dimensions, never into task count. Market/JD trend reports, student gap-diagnosis, and any multi-part expansion are demand-gated futures (§8).

**Research posture:** this project is run as a research project, not a demo build. The framework's value is proven by **findings** — documented instances of "evaluation surfaced a problem → design was revised → metrics improved." A harness with no findings is an engineering artifact; a harness with findings is research. Every phase produces a public phase report; every non-trivial discovery is archived as a finding (§4, §9, Decision 13).

## 2. Locked Decisions (each becomes a decisions.md entry with rationale)

| # | Decision | Rationale |
|---|---|---|
| 1 | Python 3.12 + uv, typer CLI, filesystem-only storage (JSON / JSONL / YAML), no database service, no frontend | Single user, small data; the product is a CLI + a reproducible eval report. **Clarification:** LangGraph's single-file SQLite checkpointer does not violate this decision (no server, no schema management); a custom JSON checkpointer is an acceptable alternative |
| 2 | **LangGraph** for the agent | Real HITL need: assessment pauses at the gate and resumes after human review — interrupts/checkpointing are the framework's actual value (contrast recorded: the owner's other project hand-writes a linear loop; knowing when a framework earns its keep is the point) |
| 3 | **OpenAI-compatible client, provider by env config** — dev = DeepSeek (cost), delivery = OpenAI | Switch is configuration, not code. Compatibility-layer hard requirements in P1 |
| 4 | **Ground truth = layered, honestly framed:** public resume–JD datasets as the base + owner rubric-labeled subset + mentor light review of a sample. Treated as a **noisy reference standard**, never "authoritative gold truth"; the framework includes disagreement analysis | Any single annotation source is noisy; quantifying and classifying disagreement is research depth, not a weakness. Banned phrases recorded: "train the eval agent", "gold-standard ground truth" |
| 5 | **Data policy:** public resume–JD datasets are the primary data source and may be committed to the repo **only if the dataset license permits use and redistribution**; where the license is unclear, the repo carries a download script + checksum instead of the data. **Resumes of real NUS-ISS students/applicants or anyone personally known to the owner are never committed and never transit an API without explicit consent** — optional local demo material only | Public web datasets are usable and keep the repo reproducible; license compliance is the legal floor for a public repo. Data from identifiable people around the owner carries a categorically different risk and stays out |
| 6 | Rubric = YAML (dimensions e.g. skills coverage, experience level, hard requirements, education/domain fit; weights; criteria; anchor examples) | Machine-readable, human-editable, and anchor examples fight score instability |
| 7 | **Evidence citation is mandatory:** every dimension score cites the resume/JD span it rests on; uncited claims render as flagged | Feeds the faithfulness spot-check; kills "right score, fabricated reasoning" |
| 8 | Eval = pytest + hand-written trajectory scorers; **no RAGAS/DeepEval** | Trajectory-level metrics don't exist off-the-shelf; building them IS the differentiation |
| 9 | **No RAG** (rubric + one resume + one JD fit in context; nothing to retrieve) · **no MCP here** (story separation — MCP belongs to the stock project) · **no fine-tuning** (sample size two orders of magnitude short; reliability/explainability is the goal and fine-tuning blackboxes it — prepared answer lives in interview-defense) | "Knowing what not to build" entries; read before proposing any of these |
| 10 | **Fairness/ethics posture (hiring domain):** this is an evaluation-research demo, NOT a production hiring tool. Mitigations by design: structured rubric only (no free-form vibes scoring), no protected-attribute inputs, mandatory evidence citation, human holds final decision via the gate. Recorded so the inevitable bias question has a prepared, honest answer | Hiring AI draws fairness grilling; face it head-on |
| 11 | Trajectory JSONL is the eval's source of truth; every LLM call logs provider, model, tokens, latency. **The trajectory schema is defined at the very start of P1, before any tool code is written**, and frozen before P2. **All figures in phase reports must be regenerable from trajectory JSONL** (generation scripts live in `eval/reports/`) | Offline replay beats parsing a vendor's trace format; tools log into the schema from day one, so schema-first prevents discarding early logs; regenerable figures are a research-reproducibility norm |
| 12 | Final eval numbers are produced on the **delivery model (OpenAI)**; DeepSeek runs are dev iteration; the **cross-model comparison table is a required P2 deliverable**. **At most one documented round of prompt calibration is permitted on the delivery model**; further tuning would contaminate the provider-agnostic claim | Prompts/thresholds tuned on one model drift on another; the table is empirical proof the harness is provider-agnostic; capping calibration keeps that proof honest |
| 13 | **Research artifacts are public repo content:** `docs/findings/` and `docs/phase-reports/` are tracked and committed. Each finding follows the five-part format: **Observation → Hypothesis → Verification → Change → Result (with before/after numbers and run IDs)**. `interview-defense.md` holds interview phrasing only and carries no research-record duty | The research process must be visible to anyone opening the repo — advisors, interviewers, the owner's future self — not locked in private notes |
| 14 | **Secrets hygiene:** API keys live in `.env` (gitignored) with a committed `.env.example`; keys never appear in code or logs; CI includes a secrets scan (e.g. gitleaks) | The owner has personally experienced the key-leak failure mode; a repo headed for public visibility gets scanning from day one |
| 15 | **HITL gate runs in two modes:** *interactive mode* (gate interrupts and waits for human review — demos and real use) and *eval mode* (gate triggers are **recorded as trajectory events but auto-resumed** under a default policy — batch evaluation). Gate-integrity scoring reads the recorded events; recording and blocking are independent concerns | pass^k and 30-case batch runs are impossible if every gate trigger suspends execution; eval mode preserves the research signal (did it gate?) without the operational block |

## 3. Repository Structure

```
trajectory-eval-harness/
├── agent/                 # host: LangGraph graph, gate logic, tools
├── eval/                  # protagonist: scorers, cases, runners, reports
│   └── reports/           # figure/report generation scripts (regenerable from JSONL)
├── rubrics/               # YAML rubrics (versioned: v1, v1.1, ...)
├── data/                  # license-cleared datasets OR download scripts + checksums
├── review/                # HITL queue — gitignored
├── examples/              # 2–3 walkthrough pairs for the README/demo
├── docs/
│   ├── roadmap.md
│   ├── decisions.md
│   ├── eval-design.md
│   ├── findings/          # ★ research findings, one file each, five-part format
│   │   └── 000-example.md #   synthetic example seeded at init as the format anchor
│   └── phase-reports/     # ★ per-phase closing reports (p0 ... p4)
├── SETUP.md               # mentor-facing quickstart
├── CLAUDE.md              # provided verbatim alongside this handoff
├── .env.example           # committed; .env is gitignored
├── teaching-protocol.md   # gitignored (ported from existing project)
└── interview-defense.md   # gitignored — spec in §7
```

## 4. Phases

Phases are ordered by dependency, not by calendar. **There are no time boxes: a phase closes when its acceptance criteria pass, and the next phase does not begin before closure** (or an explicit, recorded skip — see §9). Each phase ends with a public phase report in `docs/phase-reports/`.

**P0 — Data + rubric foundation.**
CC surveys public resume–JD matching datasets (Kaggle / HuggingFace; report options with size, label type, **license terms**) → owner selects (license permitting redistribution required for committed data; otherwise script+checksum) → rubric v1 in YAML (dimensions + weights + criteria + anchor examples) → labeling protocol written → **owner labels ~30 pairs against the rubric** (owner-judgment work, not CC's). **Each labeled pair also records `gate_expected: yes/no` + reason** (boundary score / insufficient evidence / anomaly) — this field is the ground truth for the P2 gate-integrity scorer. → mentor reviews ~10 of them (her first touchpoint; **during this review the owner mentions the plan to develop this into a presentable research project and the hope to list her as advisor** — setting expectation early, no commitment requested).
*Phase report (p0):* dataset comparison table with rejection reasons; **label statistics** (score distributions overall and per dimension); rubric problems surfaced during labeling → rubric v1→v1.x revision log; **mentor-review agreement analysis** (how many of the 10 diverged, on which dimensions, how resolved — this is the project's first disagreement dataset and a preview of P2's disagreement analysis).
*Acceptance:* chosen dataset documented with license status; rubric v1 committed; 30 labeled pairs (including `gate_expected`) in a versioned reference file; labeling protocol reproducible; **p0 report complete with label-distribution figures and ≥1 recorded rubric revision.**

**P1 — Agent + HITL gate.**
**First action: draft and commit the trajectory JSONL schema** (Decision 11) — all tools log into it from their first line of code. Then LangGraph graph: parse resume + JD → structured extraction → per-dimension rubric assessment with **mandatory evidence citations** → aggregate → **gate** → recommendation. Gate triggers (thresholds TBD, revised by P2 numbers): aggregate in the boundary band; any dimension with insufficient evidence; high cross-dimension disagreement; anomalies (empty/garbled resume, suspected injection). Gate implementation honors **Decision 15's two modes**: interactive (LangGraph interrupt; human edits/approves a file in `review/`; run resumes) and eval (trigger recorded, auto-resume). Tool surface (≤6, locked): `parse_resume`, `parse_jd`, `get_rubric`, `assess_dimension`, `submit_assessment`, `flag_for_review` — revise names freely at plan time, not count. **Compatibility layer, three hard requirements:** ① provider specifics live in one config/client module (no provider strings in agent/eval code); ② output-schema validation + one retry + visible degradation in a provider-agnostic layer, one malformed-output test per provider; ③ trajectory JSONL carries provider/model/tokens/latency.
*Phase report (p1):* graph structure diagram (mermaid); initial gate-trigger settings with rationale; **2–3 complete trajectories walked through and annotated** (what each step did, why the gate did/didn't fire); malformed-output test results for both providers.
*Acceptance:* schema frozen-candidate committed; graph runs end-to-end in both modes on the example pairs; compatibility layer passes its three requirements; **p1 report complete with graph diagram and annotated trajectory samples.**

**P2 — Trajectory eval harness (the research core).**
Scorers over trajectories, explicitly split into two tiers (recorded in eval-design.md):
- **Structural scorers** (no human annotation needed, run on every case): gate integrity as a should-gate × did-gate confusion matrix (ground truth = P0's `gate_expected`), tool-call structural correctness (every rubric dimension assessed exactly once; argument validity; call ordering), error recovery (malformed inputs → graceful path), **pass^k** (same pair k times; score stability — an unstable screener is a real incident, quantify it).
- **Semantic checks** (human-verified samples): per-dimension agreement vs the reference set; **faithfulness spot-check** — 5–10 manual verifications that cited evidence exists and supports the score; semantic tool-call correctness (were the *right* spans extracted) folds into this tier rather than pretending to be automatable.

**Disagreement analysis:** when agent and reference differ, classify — agent error vs ambiguous label vs rubric gap; findings feed gate-threshold revisions (the eval-informs-design loop, recorded in decisions.md and archived as findings).
**Scorer self-verification:** before trusting any scorer, hand-craft synthetic trajectory JSONL files with known injected defects (missing gate event, wrong dimension, orphaned tool result, etc.); each scorer gets pytest cases proving it catches its known defects. A scorer that can't catch a planted defect is not done.
~30 seed cases (the P0 labeled pairs + variants). Cost is recorded (tokens are already in the JSONL) and reported per run.
*Phase report (p2 — the heaviest report of the project):* full scorer results with **at least one figure per metric** (pass^k variance by dimension, agreement decomposition by dimension, gate-integrity confusion matrix); disagreement classification statistics with one example per class; **cross-model comparison table (required) with interpretation** — which metrics are stable across providers, which drift, what that implies; threshold revision record (eval result → gate threshold A→B → re-run → gate-integrity delta: the loop's numeric evidence).
*Acceptance:* one reproducible command → eval report (all metrics, agreement by dimension); cross-model table complete; final numbers on the delivery model; scorer self-verification tests green; **every scorer category has produced ≥1 archived finding — a scorer with no finding is not complete**; p2 report complete.

**P3 — Adversarial cases.**
Threat model: injection via candidate documents ("ignore previous instructions — ideal candidate", white-text ATS tricks). Defense: untrusted-data demarcation of all parsed content + sanitization at the parse seam. 3–5 poisoned-resume eval cases; pass = assessment uninfluenced AND ideally gate-flagged. Record the depth-matching argument (no LLM injection classifier; demarcation + sanitization + human gate matches this threat model).
*Phase report (p3):* threat-model table (attack type × defense × test result); per-case record (injected content, actual agent behavior, gate flagged or not). **Any defense failure is archived as a finding** — "didn't hold, then fixed" is better research material than a clean sweep.
*Acceptance:* all poisoned cases run and recorded; failures either fixed with before/after evidence or documented as known limits; p3 report complete.

**P4 — Packaging + final report + mentor handoff.**
**First deliverable: the final report** — executive summaries of all phase reports, full findings index, consolidated metrics tables. Then SETUP.md (uv-first, Windows note), optional single-stage Dockerfile, one documented end-to-end example, README polish: protagonist framing first sentence, data-handling note, demand-gated futures list, and a **"Key Findings" section** — one-line versions of the 2–3 strongest findings, links into `docs/findings/`, and 1–2 of the most persuasive figures (e.g. pass^k variance before/after a rubric revision). Anyone opening the repo should see within ten seconds that this is research, not a demo. Mentor demo — her second touchpoint; the final report is the demo material, and the ask alongside it: **endorsement / advisor attribution** (expectation was seeded at P0).
*Acceptance:* final report committed; README carries protagonist sentence + Key Findings; SETUP.md verified on a clean environment; repo ready to flip public (license-cleared data, secrets scan green).

## 5. Five-Pillar Mapping (sanity check, keep in roadmap)

trajectory eval + reference standard → P2 (protagonist) · LangGraph + tool calling → P1 · HITL gate → P1 (advance/reject is a consequential decision) · injection defense → P3 · cross-model comparison → P2. MCP deliberately absent (stock project owns it).

## 6. Mentor Protocol

She is a **light reviewer and endorser, not a data source or evaluator of agent quality**. Exactly two touchpoints: P0 (review 10 labeled pairs; owner seeds the advisor-attribution expectation in the same conversation) and P4 (demo with the final report + endorsement/attribution ask). Everything else self-directed. Any real-resume material she offers goes through Decision 5's rules or is politely declined.

## 7. `interview-defense.md` (gitignored — career material never in tracked files)

Four sections, maintained continuously. Note Decision 13: research records live in `docs/findings/` and `docs/phase-reports/`; this file holds **interview phrasing distilled from them**, not the records themselves.

1. **Resume bullet inventory** — status-marked (✅ live / 🔒 blocked by phase); bullets unlock only with real numbers; a bullet ships together with its defense block, same session. Bullet style rule: lead with what the evaluation *surfaced and changed*, not just what was built (e.g. "…framework that surfaced N failure modes — score instability from ambiguous rubric criteria, gate misses on boundary cases — driving rubric and threshold revisions that improved X from A to B").
2. **Problems & fixes log (the practical-experience record — highest-value section).** Every non-trivial tuning problem gets an entry **the day it happens**, format: date · problem · what was tried · method chosen and why · outcome · one-sentence interview soundbite. Each entry cross-references its finding file when one exists. CC prompts the owner to log after every core milestone.
3. **Question bank** (merge-gate questions draw from here; seed it with:) why is your reference standard trustworthy · pass^k: why that k, what did variance reveal · how is this different from an ATS product ("it's an eval framework; the matcher is the host") · why LangGraph here but a hand-written loop in your other project · why no RAG / no fine-tuning (prepared answers) · how were gate thresholds chosen (the eval-informs-gate loop) · bias/fairness in hiring AI (Decision 10's posture) · what breaks at 10k resumes · is n=30 enough ("a reference set for regression and agreement, not a benchmark — say it first") · how do you know your scorers themselves are correct (synthetic-defect trajectories).
4. **Defense blocks** per bullet: L1 what/how · L2 why/tradeoffs · L3 limits/counterfactuals · known weaknesses to own when probed.

## 8. Explicitly Not Building (demand-gated or permanently out)

Market/JD trend reports for faculty · student gap-diagnosis ("what to add to reach this JD") · multi-part agent · RAG · MCP (here) · fine-tuning · frontend · database service · production hiring deployment. Gate for futures: same pain 3+ times in real use.

## 9. Research Mentorship Protocol — CC as Research Advisor

Background: the owner has no prior research training and no supervisor for day-to-day work. Research-process discipline is therefore **CC's active responsibility** — executed proactively, never dependent on the owner remembering rules they were never taught. CC's role = research advisor + process gatekeeper, not just the coding hands.

### 9.1 Things CC must do unprompted

**Finding-sniffing (the most important duty).** Whenever any of these signals appears, CC pauses and asks *"is this a finding? Should we archive it?"*:
- A metric is surprising (too high / too low / high variance)
- A bug's root cause traces to rubric / prompt / threshold **design** (not a code typo)
- The same problem appears a second time
- The owner says "interesting", "weird", or "why would it do that"

The owner does not yet know what deserves recording — judging "this is finding-worthy" is CC's job. Err toward asking and being declined, never toward silence.

**Phase closure ritual.** Before any phase's acceptance check, CC initiates closure:
1. Walk the acceptance criteria item by item; list gaps
2. Draft the phase-report skeleton (figures/numbers as placeholders, marked for the owner to run/confirm)
3. Verify this phase's findings are archived (from P2 on: a scorer with no finding = incomplete)
4. Prompt the owner to update the matching interview-defense.md entries

Until closure completes, CC does not start next-phase work — even on direct instruction. CC responds: *"P{n} still has X open — close it first, or skip explicitly?"* An explicit skip is recorded in decisions.md.

**Baseline-before-change.** Before any change that affects metrics (rubric, prompt, threshold, scorer logic), CC asks: *"is the pre-change baseline recorded?"* No baseline → no before/after → no finding. Flow: record baseline → change → re-run the same seed set → record result → archive as finding if meaningful.

**Evidence check on numeric claims.** Any numeric statement written into a report, README, or finding ("variance dropped", "agreement reached X") must be traceable: which run's trajectory JSONL reproduces it? Cite the run ID. Untraceable numbers do not enter documents.

### 9.2 Teaching style (continues the existing teach-mode principles)

- On first encounter with a research concept (inter-annotator agreement, confusion matrix, variance decomposition, …), CC explains it **using this project's real data**, never abstract definitions — one-time explanation cost, project-long payoff
- The *why* behind research method is always taught: why a fixed seed set, why single-variable changes, why n=30 is framed as a reference set rather than a benchmark — the owner must be able to say these unaided in an interview
- The hint-not-solution rule extends to documents: findings and phase reports get their **core judgments written by the owner** (what was observed, what the owner believes caused it); CC drafts skeletons and data sections, checks evidence, and challenges logic — but "what was discovered and what it means" comes from the owner, because interviews test the owner's understanding, not CC's prose

### 9.3 Cadence checks

- At the end of each working session, CC summarizes in 2–3 sentences: what moved today, what remains before the current phase's acceptance, anything discovered but not yet archived
- If 3 consecutive sessions produce no finding and no report progress (pure coding), CC asks: *"engineering-only stretch — is this a normal build phase (e.g. P1 scaffolding) or are we missing records?"*

## Today's Definition of Done

Repo created (private for now) · structure + gitignore (`review/`, `interview-defense.md`, `teaching-protocol.md`, `.env`) verified in the initial commit · `.env.example` committed · decisions.md (15 entries) · roadmap.md (P0–P4 with acceptance criteria, five-pillar map, not-building list) · CLAUDE.md placed verbatim (including the research-advisor role line) · `docs/findings/000-example.md` seeded with a synthetic five-part example as the format anchor · `docs/phase-reports/` scaffolded · interview-defense.md scaffolded with the four sections + seeded question bank · CI (ruff + pytest + typecheck + secrets scan) green on the skeleton · README first pass with the protagonist sentence · P0 dataset survey kicked off. **Nothing else.**
