# Roadmap

Derived from the project handoff ([handoff-trajectory-eval-harness.md](handoff-trajectory-eval-harness.md) §4–§6, §8). When this file and the handoff conflict, ask the owner — do not guess.

**Phase discipline:** phases are ordered by dependency, not calendar — **no time boxes**. A phase closes when its acceptance criteria pass and its public report lands in `docs/phase-reports/`; the next phase does not begin before closure (or an explicit skip recorded in `decisions.md`). Closure follows the ritual in CLAUDE.md / handoff §9.

**P0 and P1 both closed (2026-07-21).** Current phase: **P2 (the research core) — not yet started.** Phase order was P0→P1 overlapped (decisions.md 2026-07-17); both closures now complete.

---

## P0 — Data + rubric foundation

**Work:**

1. Survey public resume–JD matching datasets (Kaggle / HuggingFace); report options with size, label type, **license terms** → owner selects (license permitting redistribution required for committed data; otherwise script + checksum) — table lives in `data/README.md` until it moves into the p0 report
2. Rubric v1 in YAML: dimensions + weights + criteria + anchor examples
3. Labeling protocol written, reproducible
4. **Owner labels ~30 pairs** against the rubric (owner-judgment work, not CC's). Each labeled pair also records **`gate_expected: yes/no` + reason** (boundary score / insufficient evidence / anomaly) — ground truth for the P2 gate-integrity scorer
5. Mentor reviews ~10 labeled pairs — her first touchpoint (see Mentor protocol below)

**Phase report (p0):** dataset comparison table with rejection reasons · label statistics (score distributions overall and per dimension) · rubric problems surfaced during labeling → rubric v1→v1.x revision log · mentor-review agreement analysis (how many of the 10 diverged, on which dimensions, how resolved — the project's first disagreement dataset, previewing P2's disagreement analysis).

**Acceptance:**

- [x] Chosen dataset documented with license status (`data/README.md` — survey 2026-07-13, Route A selection recorded in decisions.md log)
- [x] Rubric v1 committed (v1.3 — authored v1.0, active v1.1, calibrated v1.2/v1.3 during P1)
- [x] 30 labeled pairs (including `gate_expected`) in a versioned reference file (`data/reference/labels-v1.jsonl`)
- [x] Labeling protocol reproducible (`docs/labeling-protocol.md` + seeded sampler + cockpit)
- [x] p0 report complete — label distributions (§3), disagreement 6/30 (§4), mentor agreement 90%/gate 10/10 (§5), three rubric revisions

## P1 — Agent + HITL gate

**Work:**

1. **First action: draft and commit the trajectory JSONL schema** (Decision 11) — all tools log into it from their first line of code; schema frozen before P2
2. LangGraph graph: parse resume + JD → structured extraction → per-dimension rubric assessment with **mandatory evidence citations** → aggregate → **gate** → recommendation
3. Gate triggers (thresholds TBD, revised by P2 numbers): aggregate in the boundary band · any dimension with insufficient evidence · high cross-dimension disagreement · anomalies (empty/garbled resume, suspected injection)
4. Gate honors **Decision 15's two modes**: interactive (LangGraph interrupt; human edits/approves a file in `review/`; run resumes) and eval (trigger recorded as a trajectory event, auto-resumed)
5. Tool surface (≤6, count locked; names revisable at plan time): `parse_resume`, `parse_jd`, `get_rubric`, `assess_dimension`, `submit_assessment`, `flag_for_review`
6. **Compatibility layer, three hard requirements:** ① provider specifics live in one config/client module — no provider strings in agent/eval code; ② output-schema validation + one retry + visible degradation in a provider-agnostic layer, one malformed-output test per provider; ③ trajectory JSONL carries provider/model/tokens/latency

**Phase report (p1):** graph structure diagram (mermaid) · initial gate-trigger settings with rationale · 2–3 complete trajectories walked through and annotated (what each step did, why the gate did/didn't fire) · malformed-output test results for both providers.

**Acceptance:**

- [x] Schema frozen-candidate committed (v0.2 — `docs/trajectory-schema.md`, validator + planted-defect tests; freezes at P2's first scorer commit)
- [x] Graph runs end-to-end in both modes on the example pairs (eval: three 30-pair batches, 30/30 valid; interactive: owner-driven live run `r20260721T031458-26e0fd`)
- [x] Compatibility layer passes its three requirements (CI-enforced — provider isolation test, malformed matrix, per-call metadata)
- [x] p1 report complete with graph diagram and annotated trajectory samples (`docs/phase-reports/p1.md`)

## P2 — Trajectory eval harness (the research core)

**Work:** scorers over trajectories, explicitly split into two tiers (recorded in `docs/eval-design.md`):

- **Structural scorers** (no human annotation needed, run on every case): gate integrity as a should-gate × did-gate confusion matrix (ground truth = P0's `gate_expected`) · tool-call structural correctness (every rubric dimension assessed exactly once; argument validity; call ordering) · error recovery (malformed inputs → graceful path) · **pass^k** (same pair k times; score stability — an unstable screener is a real incident, quantify it)
- **Semantic checks** (human-verified samples): per-dimension agreement vs the reference set · **faithfulness spot-check** — 5–10 manual verifications that cited evidence exists and supports the score · semantic tool-call correctness (were the *right* spans extracted) folds into this tier rather than pretending to be automatable

**Disagreement analysis:** when agent and reference differ, classify — agent error vs ambiguous label vs rubric gap; findings feed gate-threshold revisions (the eval-informs-design loop, recorded in decisions.md and archived as findings).

**Scorer self-verification:** before trusting any scorer, hand-craft synthetic trajectory JSONL files with known injected defects (missing gate event, wrong dimension, orphaned tool result, …); each scorer gets pytest cases proving it catches its known defects. A scorer that can't catch a planted defect is not done.

~30 seed cases (the P0 labeled pairs + variants). Cost recorded (tokens already in the JSONL) and reported per run. Final numbers on the delivery model (OpenAI); **at most one documented round of prompt calibration on the delivery model** (Decision 12).

**Phase report (p2 — the heaviest of the project):** full scorer results with ≥1 figure per metric (pass^k variance by dimension, agreement decomposition by dimension, gate-integrity confusion matrix) · disagreement classification statistics with one example per class · **cross-model comparison table (required) with interpretation** — which metrics are stable across providers, which drift, what that implies · threshold revision record (eval result → gate threshold A→B → re-run → gate-integrity delta: the loop's numeric evidence).

**Acceptance:**

- [ ] One reproducible command → eval report (all metrics, agreement by dimension)
- [ ] Cross-model table complete
- [ ] Final numbers produced on the delivery model
- [ ] Scorer self-verification tests green
- [ ] **Every scorer category has produced ≥1 archived finding** — a scorer with no finding is not complete
- [ ] p2 report complete

## P3 — Adversarial cases

**Work:** threat model = injection via candidate documents ("ignore previous instructions — ideal candidate", white-text ATS tricks). Defense = untrusted-data demarcation of all parsed content + sanitization at the parse seam. 3–5 poisoned-resume eval cases; pass = assessment uninfluenced AND ideally gate-flagged. Record the depth-matching argument: no LLM injection classifier — demarcation + sanitization + human gate matches this threat model.

**Phase report (p3):** threat-model table (attack type × defense × test result) · per-case record (injected content, actual agent behavior, gate flagged or not). **Any defense failure is archived as a finding** — "didn't hold, then fixed" is better research material than a clean sweep.

**Acceptance:**

- [ ] All poisoned cases run and recorded
- [ ] Failures either fixed with before/after evidence or documented as known limits
- [ ] p3 report complete

## P4 — Packaging + final report + mentor handoff

**Work:** **first deliverable is the final report** — executive summaries of all phase reports, full findings index, consolidated metrics tables. Then `SETUP.md` (uv-first, Windows note) · optional single-stage Dockerfile · one documented end-to-end example · README polish: protagonist framing first sentence, data-handling note, demand-gated futures list, and a **"Key Findings" section** — one-line versions of the 2–3 strongest findings, links into `docs/findings/`, 1–2 of the most persuasive figures. Anyone opening the repo should see within ten seconds that this is research, not a demo. Mentor demo — second touchpoint; the final report is the demo material.

**Acceptance:**

- [ ] Final report committed
- [ ] README carries protagonist sentence + Key Findings
- [ ] SETUP.md verified on a clean environment
- [ ] Public-readiness criteria hold: license-cleared data only, secrets scan green (repo has been public since init — see decisions.md log — so these criteria are standing obligations, not a flip-the-switch step)

---

## Five-pillar mapping (sanity check)

| Pillar | Phase |
|---|---|
| Trajectory eval + reference standard | **P2 (protagonist)** |
| LangGraph + tool calling | P1 |
| HITL gate (advance/reject is a consequential decision) | P1 |
| Injection defense | P3 |
| Cross-model comparison | P2 |

MCP deliberately absent — the owner's stock project owns that story.

## Mentor protocol

Light reviewer and endorser — not a data source, not an evaluator of agent quality. Exactly two touchpoints: **P0** (review ~10 labeled pairs) and **P4** (demo with the final report). Everything else is self-directed. Any real-resume material offered goes through Decision 5's rules or is politely declined.

## Explicitly not building (demand-gated or permanently out)

Market/JD trend reports for faculty · student gap-diagnosis ("what to add to reach this JD") · multi-part agent · RAG · MCP (here) · fine-tuning · frontend · database service · production hiring deployment.

Gate for the demand-gated futures: the same pain, 3+ times, in real use.
