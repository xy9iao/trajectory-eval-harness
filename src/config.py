"""Model + path configuration.

A single provider-agnostic factory (`make_model`) is the seam the rest of the code uses, so the
provider can be swapped from one place (GUIDE §2: "Cloud API, provider-agnostic"). Defaults to
OpenAI per project setup; point OPENAI_BASE_URL at a gateway to route elsewhere.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # read .env once at import

# --- paths ---
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
EVAL_SET = DATA_DIR / "eval_set.jsonl"

# --- model config ---
DEFAULT_MODEL = os.getenv("MODEL", "gpt-4o-mini")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4o")


def make_model(model: str | None = None, temperature: float = 0.0, **kwargs):
    """Return a chat model. Provider-agnostic seam — swap providers here only.

    Reads OPENAI_API_KEY (and optional OPENAI_BASE_URL) from the environment. temperature=0 by
    default for stability where we want it; raise it for the pass@k / pass^k sampling study (§6.3).
    """
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=model or DEFAULT_MODEL, temperature=temperature, **kwargs)
