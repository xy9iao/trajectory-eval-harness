"""Secrets hygiene (Decision 14) and the gitignore contract must hold from the first commit."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Local-only paths that must never be committed (CLAUDE.md, non-negotiable;
# data/raw/ holds unlicensed dataset text — Decision 5)
REQUIRED_IGNORES = [
    "review/",
    "interview-defense.md",
    ".env",
    "data/raw/",
]

# Shapes of real credentials; placeholders in .env.example must not match any of them
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
]


def test_gitignore_covers_local_only_files() -> None:
    entries = (ROOT / ".gitignore").read_text().splitlines()
    for required in REQUIRED_IGNORES:
        assert required in entries, f"{required!r} missing from .gitignore"


def test_env_example_committed_without_real_secrets() -> None:
    env_example = ROOT / ".env.example"
    assert env_example.exists(), ".env.example must be committed (Decision 14)"
    content = env_example.read_text()
    for pattern in SECRET_PATTERNS:
        assert not pattern.search(content), f"credential-shaped value matches {pattern.pattern}"
