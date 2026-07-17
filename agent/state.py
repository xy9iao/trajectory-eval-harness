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

    Carve-out analysis (CC, for owner ruling): the design-doc carve-out for
    "legitimate rewrites (retry after malformed output)" may be UNNECESSARY at
    the state layer — retries happen INSIDE assess_dimension (client layer,
    decision 7), so one dimension pass produces exactly one state write no
    matter how many llm_call attempts it took. If that holds, this reducer can
    be strictly raise-on-duplicate with no exception, and the legal-rewrite
    definition lives only at the trajectory layer (invariant 6, llm_call
    attempts). Owner confirms or refutes; rationale goes to Problems & Fixes.
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
