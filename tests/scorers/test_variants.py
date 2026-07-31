"""Variant-spec self-verification (eval-design 3b/3c).

The variant set is a suite of unit tests with known answers, so the specs
themselves need tests: the scope gates are only binding if something
enforces them.

Structural: counts inside their ranges, closed perturbation types, every
variant carrying its one-sentence expectation.

Semantic-boundary: a spec whose stated expectation contradicts its own
perturbation (a gate negative expecting the gate to fire) must be rejected
— a variant that cannot fail is not a test, and a variant whose answer
disagrees with its construction is worse than none.
"""

from typing import Any

import pytest

from eval.variants import Variant, load_variants, materialize

CLOSED_TYPES = {
    "append_resume_segment",
    "truncate_resume",
    "empty_jd",
    "corrupt_encoding",
    "malformed_output",
}


def _spec(**over: Any) -> Variant:
    base: dict[str, Any] = {
        "id": "t-01",
        "batch": "gate_negative",
        "base_pair": {"split": "train", "row": 596},
        "perturbation": {"type": "append_resume_segment", "text": "x"},
        "changed": "appended a segment",
        "expected_gate": False,
        "expected_reasons": [],
        "rationale": "test",
    }
    return Variant(**(base | over))


# --- scope gates (3c) ---


def test_batch_counts_are_within_the_ratified_ranges() -> None:
    variants = load_variants()
    negatives = [v for v in variants if v.batch == "gate_negative"]
    faults = [v for v in variants if v.batch == "fault"]
    assert 6 <= len(negatives) <= 8, "gate negatives: ratified range is 6-8"
    assert 5 <= len(faults) <= 6, "fault samples: ratified range is 5-6"


def test_perturbation_types_stay_closed() -> None:
    for v in load_variants():
        assert v.perturbation["type"] in CLOSED_TYPES, (
            f"{v.id} uses an unratified perturbation type — a new type needs a new ruling"
        )


def test_every_variant_states_what_changed_and_what_is_expected() -> None:
    for v in load_variants():
        assert v.changed.strip(), f"{v.id}: no 'changed' sentence"
        assert v.rationale.strip(), f"{v.id}: no expectation rationale"
        assert isinstance(v.expected_gate, bool)


def test_both_negative_routes_are_represented() -> None:
    # the high road (meets the musts and scores well -> advance) and the low
    # road (meets the musts, still weak -> do_not_advance) are different
    # no-gate cases; a set with only one route tests only half the boundary
    negatives = [v for v in load_variants() if v.batch == "gate_negative"]
    advance = [v for v in negatives if "advance." in v.rationale]
    do_not = [v for v in negatives if "do_not_advance." in v.rationale]
    assert advance and do_not, "gate negatives must cover both advance and do_not_advance"


def test_fault_batch_covers_each_failure_route() -> None:
    kinds = {v.perturbation["type"] for v in load_variants() if v.batch == "fault"}
    assert {"truncate_resume", "empty_jd", "corrupt_encoding", "malformed_output"} <= kinds


# --- semantic boundary: a spec that contradicts itself ---


def test_gate_negative_expecting_a_gate_is_a_contradiction() -> None:
    # SEMANTIC-BOUNDARY: this spec is structurally well-formed — right type,
    # has both sentences, counts fine — and still nonsense: a gate negative
    # whose expectation is that the gate fires tests nothing. Type checks
    # alone would pass it.
    bad = _spec(expected_gate=True, expected_reasons=["hard_unmet"])
    assert bad.batch == "gate_negative" and bad.expected_gate is True
    contradictory = bad.batch == "gate_negative" and bad.expected_gate
    assert contradictory, "the checker below must catch exactly this shape"
    for v in load_variants():
        assert not (v.batch == "gate_negative" and v.expected_gate), (
            f"{v.id}: a gate negative that expects the gate to fire is not a test"
        )


def test_fault_expectations_name_their_trigger_or_declare_unconstrained() -> None:
    for v in load_variants():
        if v.batch != "fault":
            continue
        # either the variant names the trigger it must produce, or it declares
        # itself unconstrained (graceful-handling checks assert validity, not
        # triggers) — silence about the expectation is what is forbidden
        assert "expect" in v.rationale.lower() or v.expected_reasons, (
            f"{v.id}: fault variants must state the expected trigger or say why none"
        )


# --- materialization (needs the gitignored corpus; skipped without it) ---


def _corpus_available() -> bool:
    from pathlib import Path

    return (Path(__file__).resolve().parents[2] / "data" / "raw" / "train.csv").exists()


needs_corpus = pytest.mark.skipif(
    not _corpus_available(), reason="raw dataset not present (gitignored)"
)


@needs_corpus
def test_materialize_applies_each_perturbation() -> None:
    by_id = {v.id: v for v in load_variants()}
    resume, jd = materialize(by_id["gn-01"])
    assert "Spring Boot" in resume  # our authored segment is present
    trunc_resume, _ = materialize(by_id["fs-01"])
    assert len(trunc_resume) == 150
    _, empty = materialize(by_id["fs-02"])
    assert empty == ""


@needs_corpus
def test_specs_carry_no_dataset_text() -> None:
    # data discipline: the spec file stores a pair reference plus OUR text;
    # never a slice of the corpus (same rule as reference labels)
    import json
    from pathlib import Path
    import sys

    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "data"))
    from corpus import DOC_COLUMNS, load_row

    raw = json.loads((root / "data" / "variants" / "variants-v1.json").read_text(encoding="utf-8"))
    blob = json.dumps(raw)
    for v in load_variants():
        row = load_row(*v.pair_key)
        for column in DOC_COLUMNS.values():
            text = row[column]
            for i in range(0, max(1, len(text) - 40), 40):
                assert text[i : i + 40] not in blob, f"{v.id}: spec carries dataset text"


@needs_corpus
def test_unknown_perturbation_type_raises() -> None:
    with pytest.raises(ValueError, match="closed list"):
        materialize(_spec(perturbation={"type": "invent_a_new_kind"}))
