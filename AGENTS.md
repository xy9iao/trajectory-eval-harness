# AGENTS.md — trajectory-eval-harness

**Before you touch anything in this repo, open and read [CLAUDE.md](CLAUDE.md) and
[docs/decisions.md](docs/decisions.md) in full, and follow them.** They are the single source
of standing rules and locked decisions. This applies to ANY coding agent — Codex included —
with "Claude" read as "the agent you are". This file is a pointer, not a copy; if it ever
diverges from CLAUDE.md, CLAUDE.md wins and this file must be restored to a pointer.

Non-negotiables, restated here as a safety net in case you did not chase the pointer (they
bind every AI tool, not one vendor):

- **Sole-author project.** No `Co-Authored-By` trailers of any agent, no "Generated with …"
  lines in commits/PRs/issues, no AI-attribution badges or footers anywhere. Commit
  author/committer is the owner's git identity only. (A CI test scans tracked files for
  attribution; commit-message trailers are on you to omit.)
- **Data rules** (CLAUDE.md §Data & secrets): unlicensed dataset text is never committed and
  never placed in logs, trajectories, or commits; data-boundary holes are fixed on discovery,
  never queued. CI enforces this (`tests/test_repo_hygiene.py`).
- **Workflow:** no direct commits to `main`; one deliverable per PR; the owner reviews and
  merges every PR. All repo content is English (CI-enforced); conversation may be bilingual.

**Behavioral / working agreement** (how work is paced and divided — pacing, delegation,
research discipline) lives in [docs/collaboration-protocol.md](docs/collaboration-protocol.md).
It is **not** auto-applied; read it when the owner points you there.
