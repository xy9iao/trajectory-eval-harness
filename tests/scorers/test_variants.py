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

from eval.variants import SPECS, Variant, load_variants, materialize


def _raw() -> dict[str, Any]:
    import json

    return dict(json.loads(SPECS.read_text(encoding="utf-8")))


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


def test_fault_batch_count_is_within_the_ratified_range() -> None:
    faults = [v for v in load_variants() if v.batch == "fault"]
    assert 5 <= len(faults) <= 6, "fault samples: ratified range is 5-6"


def test_undersized_negative_set_must_be_declared_not_padded() -> None:
    # Gate 1 asks for 6-8 gate negatives; gate 5 forbids admitting a broken
    # construction. When they conflict GATE 5 WINS (ruling 2026-08-02): the
    # count is a target, never a quota, because padding to hit it manufactures
    # phantom true-negatives. So an undersized set is legal ONLY while the
    # spec says out loud that it is undersized and why.
    negatives = [v for v in load_variants() if v.batch == "gate_negative"]
    if len(negatives) < 6:
        status = _raw().get("negative_set_status", "")
        assert "UNDER-POPULATED" in status, (
            f"{len(negatives)} gate negatives is below gate 1's range — legal only with an "
            "explicit negative_set_status declaring it, never by quietly adding variants back"
        )
        assert "GATE 5 WINS" in status
    assert len(negatives) <= 8, "gate negatives: ratified ceiling is 8"


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


def test_negative_set_is_high_road_only_and_says_so() -> None:
    # The low road (meets every stated must, still scores below 2.5 -> no gate,
    # do_not_advance) is ABSENT BY RULING, not by oversight. Mechanism, verified
    # in finding 014: the hard-requirement ledger REUSES the determinations that
    # produce skills_coverage and experience_level (28/30 ledgers say so in
    # prose), so the low road asks two coupled variables to move in opposite
    # directions. The eligible corner is 16/216 band combinations and 0/30
    # reference pairs. Two attempts (cf-01, cf-02) failed exactly here. This
    # test pins the absence to the record so a later reader does not "fix" the
    # gap by adding a low-road variant back.
    negatives = [v for v in load_variants() if v.batch == "gate_negative"]
    assert all("advance." in v.rationale for v in negatives)
    assert not any("do_not_advance." in v.rationale for v in negatives), (
        "a low-road negative is near-impossible under this rubric's score geometry — "
        "if you are adding one, read the construction_failures block first"
    )
    assert _raw()["construction_failures"], "the failed low-road constructions must stay recorded"


def test_construction_failures_never_leak_into_the_variant_set() -> None:
    # 3c gate 5: a variant whose result contradicts its expectation is a broken
    # CONSTRUCTION until proven otherwise. Recording it as a negative would
    # manufacture a phantom true-negative and corrupt the headline metric — the
    # exact failure this whole batch exists to avoid.
    raw = _raw()
    live = {v.id for v in load_variants()}
    for failure in raw["construction_failures"]:
        assert failure["id"] not in live, (
            f"{failure['id']} is a failed construction, not a test case"
        )
        for field in ("intended", "expected", "actual", "cause"):
            assert failure.get(field, "").strip(), f"{failure['id']}: missing '{field}'"
    assert "construction is wrong" in raw["construction_failure_rule"]


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
