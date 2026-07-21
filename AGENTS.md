# AGENTS.md — trajectory-eval-harness

**Single source of standing rules: [CLAUDE.md](CLAUDE.md).** Everything in it applies to ANY
coding agent working in this repo — Codex included — with "Claude" read as "the agent you
are". Do not duplicate rules here; if this file and CLAUDE.md ever diverge, CLAUDE.md wins
and this file must be restored to a pointer.

Non-negotiables restated once (they bind every AI tool, not one vendor):

- **Sole-author project.** No `Co-Authored-By` trailers of any agent, no "Generated with …"
  lines in commits/PRs/issues, no AI-attribution badges anywhere. Owner's git identity only.
- **Data rules** (CLAUDE.md §Data & secrets): unlicensed dataset text never committed and
  never placed in logs, trajectories, or commits; data-boundary holes are fixed on
  discovery, never queued.
- **Workflow:** no direct commits to `main`; one deliverable per PR; the owner reviews and
  merges every PR.
