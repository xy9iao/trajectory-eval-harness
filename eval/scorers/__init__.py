"""Scorer framework (P2 eval-design decision 2).

Uniform signature — every scorer is `(corpus, reference) -> ScorerResult`;
the runner is a dumb pipe (`for scorer in REGISTRY: scorer(corpus, ref)`)
and all intelligence lives in single-testable pure functions. Arity
(per-run / per-pair-group / per-corpus) lives INSIDE each scorer via the
Corpus accessors.

Exclusion contract (decision 2a): `Corpus.load` validates every trajectory
first; any case that fails `validate_trajectory` is excluded from all
scorers and recorded in `Corpus.excluded` — a scorer never sees an illegal
trajectory, and the exclusion is visible (surfaced in the report header),
not silent.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from eval.trajectory import load_trajectory, validate_trajectory

Reference = dict[tuple[str, int], dict[str, Any]]  # (split, row) -> reference label record
PairKey = tuple[str, int]


@dataclass(frozen=True)
class Case:
    """One validated run trajectory, with typed accessors over its events."""

    run_id: str
    events: list[dict[str, Any]]

    @property
    def _start(self) -> dict[str, Any]:
        return self.events[0]

    @property
    def _end(self) -> dict[str, Any]:
        return self.events[-1]

    @property
    def pair(self) -> PairKey:
        p = self._start["pair"]
        return (p["split"], p["row"])

    @property
    def provider(self) -> str:
        return str(self._start.get("provider"))

    @property
    def model(self) -> str:
        return str(self._start.get("model"))

    @property
    def config_digest(self) -> str:
        return str(self._start.get("config_digest"))

    def dimension_scores(self) -> dict[str, int | None]:
        return {
            e["dimension"]: (None if e.get("degraded") else e.get("score"))
            for e in self.events
            if e.get("type") == "dimension_assessed"
        }

    @property
    def gate_fired(self) -> bool:
        return bool(self._end.get("gate_fired"))

    @property
    def recommendation(self) -> str | None:
        rec = self._end.get("recommendation")
        return str(rec) if rec is not None else None

    @property
    def aggregate(self) -> dict[str, Any]:
        agg: dict[str, Any] = self._end.get("aggregate") or {}
        return agg


@dataclass
class Corpus:
    """Validated run trajectories, grouped-by-pair on demand."""

    cases: list[Case]
    excluded: list[tuple[str, str]] = field(default_factory=list)  # (run_id, reason)

    @classmethod
    def load(
        cls,
        runs_dir: Path,
        provider: str | None = None,
        stub_ok: bool = False,
        run_ids: set[str] | None = None,
    ) -> "Corpus":
        """Load validated trajectories. `run_ids` scopes to a specific set
        (e.g. one pass^k batch's manifest) so a scorer never mixes a batch
        with unrelated historical runs sharing the same pair."""
        cases: list[Case] = []
        excluded: list[tuple[str, str]] = []
        for path in sorted(runs_dir.glob("*/trajectory.jsonl")):
            events = load_trajectory(path)
            if not events or events[0].get("type") != "run_start":
                continue
            run_id = str(events[0].get("run_id"))
            if run_ids is not None and run_id not in run_ids:
                continue
            run_provider = events[0].get("provider")
            if not stub_ok and run_provider == "stub":
                continue
            if provider is not None and run_provider != provider:
                continue
            problems = validate_trajectory(events)
            if problems:
                excluded.append((run_id, f"{len(problems)} validation failure(s)"))
                continue
            cases.append(Case(run_id=run_id, events=events))
        return cls(cases=cases, excluded=excluded)

    @classmethod
    def from_manifest(cls, runs_dir: Path, manifest_path: Path) -> "Corpus":
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return cls.load(runs_dir, run_ids=set(manifest["run_ids"]))

    def by_pair(self) -> dict[PairKey, list[Case]]:
        groups: dict[PairKey, list[Case]] = {}
        for c in self.cases:
            groups.setdefault(c.pair, []).append(c)
        return groups


@dataclass
class ScorerResult:
    """A scorer's output: named metrics + optional per-row detail + notes.
    Figures are declared as (filename, kind) specs the report step renders —
    scorers stay pure (no I/O)."""

    name: str
    metrics: dict[str, Any]
    rows: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""


Scorer = Callable[[Corpus, Reference], ScorerResult]


def load_reference(path: Path) -> Reference:
    return {
        (r["pair"]["split"], r["pair"]["row"]): r
        for r in (json.loads(x) for x in path.read_text(encoding="utf-8").splitlines())
    }
