"""Variant materialization (eval-design 3b/3c).

A variant is a **unit test with a known answer**: a controlled perturbation
of one real pair, plus the gate behavior expected after the change. Specs
live in `data/variants/variants-v1.json`.

Data discipline: a spec stores the BASE PAIR REFERENCE plus the text WE
author (an inserted resume segment, a truncation length). It never stores
dataset text — the perturbed document is materialized at run time from the
gitignored corpus, exactly as reference labels store offsets rather than
quotes.

Two batches, deliberately separate (3b): gate negatives exercise the
decision path (finding 004's TN=0), fault samples exercise the
retry -> degrade -> escalate path. One does not cover the other.

Reporting rule (3c gate 4): variant results NEVER merge with live-corpus
results. Constructed negatives and real positives go in separate tables or
carry a source column — enforced here by tagging every variant run's
trajectory with `variant_id`, so the corpus loader can always separate them.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))

SPECS = ROOT / "data" / "variants" / "variants-v1.json"


@dataclass(frozen=True)
class Variant:
    id: str
    batch: str  # "gate_negative" | "fault"
    base_pair: dict[str, Any]
    perturbation: dict[str, Any]
    changed: str
    expected_gate: bool
    expected_reasons: list[str]
    rationale: str
    # Set when a dry run resolved a divergence to "agent-rubric divergence"
    # (3c gate 5, state 2): the construction is sound and the departure is the
    # agent's, so the variant stays live and names the finding that owns it.
    # A construction error would be removed to `construction_failures` instead.
    known_divergence: str | None = None

    @property
    def pair_key(self) -> tuple[str, int]:
        return (self.base_pair["split"], self.base_pair["row"])


def load_variants(path: Path = SPECS) -> list[Variant]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [Variant(**v) for v in payload["variants"]]


def materialize(variant: Variant) -> tuple[str, str]:
    """Apply the perturbation to the base pair; returns (resume, jd).

    Perturbation types are CLOSED (3c gate 2) — a new type needs a new
    ruling, which is what stops the set growing extra categories mid-build.
    """
    from corpus import DOC_COLUMNS, load_row

    row = load_row(*variant.pair_key)
    resume = row[DOC_COLUMNS["resume"]]
    jd = row[DOC_COLUMNS["jd"]]
    p = variant.perturbation
    kind = p["type"]

    if kind == "append_resume_segment":
        # our authored text, not dataset text
        return resume + "\n" + p["text"], jd
    if kind == "truncate_resume":
        return resume[: p["chars"]], jd
    if kind == "empty_jd":
        return resume, ""
    if kind == "corrupt_encoding":
        # mojibake a slice of the resume: bytes reinterpreted under the wrong codec
        start, end = p["start"], p["end"]
        damaged = resume[start:end].encode("utf-8").decode("latin-1", errors="replace")
        return resume[:start] + damaged + resume[end:], jd
    if kind == "malformed_output":
        # no document change; the fault is injected at the client seam
        return resume, jd
    raise ValueError(f"unknown perturbation type {kind!r} (closed list, eval-design 3c gate 2)")


def faulty_completer(inner: Any, failures: int, node: str = "assess") -> Any:
    """Wrap a completer so the first `failures` assessment calls return
    malformed arguments — exercising retry -> degrade -> escalate on real
    documents rather than in a unit test."""
    state = {"remaining": failures}

    def complete(messages: list[dict[str, Any]], tool_schema: dict[str, Any]) -> Any:
        from agent.client import RawCompletion

        is_assessment = tool_schema["function"]["name"] == "submit_assessment"
        if is_assessment and state["remaining"] > 0:
            state["remaining"] -= 1
            return RawCompletion(arguments_json="{not valid json", tokens_in=10, tokens_out=5)
        return inner(messages, tool_schema)

    return complete
