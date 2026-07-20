"""The assessment graph (design decision 1):

    parse → extract → assess ⟲ (once per dimension, hard_requirements last)
          → aggregate → gate → recommend

Stage E: deterministic stubs, no LLM — proves plumbing and emits a
schema-valid trajectory. Nodes return partial state updates (decision 2b);
trajectory events are emitted as side effects through the writer
(logger-side, decision 2).
"""

import hashlib
import json
import time
from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agent.client import CallMeta
from agent.state import AgentState
from agent.types import Assessment
from agent.tools import (
    DocumentSource,
    assess_dimension_stub,
    document_anomalies,
    flag_for_review,
    get_rubric,
    parse_jd,
    parse_resume,
)
from agent.trajectory_writer import TrajectoryWriter
from agent.types import DIMENSIONS, Aggregate, GateReason
from eval.rubric_loader import load_rubric

from .tools import RUBRIC_PATH

# Design decision 5: boundary band + veto cap.
ADVANCE_THRESHOLD = 3.5
BOUNDARY_FLOOR = 2.5
VETO_CAP = 2.4

# hard_requirements last: it re-reads the other dimensions' determinations.
ASSESS_ORDER = [d for d in DIMENSIONS if d != "hard_requirements"] + ["hard_requirements"]


def config_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def scoring_weights() -> dict[str, float]:
    rubric = load_rubric(RUBRIC_PATH)
    return {d["id"]: float(d["weight"]) for d in rubric.scoring_dimensions}


# Stage F injection seams: extract/assess implementations (stub or client-backed).
Extractor = Callable[[str, str], tuple[dict[str, Any], list[CallMeta]]]
Assessor = Callable[
    [str, dict[str, Any], dict[str, Any], str, str, dict[str, Assessment]],
    tuple[Assessment, list[CallMeta]],
]


