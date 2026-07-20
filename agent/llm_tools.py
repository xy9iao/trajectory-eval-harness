"""Client-backed extract + assess (Stage F; design decisions 3 and 7).

Prompt layout follows the prefix discipline (decision 3): invariant content
(system + documents + extraction) forms a shared prefix across the four
assess calls; per-dimension content (rubric slice, instructions) rides the
suffix — provider prefix caching amortizes the raw-document cost.

Evidence flow (decision 3): the model submits verbatim quotes; quotes are
resolved here to raw offsets with the SAME search semantics as the
--find/--span verification tools (corpus.find_offsets); an assessment
whose quotes all fail resolution is a validation failure and joins the
retry/degrade chain — fabricated evidence is structurally unable to pass.

Degraded hard_requirements carries veto_state="indeterminate": the ledger
could not be read, which is exactly what indeterminate means ("cannot
decide from the text") — this keeps schema invariant 4's aggregate/veto
coherence intact and routes the pair to the gate through BOTH
hard_indeterminate and insufficient_evidence.
"""

import json
import sys
from pathlib import Path
from typing import Any

import yaml

from agent.client import CallMeta, Completer, ProviderConfig, call_with_validation
from agent.types import (
    Assessment,
    EvidenceQuote,
    EvidenceSpan,
    ExtractRequirements,
    SubmitAssessment,
    VetoState,
    extract_requirements_tool,
    submit_assessment_tool,
    veto_from_score,
)

SYSTEM = (
    "You are a resume-screening assessor. Judge ONLY from the resume and job"
    " description provided. Every claim must be supported by verbatim quotes"
    " from the documents — quotes are checked mechanically against the raw"
    " text, and unverifiable quotes invalidate your response."
)

HARD_SCORES = (0, 3, 5)


def _find_first(text: str, needle: str) -> tuple[int, int] | None:
    """Same case-insensitive search semantics as data/corpus.py find_offsets
    (imported via path shim — data/ is not a package)."""
    data_dir = str(Path(__file__).resolve().parents[1] / "data")
    if data_dir not in sys.path:
        sys.path.insert(0, data_dir)
    from corpus import find_offsets

    hits = find_offsets(text, needle, limit=1)
    return hits[0] if hits else None


def resolve_quotes(
    quotes: list[EvidenceQuote], resume_text: str, jd_text: str
) -> tuple[list[EvidenceSpan], int]:
    """Quotes -> resolved raw offsets; returns (spans, failure_count)."""
    spans: list[EvidenceSpan] = []
    failures = 0
    for quote in quotes:
        text = resume_text if quote.doc == "resume" else jd_text
        hit = _find_first(text, quote.quote)
        if hit is None:
            failures += 1
        else:
            spans.append(EvidenceSpan(doc=quote.doc, start=hit[0], end=hit[1]))
    return spans, failures


def shared_prefix(
    resume_text: str, jd_text: str, extraction: dict[str, Any]
) -> list[dict[str, Any]]:
    return [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": (
                f"RESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{jd_text}\n\n"
                f"EXTRACTED REQUIREMENTS:\n{json.dumps(extraction, ensure_ascii=False)}"
            ),
        },
    ]


def extract_requirements(
    cfg: ProviderConfig, completer: Completer, resume_text: str, jd_text: str
) -> tuple[dict[str, Any], list[CallMeta]]:
    messages = [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": (
                f"JOB DESCRIPTION:\n{jd_text}\n\nRESUME:\n{resume_text}\n\n"
                "Extract the JD's must/required items (bundle = one item). If the"
                " JD states no must-have skills, derive skill requirements from"
                " its duties section and set derived=true (rubric v1.1)."
            ),
        },
    ]
    call = call_with_validation(
        messages, ExtractRequirements, extract_requirements_tool(), completer, cfg
    )
    if call.result is None:
        return {"must_items": [], "derived": False, "extraction_degraded": True}, call.attempts
    return call.result.model_dump() | {"extraction_degraded": False}, call.attempts


def assess_dimension_llm(
    cfg: ProviderConfig,
    completer: Completer,
    dimension: str,
    extraction: dict[str, Any],
    rubric_slice: dict[str, Any],
    resume_text: str,
    jd_text: str,
    prior: dict[str, Assessment],
) -> tuple[Assessment, list[CallMeta]]:
    suffix = [
        f"Assess exactly one dimension now: {dimension}.",
        "RUBRIC SLICE (criteria, scope notes, determination rules):\n"
        + yaml.safe_dump(rubric_slice, allow_unicode=True, sort_keys=False),
    ]
    if dimension == "skills_coverage":
        suffix.append(
            "Include determinations: one covered/partial/absent judgment per"
            " must-have skill requirement."
        )
    if dimension == "hard_requirements":
        prior_summary = {
            d: {
                "score": a.score,
                "determinations": (
                    [x.model_dump() for x in a.determinations] if a.determinations else None
                ),
            }
            for d, a in prior.items()
        }
        suffix.append(
            "PRIOR DIMENSION RESULTS (reuse these determinations for the ledger):\n"
            + json.dumps(prior_summary, ensure_ascii=False)
        )
        suffix.append("The hard_requirements score MUST be exactly 0, 3, or 5.")
    messages = shared_prefix(resume_text, jd_text, extraction) + [
        {"role": "user", "content": "\n\n".join(suffix)}
    ]

    resolution: dict[str, Any] = {"spans": [], "total_failures": 0}

    def post_validate(parsed: SubmitAssessment) -> str | None:
        if parsed.dimension != dimension:
            return f"dimension must be {dimension!r}"
        if dimension == "hard_requirements" and parsed.score not in HARD_SCORES:
            return "hard_requirements score must be exactly 0, 3, or 5"
        spans, failures = resolve_quotes(parsed.evidence_quotes, resume_text, jd_text)
        resolution["spans"] = spans
        resolution["total_failures"] += failures
        if not spans:
            return (
                "none of the evidence_quotes are verbatim substrings of the"
                " documents — quote exactly"
            )
        return None

    call = call_with_validation(
        messages,
        SubmitAssessment,
        submit_assessment_tool(),
        completer,
        cfg,
        post_validate=post_validate,
    )
    if call.result is None:
        veto: VetoState | None = "indeterminate" if dimension == "hard_requirements" else None
        return (
            Assessment(
                dimension=dimension,  # type: ignore[arg-type]
                score=None,
                degraded=True,
                evidence_spans=[],
                resolution_failures=resolution["total_failures"],
                veto_state=veto,
                notes="degraded: output failed validation after retry (3-ii escalation)",
            ),
            call.attempts,
        )
    parsed = call.result
    return (
        Assessment(
            dimension=parsed.dimension,
            score=parsed.score,
            degraded=False,
            evidence_spans=resolution["spans"],
            resolution_failures=resolution["total_failures"],
            determinations=parsed.determinations,
            veto_state=(
                veto_from_score(parsed.score) if dimension == "hard_requirements" else None
            ),
            notes=parsed.notes,
        ),
        call.attempts,
    )
