"""Review artifact for the interactive gate (design decision 6c).

review/ is gitignored: evidence TEXT is legal here and nowhere else — the
reviewer must see what the scores rest on. Raw and capped aggregates sit
side by side (decision 5c: the cap constrains the machine's conclusion,
not the human's information).

Re-execution contract (the Stage-G lesson): the gate node re-runs from its
top on resume, so `write_review_file` is idempotent-by-existence — it
never overwrites an existing file, because by resume time the human has
edited it.
"""

import re
from pathlib import Path
from typing import Any

from agent.state import AgentState
from agent.types import GateReason

DECISION_RE = re.compile(r"^decision:\s*(approve|edit|reject)\s*$", re.MULTILINE | re.IGNORECASE)


def build_payload(state: AgentState, triggers: list[GateReason]) -> dict[str, Any]:
    aggregate = state["aggregate"]
    assert aggregate is not None
    docs = {"resume": state["resume_text"], "jd": state["jd_text"]}
    dimensions = []
    for dimension, a in state["assessments"].items():
        dimensions.append(
            {
                "dimension": dimension,
                "score": a.score,
                "degraded": a.degraded,
                "veto_state": a.veto_state,
                "evidence": [
                    {
                        "doc": s.doc,
                        "span": f"{s.start}:{s.end}",
                        "text": docs[s.doc][s.start : s.end],
                    }
                    for s in a.evidence_spans
                ],
                "notes": a.notes,
            }
        )
    return {
        "pair": state["pair"].model_dump(),
        "triggers": list(triggers),
        "dimensions": dimensions,
        "aggregate_raw": aggregate.weighted_mean,
        "aggregate_capped": aggregate.capped,
        "veto": aggregate.veto,
        "machine_draft": "flagged",
    }


def write_review_file(review_dir: Path, run_id: str, payload: dict[str, Any]) -> Path:
    """Idempotent by existence — never clobbers the human's edits on re-run."""
    review_dir.mkdir(parents=True, exist_ok=True)
    path = review_dir / f"{run_id}.md"
    if path.exists():
        return path
    lines = [
        f"# Gate review — {run_id}",
        "",
        f"pair: {payload['pair']['split']}:{payload['pair']['row']}",
        f"triggers: {', '.join(payload['triggers'])}",
        f"aggregate: raw={payload['aggregate_raw']} capped={payload['aggregate_capped']}"
        f" veto={payload['veto']}",
        f"machine draft: {payload['machine_draft']}",
        "",
        "## Dimensions",
        "",
    ]
    for d in payload["dimensions"]:
        lines.append(
            f"### {d['dimension']} — score {d['score']}"
            + (" (degraded)" if d["degraded"] else "")
            + (f" · veto {d['veto_state']}" if d["veto_state"] else "")
        )
        for ev in d["evidence"]:
            lines.append(f"- [{ev['doc']} {ev['span']}] {ev['text']!r}")
        if d["notes"]:
            lines.append(f"- notes: {d['notes']}")
        lines.append("")
    lines += [
        "---",
        "",
        "Edit the line below to one of: approve · edit · reject — then run:",
        f"    python -m agent.run --resume {run_id}",
        "",
        "decision: pending",
        "",
    ]
    content = "\n".join(lines)
    path.write_text(content, encoding="utf-8")
    return path


def read_decision(review_dir: Path, run_id: str) -> str | None:
    """The human's decision, lowercased; None while still 'pending'/absent."""
    path = review_dir / f"{run_id}.md"
    if not path.exists():
        return None
    match = DECISION_RE.search(path.read_text(encoding="utf-8"))
    return match.group(1).lower() if match else None