def build_graph(
    source: DocumentSource,
    writer: TrajectoryWriter,
    extractor: Extractor | None = None,
    assessor: Assessor | None = None,
) -> CompiledStateGraph[AgentState, Any, AgentState, AgentState]:
    def _timed_tool(tool: str, args_summary: dict[str, Any], fn: Any) -> Any:
        started = time.perf_counter()
        status = "ok"
        try:
            return fn()
        except Exception:
            status = "error"
            raise
        finally:
            writer.emit(
                "tool_call",
                tool=tool,
                status=status,
                latency_ms=int((time.perf_counter() - started) * 1000),
                args_summary=args_summary,
            )

    def parse(state: AgentState) -> dict[str, Any]:
        pair = state["pair"]
        summary = {"split": pair.split, "row": pair.row}
        resume_text = _timed_tool("parse_resume", summary, lambda: parse_resume(source, pair))
        jd_text = _timed_tool("parse_jd", summary, lambda: parse_jd(source, pair))
        return {
            "resume_text": resume_text,
            "jd_text": jd_text,
            "anomalies": document_anomalies(resume_text, jd_text),
        }

    def extract(state: AgentState) -> dict[str, Any]:
        if extractor is not None:
            extraction, metas = extractor(state["resume_text"], state["jd_text"])
            for meta in metas:
                writer.emit(
                    "llm_call",
                    node="extract",
                    purpose="extraction",
                    provider=meta.provider,
                    model=meta.model,
                    tokens_in=meta.tokens_in,
                    tokens_out=meta.tokens_out,
                    latency_ms=meta.latency_ms,
                    attempt=meta.attempt,
                    status=meta.status,
                )
            return {"extraction": extraction, "dimensions_remaining": list(ASSESS_ORDER)}
        # Stage-E stub: no LLM; a fake ok llm_call keeps totals meaningful.
        writer.emit(
            "llm_call",
            node="extract",
            purpose="extraction",
            provider="stub",
            model="stub",
            tokens_in=200,
            tokens_out=50,
            latency_ms=1,
            attempt=1,
            status="ok",
        )
        return {"extraction": {"must_items": []}, "dimensions_remaining": list(ASSESS_ORDER)}

    def assess(state: AgentState) -> dict[str, Any]:
        remaining = list(state["dimensions_remaining"])
        dimension = remaining.pop(0)
        rubric_slice = _timed_tool(
            "get_rubric", {"dimension": dimension}, lambda: get_rubric(dimension)
        )
        assess_fn: Assessor = assessor if assessor is not None else assess_dimension_stub
        assessment, metas = _timed_tool(
            "assess_dimension",
            {"dimension": dimension},
            lambda: assess_fn(
                dimension,
                state["extraction"] or {},
                rubric_slice,
                state["resume_text"],
                state["jd_text"],
                state["assessments"],
            ),
        )
        for meta in metas:
            writer.emit(
                "llm_call",
                node="assess",
                purpose="assessment",
                provider=meta.provider,
                model=meta.model,
                tokens_in=meta.tokens_in,
                tokens_out=meta.tokens_out,
                latency_ms=meta.latency_ms,
                attempt=meta.attempt,
                status=meta.status,
            )
        writer.emit(
            "dimension_assessed",
            dimension=assessment.dimension,
            score=assessment.score,
            degraded=assessment.degraded,
            resolution_failures=assessment.resolution_failures,
            evidence_spans=[s.model_dump() for s in assessment.evidence_spans],
            **(
                {"determinations": [d.model_dump() for d in assessment.determinations]}
                if assessment.determinations
                else {}
            ),
            **({"veto_state": assessment.veto_state} if assessment.veto_state else {}),
        )
        return {
            "assessments": {assessment.dimension: assessment},
            "dimensions_remaining": remaining,
        }

    def assess_router(state: AgentState) -> str:
        return "assess" if state["dimensions_remaining"] else "aggregate"

    def aggregate(state: AgentState) -> dict[str, Any]:
        weights = scoring_weights()
        assessments = state["assessments"]
        hard = assessments["hard_requirements"]
        veto = hard.veto_state or "met"
        missing = [d for d in weights if assessments[d].degraded]
        if missing:
            mean: float | None = None
            capped: float | None = None
        else:
            mean = round(sum((assessments[d].score or 0) * w for d, w in weights.items()), 2)
            capped = min(mean, VETO_CAP) if veto == "unmet" else mean
        return {
            "aggregate": Aggregate(
                weighted_mean=mean,
                capped=capped,
                veto=veto,
                partial=bool(missing),
                missing=missing,
            )
        }

    def gate(state: AgentState) -> dict[str, Any]:
        aggregate_ = state["aggregate"]
        assert aggregate_ is not None
        triggers: list[GateReason] = []
        if aggregate_.veto == "unmet":
            triggers.append("hard_unmet")
        elif aggregate_.veto == "indeterminate":
            triggers.append("hard_indeterminate")
        if (
            aggregate_.capped is not None
            and BOUNDARY_FLOOR <= aggregate_.capped < ADVANCE_THRESHOLD
        ):
            triggers.append("boundary")
        if aggregate_.partial or any(a.degraded for a in state["assessments"].values()):
            # partial covers degraded scoring dims; the any() covers a degraded
            # hard_requirements (weight 0 — never in `missing`, still 3-ii)
            triggers.append("insufficient_evidence")
        if state["anomalies"]:
            triggers.append("anomaly")
        if not triggers:
            return {"gate": None}
        outcome = flag_for_review(triggers, state["mode"])
        writer.emit(
            "gate_event",
            triggers=list(outcome.triggers),
            mode=outcome.mode,
            action=outcome.action,
            resolution=outcome.resolution,
        )
        return {"gate": outcome}

    def recommend(state: AgentState) -> dict[str, Any]:
        aggregate_ = state["aggregate"]
        assert aggregate_ is not None
        if state["gate"] is not None:
            recommendation = "flagged"
        elif aggregate_.capped is not None and aggregate_.capped >= ADVANCE_THRESHOLD:
            recommendation = "advance"
        else:
            recommendation = "do_not_advance"
        writer.emit(
            "run_end",
            recommendation=recommendation,
            aggregate=state["aggregate"].model_dump() if state["aggregate"] else None,
            gate_fired=state["gate"] is not None,
            totals=writer_totals(writer),
        )
        return {"recommendation": recommendation}

    graph: StateGraph[AgentState, Any, AgentState, AgentState] = StateGraph(AgentState)
    graph.add_node("parse", parse)
    graph.add_node("extract", extract)
    graph.add_node("assess", assess)
    graph.add_node("aggregate", aggregate)
    graph.add_node("gate", gate)
    graph.add_node("recommend", recommend)
    graph.add_edge(START, "parse")
    graph.add_edge("parse", "extract")
    graph.add_edge("extract", "assess")
    graph.add_conditional_edges("assess", assess_router, ["assess", "aggregate"])
    graph.add_edge("aggregate", "gate")
    graph.add_edge("gate", "recommend")
    graph.add_edge("recommend", END)
    return graph.compile()


def writer_totals(writer: TrajectoryWriter) -> dict[str, int]:
    """Recompute totals from the written events — the run_end totals are a
    reconciliation promise (invariant 5), so derive them from the same file
    the validator will read."""
    import json as _json

    calls = [
        e
        for e in (
            _json.loads(line) for line in writer.path.read_text(encoding="utf-8").splitlines()
        )
        if e["type"] == "llm_call"
    ]
    return {
        "llm_calls": len(calls),
        "tokens_in": sum(c["tokens_in"] for c in calls),
        "tokens_out": sum(c["tokens_out"] for c in calls),
        "latency_ms": sum(c["latency_ms"] for c in calls),
    }
