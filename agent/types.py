"""Single-source types (design decision 7b): one definition, three imports —
client validation (`model_validate`), graph state annotation, scorer
assertion. The provider-facing wire schema is GENERATED from these models
(`submit_assessment_tool()`), so the contract the model must obey and the
validator that checks it are the same object; prompt-side/validation-side
schema drift is structurally impossible.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

DIMENSIONS = (
    "skills_coverage",
    "experience_level",
    "education_domain_fit",
    "hard_requirements",
)
Dimension = Literal[
    "skills_coverage", "experience_level", "education_domain_fit", "hard_requirements"
]
Doc = Literal["jd", "resume"]
VetoState = Literal["met", "indeterminate", "unmet"]
GateReason = Literal[
    "hard_unmet", "hard_indeterminate", "boundary", "insufficient_evidence", "anomaly"
]
AgentMode = Literal["interactive", "eval"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PairRef(StrictModel):
    split: Literal["train", "test"]
    row: int = Field(ge=0)


class Determination(StrictModel):
    requirement: str = Field(min_length=1)
    value: Literal["covered", "partial", "absent"]


class EvidenceQuote(StrictModel):
    """What the MODEL submits: a verbatim quote. Resolved tool-side to offsets
    (decision 3); quotes never enter the trajectory (schema invariant 7)."""

    doc: Doc
    quote: str = Field(min_length=1)


class SubmitAssessment(StrictModel):
    """The wire contract — the model must return each assessment AS this
    function call. evidence_quotes is required and non-empty: D7 as an
    API-level guarantee, not a prompt-level request."""

    dimension: Dimension
    score: int = Field(ge=0, le=5)
    evidence_quotes: list[EvidenceQuote] = Field(min_length=1)
    determinations: list[Determination] | None = None
    notes: str = ""


class EvidenceSpan(StrictModel):
    """Resolved raw-document offsets — the same convention as the reference
    labels and rubric anchors."""

    doc: Doc
    start: int = Field(ge=0)
    end: int

    @model_validator(mode="after")
    def _ordered(self) -> "EvidenceSpan":
        if self.end <= self.start:
            raise ValueError(f"span end {self.end} must be > start {self.start}")
        return self


class Assessment(StrictModel):
    """Post-resolution result (what the trajectory's dimension_assessed
    carries). Mirrors schema invariant 2: degraded ⇔ score is null."""

    dimension: Dimension
    score: int | None = None
    degraded: bool = False
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    resolution_failures: int = Field(default=0, ge=0)
    determinations: list[Determination] | None = None
    veto_state: VetoState | None = None
    notes: str = ""

    @model_validator(mode="after")
    def _score_consistent(self) -> "Assessment":
        if self.degraded and self.score is not None:
            raise ValueError("degraded assessment must carry score=None")
        if not self.degraded and not (isinstance(self.score, int) and 0 <= self.score <= 5):
            raise ValueError("non-degraded assessment needs an int score in 0..5")
        return self


class Aggregate(StrictModel):
    """weighted_mean is the RAW mean; capped is post-veto-cap (machine reads
    capped, human sees raw — decision 5c). partial ⇔ weighted_mean null ⇔
    missing nonempty (schema invariant 4)."""

    weighted_mean: float | None
    capped: float | None
    veto: VetoState
    partial: bool
    missing: list[str] = Field(default_factory=list)


class GateOutcome(StrictModel):
    triggers: list[GateReason]
    mode: AgentMode
    action: Literal["interrupt", "auto_resume"]
    resolution: Literal["approved", "edited", "rejected", "auto"]


def veto_from_score(score: int) -> VetoState:
    """hard_requirements ledger score -> soft-veto state (rubric wiring)."""
    return {0: "unmet", 3: "indeterminate", 5: "met"}[score]  # type: ignore[return-value]


def submit_assessment_tool() -> dict[str, Any]:
    """The function-calling tool definition, generated from SubmitAssessment —
    single source for wire contract and validator."""
    return {
        "type": "function",
        "function": {
            "name": "submit_assessment",
            "description": (
                "Submit the assessment for one rubric dimension. evidence_quotes"
                " must be verbatim substrings of the resume or JD."
            ),
            "parameters": SubmitAssessment.model_json_schema(),
        },
    }
