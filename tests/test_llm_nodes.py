"""Stage F contract: client-backed extract + assess with scripted completers
(zero live calls), including quote resolution, the post_validate chain, and
the FULL decision 3-ii escalation e2e: double-malformed dimension ->
degraded -> partial aggregate -> insufficient_evidence gate -> trajectory
still schema-valid.
"""

import json
from typing import Any

from agent.client import RawCompletion, provider_config
from agent.llm_tools import assess_dimension_llm, extract_requirements, resolve_quotes
from agent.run import run_pair
from agent.tools import SyntheticSource, get_rubric
from agent.types import EvidenceQuote, PairRef
from eval.trajectory import load_trajectory, validate_data_hygiene, validate_trajectory

CFG = provider_config({"LLM_PROVIDER": "openai", "LLM_API_KEY": "test-key-not-real"})

# Synthetic docs, >=200 chars each (clear of anomaly A2), containing the quote targets.
RESUME_DOC = (
    "Profile: platform engineer. Seven years building Spark and Kafka pipelines at Acme,"
    " owning ingestion reliability, warehouse modeling, and orchestration for three product"
    " teams; led the on-call rotation and the migration to streaming ingestion end to end."
)
JD_DOC = (
    "We are hiring a senior data engineer. Requirements: four or more years of relevant"
    " experience; Spark and Kafka in production required. Duties include designing streaming"
    " pipelines, maintaining the warehouse, and mentoring junior engineers across two teams."
)


def _completer(responses: list[str | None]) -> Any:
    def complete(messages: list[dict[str, Any]], tool_schema: dict[str, Any]) -> RawCompletion:
        return RawCompletion(arguments_json=responses.pop(0), tokens_in=500, tokens_out=60)

    return complete


def _submit(dimension: str, score: int, quote: str, doc: str = "resume") -> str:
    payload: dict[str, Any] = {
        "dimension": dimension,
        "score": score,
        "evidence_quotes": [{"doc": doc, "quote": quote}],
        "notes": "",
    }
    if dimension == "skills_coverage":
        payload["determinations"] = [{"requirement": "R1", "value": "covered"}]
    return json.dumps(payload)


EXTRACTION_STATE: dict[str, Any] = {
    "must_items": [
        {"id": "R1", "tag": "skills", "text": "Spark and Kafka in production"},
        {"id": "R2", "tag": "years", "text": "four or more years relevant"},
    ],
    "derived": False,
    "extraction_degraded": False,
}

EXTRACTION_OK = json.dumps(
    {
        "must_items": [
            {"tag": "skills", "text": "Spark and Kafka in production"},
            {"tag": "years", "text": "four or more years relevant"},
        ],
        "derived": False,
    }
)


# --- quote resolution ---


def test_resolve_quotes_offsets_slice_back_to_the_quote() -> None:
    spans, failures = resolve_quotes(
        [EvidenceQuote(doc="resume", quote="Spark and Kafka pipelines")], RESUME_DOC, JD_DOC
    )
    assert failures == 0 and len(spans) == 1
    s = spans[0]
    assert RESUME_DOC[s.start : s.end] == "Spark and Kafka pipelines"


def test_resolve_quotes_counts_failures() -> None:
    spans, failures = resolve_quotes(
        [EvidenceQuote(doc="jd", quote="this text is nowhere")], RESUME_DOC, JD_DOC
    )
    assert spans == [] and failures == 1


# --- extraction ---


def test_extract_requirements_ok() -> None:
    extraction, metas = extract_requirements(CFG, _completer([EXTRACTION_OK]), RESUME_DOC, JD_DOC)
    assert extraction["extraction_degraded"] is False
    assert [i["tag"] for i in extraction["must_items"]] == ["skills", "years"]
    assert [i["id"] for i in extraction["must_items"]] == ["R1", "R2"]  # tool-side ids (v2)
    assert [m.status for m in metas] == ["ok"]


# --- assess: post_validate chain ---


def test_unresolvable_quote_retries_then_ok() -> None:
    responses: list[str | None] = [
        _submit("skills_coverage", 4, "totally fabricated evidence"),
        _submit("skills_coverage", 4, "Spark and Kafka pipelines"),
    ]
    assessment, metas = assess_dimension_llm(
        CFG,
        _completer(responses),
        "skills_coverage",
        EXTRACTION_STATE,
        get_rubric("skills_coverage"),
        RESUME_DOC,
        JD_DOC,
        {},
    )
    assert not assessment.degraded and assessment.score == 4
    assert [m.status for m in metas] == ["malformed_output", "ok"]
    assert assessment.resolution_failures == 1  # the fabricated quote is counted


def test_hard_requirements_rejects_non_ledger_score() -> None:
    responses: list[str | None] = [
        _submit("hard_requirements", 4, "four or more years of relevant", doc="jd"),
        _submit("hard_requirements", 3, "four or more years of relevant", doc="jd"),
    ]
    assessment, metas = assess_dimension_llm(
        CFG,
        _completer(responses),
        "hard_requirements",
        EXTRACTION_STATE,
        get_rubric("hard_requirements"),
        RESUME_DOC,
        JD_DOC,
        {},
    )
    assert assessment.score == 3 and assessment.veto_state == "indeterminate"
    assert [m.status for m in metas] == ["malformed_output", "ok"]


