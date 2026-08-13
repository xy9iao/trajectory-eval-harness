# Setup

This project requires Python 3.12 and [uv](https://docs.astral.sh/uv/). It uses local files for
storage; no database service or build step is required.

## Install and verify

The following path needs neither an API key nor the gitignored dataset:

```bash
git clone https://github.com/xy9iao/trajectory-eval-harness.git
cd trajectory-eval-harness
uv sync
uv run pytest -q
uv run python -m agent.run --synthetic
uv run python -m eval.report --manifest examples/sample-batch/manifest.json
```

The synthetic run exercises the complete graph, writes a trajectory, and validates it. The sample
report scores a committed 3-pair, 15-trajectory slice of the P2 dev-model batch. On a fresh clone,
dataset-dependent tests skip by design; the suite should have no unexpected failures. The `xfail`
checks document retained source-text fragments and are explained in
[data/README.md](data/README.md) — one of the two also needs the dataset, so a fresh clone reports a
single `xfailed` rather than two.

If `uv sync` reports a Python version mismatch, run:

```bash
uv python install 3.12
uv sync
```

## Download the dataset

Live runs over the reference pairs require the pinned source dataset:

```bash
uv run python data/download_dataset.py
```

The script downloads `train.csv` and `test.csv` from a fixed Hugging Face revision into
`data/raw/` and verifies both files with SHA-256 checksums. A checksum mismatch stops the setup;
do not run experiments against a different file under the same name.

`data/raw/` is gitignored because the source dataset declares no license. The repository contains
the pinned download script and checksums, but does not redistribute the corpus. See
[data/README.md](data/README.md) for the dataset decision and its limitations.

### Raw CSV contract

The corpus loader expects UTF-8 CSV files with this schema:

| Column | Required | Meaning |
|---|---:|---|
| `resume_text` | yes | Raw resume text passed to the agent |
| `job_description_text` | yes | Raw job-description text passed to the agent |
| `label` | no for agent loading; present in the pinned dataset | Original dataset fit label |

Files must be named `train.csv` and `test.csv` and placed under `data/raw/`. References use the
split name plus the zero-based CSV row position, for example `train:596`. Do not reorder or rewrite
the pinned files: stored row references and character offsets are meaningful only against the
checksum-verified bytes.

The current loader implements this pinned schema; arbitrary resume or job-description formats are
not accepted automatically.

## Configure a live model

Copy the environment template and add only the key or keys you use:

```bash
cp .env.example .env
```

```dotenv
DEEPSEEK_API_KEY=your-deepseek-key
OPENAI_API_KEY=your-openai-key
# LLM_PROVIDER=deepseek     # deepseek (default) | openai
# LLM_MODEL=                # optional provider-model override
```

Keys are provider-specific, so both may remain in `.env` while `LLM_PROVIDER` selects one.
`.env` is gitignored, and CI scans every push for secrets. Keys are never written to trajectories.

## Run the agent and evaluation

Download the dataset and configure the selected provider before using `--live`:

```bash
uv run python -m agent.run --pair train:596 --live      # one pair
uv run python -m agent.run --passk 5 --smoke --live     # 2 pairs x 5 runs
uv run python -m agent.run --passk 5 --live             # 30 pairs x 5 runs
```

Run the smoke batch before the full batch. Provider behavior, cost, and wall-clock time may change,
so verify the pipeline on 10 runs before paying for 150.

Each run writes `runs/<run-id>/trajectory.jsonl`. A pass^k batch also prints and writes a manifest
such as `runs/passk-<run-id>.json`. Score that exact batch with:

```bash
uv run python -m eval.report --manifest runs/passk-<run-id>.json
```

`runs/` is gitignored because trajectories, manifests, and checkpoints are local experimental
state. Reports are regenerated from the manifest's explicit run IDs and do not mix in other local
runs.

The committed sample metrics are reproducible from `examples/sample-batch/`. Full historical runs
remain local because `runs/` is gitignored, so a fresh clone cannot regenerate every published
number from its original trajectories. A new live rerun follows the same method but may not produce
identical scores because model APIs and sampling are not deterministic.

## Troubleshooting

| Symptom | Resolution |
|---|---|
| Python version mismatch during `uv sync` | Run `uv python install 3.12`, then `uv sync`. |
| `data/raw/train.csv not found` | Run `uv run python data/download_dataset.py`. |
| Dataset checksum mismatch | Remove the mismatched local file and rerun the pinned downloader; do not bypass verification. |
| Missing provider API key | Add the selected provider's key to `.env`; confirm `LLM_PROVIDER`. |
| Live provider rejects the configured model | Remove an unnecessary `LLM_MODEL` override or set a model supported by that provider. |
| Report scores zero cases | Confirm the manifest points to live, schema-valid trajectories rather than stub runs. |

## Windows

Use PowerShell or WSL. In PowerShell, replace the POSIX copy command with:

```powershell
Copy-Item .env.example .env
```

All project text I/O declares UTF-8 explicitly, so it does not depend on the platform default
codepage.

## Repository layout

| Path | Purpose |
|---|---|
| `eval/` | Scorers, trajectory validation, and report runner |
| `agent/` | LangGraph host agent, HITL gate, tools, and sanitization |
| `rubrics/` | Versioned YAML rubric |
| `data/` | Reference labels, constructed-case specifications, and dataset loader |
| `docs/` | Final report, phase reports, findings, and design records |
| `runs/` | Local trajectories and batch manifests (gitignored) |

For the research results and design narrative, start with
[docs/final-report.md](docs/final-report.md).
