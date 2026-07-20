"""The six orchestration-contract tools (design decision 3 signature table).

Stage E ships parse/get_rubric/flag_for_review real and assess_dimension as
a deterministic STUB (no LLM) — the graph and trajectory plumbing are proven
before a token is spent. Stage F replaces the stub with the client-backed
implementation; signatures do not change.

`submit_assessment` is not a callable here: it is the wire contract the
MODEL is forced to use (agent/types.submit_assessment_tool).
"""

from pathlib import Path
from typing import Any, Protocol

from agent.client import CallMeta
from agent.types import (
    Assessment,
    Determination,
    EvidenceSpan,
    GateOutcome,
    GateReason,
    PairRef,
    veto_from_score,
)
from eval.rubric_loader import load_rubric

RUBRIC_PATH = Path(__file__).resolve().parents[1] / "rubrics" / "rubric-v1.yaml"
ANOMALY_MIN_CHARS = 200  # design decision 5b, item A2


class DocumentSource(Protocol):
    """Seam between the graph and where documents come from (real corpus vs
    synthetic test pairs). Keeps the skeleton runnable without the gitignored
    dataset — and CI-safe."""

    def load(self, pair: PairRef) -> tuple[str, str]:
        """Returns (resume_text, jd_text). Raises on load/decode failure (A3)."""
        ...


class SyntheticSource:
    """Fixed synthetic documents for tests and the skeleton runner."""

    def __init__(self, resume_text: str, jd_text: str) -> None:
        self._docs = (resume_text, jd_text)

    def load(self, pair: PairRef) -> tuple[str, str]:
        return self._docs


class CorpusSource:
    """Real pinned-CSV documents via data/corpus.py (which is not a package —
    hence the explicit path shim, same convention as the data/ tools)."""

    def load(self, pair: PairRef) -> tuple[str, str]:
        import sys

        data_dir = str(Path(__file__).resolve().parents[1] / "data")
        if data_dir not in sys.path:
            sys.path.insert(0, data_dir)
        from corpus import DOC_COLUMNS, load_row

        row = load_row(pair.split, pair.row)
        return row[DOC_COLUMNS["resume"]], row[DOC_COLUMNS["jd"]]


def parse_resume(source: DocumentSource, pair: PairRef) -> str:
    return source.load(pair)[0]


def parse_jd(source: DocumentSource, pair: PairRef) -> str:
    return source.load(pair)[1]


def document_anomalies(resume_text: str, jd_text: str) -> list[str]:
    """Design decision 5b: the CLOSED deterministic list — A1 empty, A2 short.
    (A3 load/decode failure surfaces as a raised exception in parse.)
    Nothing else may be added here in P1."""
    findings = []
    for name, text in (("resume", resume_text), ("jd", jd_text)):
        stripped = text.strip()
        if not stripped:
            findings.append(f"{name}: empty document (A1)")
        elif len(stripped) < ANOMALY_MIN_CHARS:
            findings.append(f"{name}: under {ANOMALY_MIN_CHARS} chars (A2)")
    return findings


def get_rubric(dimension: str) -> dict[str, Any]:
    """The dimension's rubric slice (criteria, scope_notes, determination
    rules, anchors) for the assess prompt."""
    rubric = load_rubric(RUBRIC_PATH)
    (slice_,) = [d for d in rubric.dimensions if d["id"] == dimension]
    return slice_


# Deterministic stub scores: chosen so the skeleton exercises the veto path
# (hard=3 -> indeterminate -> gate) with in-band aggregate (boundary trigger).
_STUB_SCORES = {
    "skills_coverage": 3,
    "experience_level": 3,
    "education_domain_fit": 3,
    "hard_requirements": 3,
}


def assess_dimension_stub(
    dimension: str,
    extraction: dict[str, Any],
    rubric_slice: dict[str, Any],
    resume_text: str,
    jd_text: str,
) -> tuple[Assessment, list[CallMeta]]:
    """Stage-E stand-in for the LLM-backed assess_dimension. Deterministic:
    fixed score per dimension, evidence span = the first 30 chars of the
    resume (resolved-offset convention, always in-bounds for non-anomalous
    docs), one fake ok llm_call's metadata for trajectory totals."""
    score = _STUB_SCORES[dimension]
    assessment = Assessment(
        dimension=dimension,  # type: ignore[arg-type]
        score=score,
        evidence_spans=[EvidenceSpan(doc="resume", start=0, end=min(30, len(resume_text)))],
        determinations=(
            [Determination(requirement="stub requirement", value="partial")]
            if dimension == "skills_coverage"
            else None
        ),
        veto_state=veto_from_score(score) if dimension == "hard_requirements" else None,
        notes="deterministic stub (Stage E)",
    )
    meta = CallMeta(
        provider="stub",
        model="stub",
        tokens_in=100,
        tokens_out=25,
        latency_ms=1,
        attempt=1,
        status="ok",
    )
    return assessment, [meta]


def flag_for_review(
    triggers: list[GateReason],
    mode: str,
) -> GateOutcome:
    """Stage E: eval-mode wiring only (auto_resume/auto). Interactive
    interrupt lands in Stage G behind the same signature."""
    return GateOutcome(
        triggers=triggers,
        mode=mode,  # type: ignore[arg-type]
        action="auto_resume",
        resolution="auto",
    )
