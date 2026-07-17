"""Graph state (design decision 2): the run's entire working memory — and
exactly what the checkpointer saves at an interrupt.

By-value documents (2a: hermetic runs, pass^k internal validity), TypedDict
(2c: framework idiom), assessments under a merge reducer (2b), trajectory
events deliberately NOT here (logger-side: evidence must not depend on the
observed party surviving).
"""

from typing import Annotated, Any, TypedDict

from agent.types import Aggregate, AgentMode, Assessment, GateOutcome, PairRef


def merge_assessments(
    left: dict[str, Assessment], right: dict[str, Assessment]
) -> dict[str, Assessment]:
    """OWNER-IMPLEMENTED — decision 2b's reserved design commitment.

    Contract (tests/test_graph_skeleton.py::TestMergeReducer):
    - disjoint keys merge into one dict;
    - a key already present in `left` raises ValueError naming the dimension
      (the default dict-union semantics silently overwrite — which would mask
      assess-loop cursor bugs and disarm schema invariant 2's alarm).

    RULED (owner, 2026-07-17): strict raise, NO carve-out. Retries live inside
    assess_dimension (client layer), so one dimension pass produces exactly one
    state write — "legitimate duplicate" has no members at this layer; any
    duplicate reaching this reducer is a bug. The legitimate-rewrite concept
    lives only at the trajectory layer (invariant 6). See p1-design.md
    decision 2b supersede.
    """
    raise NotImplementedError("owner writes this — decision 2b (Stage E)")


class AgentState(TypedDict):
    # identity & config — set once at run_start, never mutated
    pair: PairRef
    mode: AgentMode
    rubric_version: str
    # documents, by value (2a)
    resume_text: str
    jd_text: str
    # deterministic parse-time anomaly findings (design decision 5b closed list)
    anomalies: list[str]
    # working products
    extraction: dict[str, Any] | None
    dimensions_remaining: list[str]
    assessments: Annotated[dict[str, Assessment], merge_assessments]
    # downstream
    aggregate: Aggregate | None
    gate: GateOutcome | None
    recommendation: str | None
