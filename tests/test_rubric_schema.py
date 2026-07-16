"""Rubric v1 structural contract (PR #3): CI fails if the YAML stops honoring
what its own comments promise — weights, veto wiring, span integrity.

The in-bounds span check needs the raw CSVs (gitignored, Decision 5), so it
skips where the data is absent (CI) and runs on any machine that has run
data/download_dataset.py.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))

from corpus import DOC_COLUMNS, RAW_DIR, load_row  # noqa: E402

from eval.rubric_loader import Rubric, load_rubric  # noqa: E402

RUBRIC_PATH = ROOT / "rubrics" / "rubric-v1.yaml"


@pytest.fixture(scope="module")
def rubric() -> Rubric:
    return load_rubric(RUBRIC_PATH)


def test_no_todo_tokens_remain() -> None:
    text = RUBRIC_PATH.read_text(encoding="utf-8")
    assert "TODO" not in text, "rubric still carries TODO tokens"


def test_scoring_weights_sum_to_one(rubric: Rubric) -> None:
    weights = [d["weight"] for d in rubric.scoring_dimensions]
    assert sum(weights) == pytest.approx(1.0), f"scoring weights {weights} must sum to 1.0"


def test_veto_dimension_excluded_from_mean(rubric: Rubric) -> None:
    """hard_requirements acts only through the soft veto: weight 0 keeps it out of
    any weighted mean, and the veto wiring must point at it."""
    assert rubric.veto_dimension_id == "hard_requirements"
    (veto_dim,) = [d for d in rubric.dimensions if d["id"] == rubric.veto_dimension_id]
    assert veto_dim["weight"] == 0
    assert veto_dim not in rubric.scoring_dimensions


def test_anchor_spans_well_formed(rubric: Rubric) -> None:
    for dim in rubric.dimensions:
        for anchor in dim.get("anchors", []):
            assert anchor["pair"]["split"] in {"train", "test"}
            for span in anchor["evidence_spans"]:
                assert span["doc"] in DOC_COLUMNS, f"{dim['id']}: unknown doc {span['doc']!r}"
                start, end = span["start"], span["end"]
                assert isinstance(start, int) and isinstance(end, int), f"{dim['id']}: {span}"
                assert 0 <= start < end, f"{dim['id']}: empty or negative span {span}"


@pytest.mark.skipif(
    not (RAW_DIR / "train.csv").exists(),
    reason="raw dataset not present (gitignored; run data/download_dataset.py)",
)
def test_anchor_spans_in_bounds(rubric: Rubric) -> None:
    """Every anchor span must slice real text in the pinned CSVs (0-based iloc rows,
    char offsets into the raw string — same convention as data/corpus.py)."""
    rows: dict[tuple[str, int], dict[str, str]] = {}
    for dim in rubric.dimensions:
        for anchor in dim.get("anchors", []):
            key = (anchor["pair"]["split"], anchor["pair"]["row"])
            if key not in rows:
                rows[key] = load_row(*key)
            for span in anchor["evidence_spans"]:
                text = rows[key][DOC_COLUMNS[span["doc"]]]
                assert span["end"] <= len(text), (
                    f"{dim['id']}: span {span} out of bounds for {key} "
                    f"({span['doc']} has {len(text)} chars)"
                )
