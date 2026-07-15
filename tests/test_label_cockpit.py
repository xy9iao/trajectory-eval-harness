"""The cockpit's derived values ARE rubric rules (band geometry, ledger,
veto, weighted mean) — if they drift from rubric-v1.yaml, labels silently
stop following the rubric, so CI pins them here."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))

from label_pairs import (  # noqa: E402
    band_from_determinations,
    hard_requirements_score,
    veto_state,
    weighted_mean,
)

H, K, A = "hands-on", "keyword", "adjacent"


def test_band_geometry_matches_rubric() -> None:
    assert band_from_determinations([]) is None  # no skills items: undefined, manual
    assert band_from_determinations([("absent", "none")] * 2) == 0  # broadly absent
    assert band_from_determinations([("covered", H), ("absent", "none")]) == 1  # any absent
    assert band_from_determinations([("covered", H), ("partial", K)]) == 2  # any partial
    assert band_from_determinations([("covered", K), ("covered", K)]) == 3  # keyword-dominant
    assert band_from_determinations([("covered", A)]) == 3  # adjacency caps at mid-band
    assert band_from_determinations([("covered", H), ("covered", H), ("covered", K)]) == 4
    assert band_from_determinations([("covered", H), ("covered", H)]) == 5


def test_hard_requirements_ledger() -> None:
    assert hard_requirements_score([]) == 5  # nothing required, nothing unmet
    assert hard_requirements_score(["met", "met"]) == 5
    assert hard_requirements_score(["met", "indeterminate"]) == 3
    assert hard_requirements_score(["indeterminate", "unmet"]) == 0  # unmet dominates
    assert hard_requirements_score(["met", "met", "unmet"]) == 0  # 4-of-5 still 0


def test_veto_state_wiring() -> None:
    assert veto_state(0) == "unmet"
    assert veto_state(3) == "indeterminate"
    assert veto_state(5) == "met"


def test_weighted_mean_uses_rubric_weights() -> None:
    weights = {"skills_coverage": 0.5, "experience_level": 0.3, "education_domain_fit": 0.2}
    scores = {"skills_coverage": 1, "experience_level": 3, "education_domain_fit": 3}
    assert weighted_mean(scores, weights) == pytest.approx(2.0)
