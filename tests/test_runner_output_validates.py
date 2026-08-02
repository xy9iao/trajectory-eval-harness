"""Every runner must emit trajectories its own validator accepts.

This test exists because the variant runner did not. It emitted a
`variant_tag` event to carry the variant's identity — an 8th event type
against a schema frozen before P2, written AFTER `run_end`, which must be the
final event. All 11 trajectories in the first live variant batch were invalid,
and nothing noticed until the report runner tried to score them and found zero
valid cases.

The bug was invisible because the batch's own console output looked perfect:
gate triggers, means and recommendations all printed fine. Validity is a
property of the recorded artifact, not of the run that produced it, and only
something that re-reads the file can tell the difference.

Variant identity now lives in the manifest, where the batch is already scoped
and its kind already declared — the trajectory never needed it.
"""

from pathlib import Path

import pytest

from eval.trajectory import load_trajectory, validate_trajectory


def _corpus_available() -> bool:
    return (Path(__file__).resolve().parents[1] / "data" / "raw" / "train.csv").exists()


needs_corpus = pytest.mark.skipif(
    not _corpus_available(), reason="raw dataset not present (gitignored)"
)


@needs_corpus
def test_variant_runner_emits_valid_trajectories(tmp_path: Path) -> None:
    from agent.run import run_variants

    # stub mode: no API calls, but the same writer and the same event sequence
    # the live path produces.
    rc = run_variants(tmp_path, "stub", "stub", None, None, live=False, only=["gn-01", "fs-01"])
    assert rc == 0

    written = sorted(tmp_path.glob("*/trajectory.jsonl"))
    assert len(written) == 2, "the runner should have written one trajectory per variant"
    for path in written:
        problems = validate_trajectory(load_trajectory(path))
        assert not problems, f"{path.parent.name} is not schema-valid: {problems}"


@needs_corpus
def test_variant_identity_lives_in_the_manifest_not_the_trajectory(tmp_path: Path) -> None:
    import json

    from agent.run import run_variants

    run_variants(tmp_path, "stub", "stub", None, None, live=False, only=["gn-01"])
    manifest = json.loads(next(tmp_path.glob("variants-*.json")).read_text(encoding="utf-8"))

    assert manifest["kind"] == "variants"
    assert set(manifest["variant_ids"].values()) == {"gn-01"}
    assert set(manifest["variant_ids"]) == set(manifest["run_ids"])

    events = load_trajectory(next(tmp_path.glob("*/trajectory.jsonl")))
    assert events[-1]["type"] == "run_end", "run_end must remain the final event"
    assert not any(e["type"] == "variant_tag" for e in events)