def test_double_failure_degrades_with_indeterminate_veto_for_hard() -> None:
    bad = _submit("hard_requirements", 4, "four or more years of relevant", doc="jd")
    assessment, metas = assess_dimension_llm(
        CFG,
        _completer([bad, bad]),
        "hard_requirements",
        EXTRACTION_STATE,
        get_rubric("hard_requirements"),
        RESUME_DOC,
        JD_DOC,
        {},
    )
    assert assessment.degraded and assessment.score is None
    assert assessment.veto_state == "indeterminate"  # the ledger could not be read


# --- e2e through the graph with scripted LLM ---


def _wire(responses: list[str | None]) -> tuple[Any, Any]:
    completer = _completer(responses)

    def extractor(resume: str, jd: str) -> Any:
        return extract_requirements(CFG, completer, resume, jd)

    def assessor(
        dimension: str,
        extraction: dict[str, Any],
        rubric_slice: dict[str, Any],
        resume: str,
        jd: str,
        prior: dict[str, Any],
    ) -> Any:
        return assess_dimension_llm(
            CFG, completer, dimension, extraction, rubric_slice, resume, jd, prior
        )

    return extractor, assessor


def test_e2e_live_mocked_trajectory_valid(tmp_path: Any) -> None:
    responses: list[str | None] = [
        EXTRACTION_OK,
        _submit("skills_coverage", 4, "Spark and Kafka pipelines"),
        _submit("experience_level", 5, "Seven years building"),
        _submit("education_domain_fit", 3, "platform engineer"),
        _submit("hard_requirements", 5, "Spark and Kafka in production required", doc="jd"),
    ]
    extractor, assessor = _wire(responses)
    final, writer = run_pair(
        SyntheticSource(RESUME_DOC, JD_DOC),
        PairRef(split="train", row=0),
        "eval",
        tmp_path,
        provider=CFG.provider,
        model=CFG.model,
        extractor=extractor,
        assessor=assessor,
    )
    events = load_trajectory(writer.path)
    assert validate_trajectory(events) == []
    assert validate_data_hygiene(events, {"resume": RESUME_DOC, "jd": JD_DOC}) == []
    aggregate = final["aggregate"]
    assert aggregate is not None and aggregate.veto == "met"
    # 0.5*4 + 0.3*5 + 0.2*3 = 4.1 -> above band, veto met, no anomalies: advance
    assert aggregate.weighted_mean == 4.1 and aggregate.capped == 4.1
    assert final["gate"] is None
    assert final["recommendation"] == "advance"


def test_e2e_degraded_dimension_full_3ii_chain(tmp_path: Any) -> None:
    bad_edu = _submit("education_domain_fit", 99, "platform engineer")
    responses: list[str | None] = [
        EXTRACTION_OK,
        _submit("skills_coverage", 4, "Spark and Kafka pipelines"),
        _submit("experience_level", 5, "Seven years building"),
        bad_edu,
        bad_edu,  # second failure -> degraded
        _submit("hard_requirements", 5, "Spark and Kafka in production required", doc="jd"),
    ]
    extractor, assessor = _wire(responses)
    final, writer = run_pair(
        SyntheticSource(RESUME_DOC, JD_DOC),
        PairRef(split="train", row=0),
        "eval",
        tmp_path,
        provider=CFG.provider,
        model=CFG.model,
        extractor=extractor,
        assessor=assessor,
    )
    events = load_trajectory(writer.path)
    assert validate_trajectory(events) == []  # incl. invariant 4: degraded => gate
    aggregate = final["aggregate"]
    assert aggregate is not None
    assert aggregate.partial and aggregate.weighted_mean is None
    assert aggregate.missing == ["education_domain_fit"]
    gate = final["gate"]
    assert gate is not None and "insufficient_evidence" in gate.triggers
    assert final["recommendation"] == "flagged"


# --- the symmetric carrier contract (finding 007) ---


def test_verbatim_requirement_label_rejected_then_ok() -> None:
    verbatim = json.dumps(
        {
            "dimension": "skills_coverage",
            "score": 4,
            "evidence_quotes": [{"doc": "resume", "quote": "Spark and Kafka pipelines"}],
            "determinations": [
                # copies >=20 chars of the JD verbatim -> must be rejected
                {"requirement": "four or more years of relevant experience", "value": "covered"}
            ],
            "notes": "",
        }
    )
    responses: list[str | None] = [
        verbatim,
        _submit("skills_coverage", 4, "Spark and Kafka pipelines"),
    ]
    assessment, metas = assess_dimension_llm(
        CFG,
        _completer(responses),
        "skills_coverage",
        EXTRACTION_STATE,
        get_rubric("skills_coverage"),
        RESUME_DOC,
        JD_DOC,
        {},
    )
    assert [m.status for m in metas] == ["malformed_output", "ok"]
    assert not assessment.degraded and assessment.score == 4


def test_wire_schema_caps_requirement_length() -> None:
    from agent.types import submit_assessment_tool

    schema = submit_assessment_tool()["function"]["parameters"]
    requirement = schema["$defs"]["Determination"]["properties"]["requirement"]
    assert requirement["maxLength"] == 80
