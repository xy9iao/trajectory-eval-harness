# Setup

Python 3.12 and [uv](https://docs.astral.sh/uv/). No database, no service, no build step.

```bash
git clone https://github.com/xy9iao/trajectory-eval-harness
cd trajectory-eval-harness
uv sync
uv run pytest -q          # no API calls, no key needed
```

Verified from a fresh clone: **118 passed, 6 skipped.** The six skips are the dataset-dependent
tests, and they skip by design — see *The dataset is not in the repo* below.

If `uv sync` reports a Python version mismatch, `uv python install 3.12` and re-run — uv manages
the interpreter itself, so no system Python needs changing.

## Running without an API key

The test suite and the agent's stub path need no key. The stub path exercises the whole graph,
writes a real trajectory and validates it:

```bash
uv run python -m agent.run --synthetic
```

**What you cannot do unkeyed, stated plainly:** produce an eval report. `runs/` is gitignored, so a
fresh clone contains **no trajectories at all**, and the scorers deliberately skip stub-provider
runs — a report over stubbed assessments would be a table of numbers describing nothing. Point
`eval.report` at a batch and it will tell you so rather than print a plausible-looking empty table:

```
- cases scored: 0
**No valid cases in this batch — nothing was scored.**
```

So the honest order is: **key → smoke → batch → report.** The scorers are still readable and
independently testable without any of that, which is what the 118 unkeyed tests cover.

## Running with a live model

Keys are **per provider**, so both can sit in `.env` at once and switching provider is one
variable rather than a key swap:

```bash
cp .env.example .env        # then fill in the keys you have
```

```bash
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-...
# LLM_PROVIDER=deepseek     # deepseek (default) | openai
# LLM_MODEL=                # optional; each provider has a default
```

`.env` is gitignored and CI runs a secrets scan on every push. Keys never appear in code, logs or
trajectories.

```bash
uv run python -m agent.run --pair train:596 --live      # one pair
uv run python -m agent.run --passk 5 --smoke --live     # 2 pairs x 5, the cost/compat check
uv run python -m agent.run --passk 5 --live             # the full 30-pair batch
```

**Run the smoke first.** It is two pairs and a few cents, and it has caught a provider
incompatibility, a scorer scoping bug, and a wall-clock estimate that was wrong by 4x — each of
which would have cost a full batch to discover.

## The dataset is not in the repo

`data/raw/` is gitignored: the source dataset declares no license, so nothing is redistributed.
The repo carries a download script and checksums instead — see [data/README.md](data/README.md).
Without it, dataset-dependent tests skip automatically and the eval side still runs against
committed trajectories.

The 30-pair human reference set (`data/reference/labels-v1.jsonl`) **is** committed: it stores
row indices, scores and character offsets, never document text.

## Windows

Everything is stdlib path handling and uv, so no shell-specific steps — but two notes:

- Use PowerShell or WSL; the commands above assume a POSIX-ish shell for `cp`.
- Trajectories are written UTF-8 explicitly and a repo-hygiene test fails on any text I/O that
  omits an encoding, so the default-codepage problem cannot reappear silently.

## Layout

| Path | |
|---|---|
| `eval/` | the harness — scorers, corpus loading, trajectory validator, report runner |
| `agent/` | the host agent — LangGraph graph, HITL gate, tools, sanitization |
| `rubrics/` | versioned YAML rubric |
| `data/` | reference labels, constructed-case specs, dataset loader |
| `docs/` | final report, phase reports, findings, design records |
| `runs/` | trajectories and batch manifests (gitignored) |

Start at [docs/final-report.md](docs/final-report.md).
