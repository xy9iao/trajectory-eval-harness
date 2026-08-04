"""Secrets hygiene (Decision 14) and the gitignore contract must hold from the first commit."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Local-only paths that must never be committed (CLAUDE.md, non-negotiable;
# data/raw/ holds unlicensed dataset text — Decision 5)
REQUIRED_IGNORES = [
    "review/",
    "interview-defense.md",
    ".env",
    "data/raw/",
    "runs/",
    "teaching-protocol.md",
]

# Shapes of real credentials; placeholders in .env.example must not match any of them
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
]


def test_gitignore_covers_local_only_files() -> None:
    entries = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for required in REQUIRED_IGNORES:
        assert required in entries, f"{required!r} missing from .gitignore"


def test_env_example_committed_without_real_secrets() -> None:
    env_example = ROOT / ".env.example"
    assert env_example.exists(), ".env.example must be committed (Decision 14)"
    content = env_example.read_text(encoding="utf-8")
    for pattern in SECRET_PATTERNS:
        assert not pattern.search(content), f"credential-shaped value matches {pattern.pattern}"


def test_text_io_declares_encoding() -> None:
    """Text-mode file I/O must pass an explicit encoding: the omission slipped into two
    scripts in one week, and Windows default codepages make it a real failure (P4 promises
    a Windows note). Ruff's PLW1514 cannot see chained-Path receivers, so this guard greps.
    Same-line heuristic: binary modes exempt; multi-line call args are not inspected."""
    offenders = []
    for path in ROOT.rglob("*.py"):
        if ".venv" in path.parts:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for lineno, line in enumerate(lines, 1):
            for match in re.finditer(r"\b(open|read_text|write_text)\(([^)]*)", line):
                args = match.group(2)
                if "encoding=" in args or re.search(r"[\"'][rwax+]*b", args):
                    continue
                offenders.append(f"{path.relative_to(ROOT)}:{lineno}: {line.strip()}")
    assert not offenders, "text-mode I/O without encoding=:\n" + "\n".join(offenders)


def test_repo_content_is_english() -> None:
    """All repo content is English (CLAUDE.md language rule) — mechanized
    after CJK slipped into two committed docs (2026-07-21). Conversation
    may be bilingual; tracked files may not."""
    import subprocess

    cjk = re.compile("[\\u4e00-\\u9fff\\u3040-\\u30ff]")
    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, cwd=ROOT, check=True
    ).stdout.split()
    offenders = []
    for name in tracked:
        path = ROOT / name
        if path.suffix not in {".py", ".md", ".yaml", ".yml", ".toml", ".json", ".jsonl"}:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if cjk.search(line):
                offenders.append(f"{name}:{lineno}")
    assert not offenders, "non-English content in tracked files:\n" + "\n".join(offenders)


def test_no_ai_authorship_attribution() -> None:
    """Sole-author project (CLAUDE.md): no AI-attribution in tracked files —
    no co-author trailers, no 'Generated with <AI>' lines, no robot badges.
    Commit-message trailers are not in files and stay instruction-level;
    this guards the file-committed forms for ANY agent. The governance files
    that QUOTE the rule are excluded so the rule text isn't self-flagged."""
    import subprocess

    governance = {
        "CLAUDE.md",
        "AGENTS.md",
        "docs/collaboration-protocol.md",
        "docs/handoff-trajectory-eval-harness.md",
        "tests/test_repo_hygiene.py",
    }
    ai = r"(?:claude|codex|copilot|chatgpt|gpt-[0-9]|anthropic|openai)"
    patterns = [
        re.compile(r"co-authored-by:\s*.+<[^>]+@", re.IGNORECASE),  # an actual trailer
        re.compile(rf"generated with .*{ai}", re.IGNORECASE),
        re.compile(rf"co-?authored .*{ai}", re.IGNORECASE),
        re.compile(r"🤖"),
    ]
    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, cwd=ROOT, check=True
    ).stdout.split()
    offenders = []
    for name in tracked:
        if name in governance or (ROOT / name).suffix not in {
            ".py",
            ".md",
            ".yaml",
            ".yml",
            ".toml",
            ".json",
            ".jsonl",
            ".txt",
            ".cfg",
            ".ini",
        }:
            continue
        for lineno, line in enumerate((ROOT / name).read_text(encoding="utf-8").splitlines(), 1):
            if any(p.search(line) for p in patterns):
                offenders.append(f"{name}:{lineno}: {line.strip()[:80]}")
    assert not offenders, "AI-authorship attribution in tracked files:\n" + "\n".join(offenders)


