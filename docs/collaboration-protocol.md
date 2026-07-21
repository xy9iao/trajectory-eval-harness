# Collaboration protocol — working agreement

How work is paced and divided between the owner and a coding agent on this project. This is
the *behavioral* layer; the *standing rules* (authorship, data, git workflow, stack, phase
discipline) live in [CLAUDE.md](../CLAUDE.md) and locked decisions in
[decisions.md](decisions.md) — read those first. This document is **read on demand**, when the
owner points an agent here; it is deliberately not auto-loaded, so it never silently changes an
agent's default behavior.

"The agent" below means whichever agent is working (Claude Code, Codex, …). "The owner" is
Xinyang.

## 1. Delegation model

- **The owner's irreducible work is the reference labels.** The ~30-pair reference set is human
  judgment by definition — a legitimate reference standard for an evaluation harness cannot be
  machine-produced, or the whole eval measures a model against itself. The owner labels; the
  agent never fills in a score.
- **Everything around the labels is delegated to the agent**, without per-item sign-off: the
  agent authors and maintains the rubric, findings, phase reports, protocol docs, tooling, and
  the agent code. The owner **ratifies in bulk by merging the PR** — that merge is the sign-off,
  not a stream of individual approvals.
- **Findings get drafted, not blocked on.** When something is finding-shaped (a surprising
  metric, a root cause in rubric/prompt/threshold design, the same problem twice), the agent
  drafts it directly and mentions it in one line; it never interrupts the owner's flow to ask
  permission to record.
- **Imperfect-rubric stance.** The rubric does not need to be perfect and should not chase
  perfection — different reviewers use different rubrics. What the reference standard must be is
  *written and self-consistent*, so that between-rater and rubric-induced variance become
  measured quantities, not silent noise. Disagreements are **classified, not resolved** (routed
  to the right chapter, not eliminated).

## 2. Pacing — two modes, the owner declares which

**STEP mode (default for core / research work — anything the owner wants to learn or own):**
- The agent does exactly one agreed step, then stops and reports.
- No PR, branch, commit, or file the owner did not approve. Plans are proposals: written first,
  executed only after an explicit "go".
- One deliverable per "go"; finishing early never means starting the next step.
- At each step the owner chooses who writes the code: owner / owner-with-hints / agent-scaffolds
  + owner-writes-the-judgment-parts / agent-writes + owner-line-reviews.
- Teaching happens at the point of contact, using this project's real data — hints before
  solutions; the owner runs code and sees real output before writing logic.

**SPRINT mode (explicit only — for grunt/cleanup work):**
- Batch execution: the agent decides, records, and reports in bulk.
- Applies only when the owner says "sprint" for a named scope, and expires when that scope
  completes.

Rubric/docs/findings maintenance follows SPRINT rules regardless of the declared mode (it is the
delegated work of §1). When in doubt, default to STEP and ask.

## 3. Research discipline (the reason the agent is an advisor, not just hands)

- **Baseline before change.** Before any metric-affecting change (rubric, prompt, threshold,
  scorer): is the pre-change baseline recorded? No baseline → no before/after → no finding.
- **Evidence-then-fix, with a stop-loss.** Don't whack-a-mole. Batch the runs, classify the
  failures, make one attributable change per round, re-run for the before/after. And the mirror
  clause: when the evidence shows a change won't move its target (two rounds flat), **stop** —
  reclassify as an honest measured limitation rather than spending more effort.
- **One attributable change per metric per calibration round.** Two changes on the same metric
  (or the same rubric dimension) in one round destroy the before/after attribution. Changes on
  independent metrics may share a round.
- **Mechanism over instruction.** Where something must hold, enforce it structurally (schema,
  validator, CI test), not by asking the model or the reader nicely. Empirically on this
  project: mechanisms held; prose redefinitions of judgment semantics did not (finding 009).
- **Every numeric claim cites its regenerable source** — a script in `eval/reports/`, a run ID
  whose trajectory reproduces it, or a CI test. Untraceable numbers do not enter documents.
- **Phase closure ritual.** A phase closes only when its acceptance criteria pass, its public
  report lands in `docs/phase-reports/`, findings are archived, and the interview-prep file is
  updated. The next phase does not begin before closure (or an explicit recorded skip).

## 4. Language

The owner works in a mix of Chinese and English; match the owner's language in conversation.
**All repo content — code, comments, docs, commits, PRs — is English** (CI-enforced).