# --- the data boundary, extended beyond trajectories (2026-08-04) ---------
#
# finding 007 established the invariant "committed artifacts carry ids and
# offsets, never document text" and wired it into the TRAJECTORY validator.
# The invariant was never applied to the other committed artifacts, so the
# reference labels, the variant specs and several findings accumulated verbatim
# corpus fragments for three weeks while the hygiene suite reported green.
#
# The lesson is about coverage, not about that particular hole: a check that
# passes only proves the checks you wrote ran clean. These two tests split
# deliberately —
#   * the STRUCTURAL one runs everywhere, including CI without the dataset;
#   * the VERBATIM one is the real check and needs the gitignored corpus, so it
#     skips in CI. That skip is a known limit, stated here rather than left for
#     someone to discover the way this hole was discovered.

TEXT_BEARING_ARTIFACTS = [
    "data/reference/labels-v1.jsonl",
    "data/variants/variants-v1.json",
    "data/adversarial/poisoned-v1.json",
]


def _corpus_rows() -> dict[int, str]:
    import json
    import sys

    sys.path.insert(0, str(ROOT / "data"))
    from corpus import DOC_COLUMNS, load_row

    rows = {}
    for line in (
        (ROOT / "data" / "reference" / "labels-v1.jsonl").read_text(encoding="utf-8").splitlines()
    ):
        row = json.loads(line)["pair"]["row"]
        raw = load_row("train", row)
        rows[row] = raw[DOC_COLUMNS["resume"]] + "\n" + raw[DOC_COLUMNS["jd"]]
    return rows


@pytest.mark.xfail(
    reason="known: reference labels quote the source corpus; accepted, see data/README.md",
    strict=True,
)
def test_reference_labels_carry_no_free_text_requirements() -> None:
    """STRUCTURAL half — runs without the dataset, so CI enforces it.

    A determination's `requirement` must be an id or an offset pair, never a
    requirement string lifted from the JD. Length is the proxy: ids are short.
    """
    import json

    path = ROOT / "data" / "reference" / "labels-v1.jsonl"
    offenders = []
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        for dim, body in record.get("dimensions", {}).items():
            for det in body.get("determinations") or []:
                req = det.get("requirement")
                if isinstance(req, str) and len(req) > 40:
                    offenders.append(f"{record['pair']['row']}/{dim}: {req[:50]}...")
    assert not offenders, (
        "reference labels carry free-text requirement strings (finding 007's boundary):\n"
        + "\n".join(offenders[:10])
    )


@pytest.mark.xfail(
    reason="known: reference labels quote the source corpus; accepted, see data/README.md",
    strict=True,
)
@pytest.mark.skipif(
    not (ROOT / "data" / "raw" / "train.csv").exists(),
    reason="raw corpus not present (gitignored) — the verbatim check cannot run here",
)
def test_committed_artifacts_carry_no_verbatim_corpus_text() -> None:
    """VERBATIM half — the real check. Needs the gitignored corpus.

    Any run of 40+ characters shared with a source document is redistribution
    of a dataset whose license is undeclared (all-rights-reserved by default),
    and it falsifies this repo's own claim about what it stores.
    """
    corpus = "\n".join(_corpus_rows().values())
    offenders = []
    for rel in TEXT_BEARING_ARTIFACTS + sorted(
        str(p.relative_to(ROOT)) for p in (ROOT / "docs" / "findings").glob("*.md")
    ):
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for i in range(0, max(1, len(text) - 40)):
            if text[i : i + 40] in corpus:
                offenders.append(f"{rel}: {text[i : i + 40]!r}")
                break
    assert not offenders, "verbatim corpus text in committed artifacts:\n" + "\n".join(offenders)
