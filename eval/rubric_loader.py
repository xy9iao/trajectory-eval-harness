"""Load rubric YAML and expose the pieces the schema contract is stated over.

The loader is deliberately thin: it parses, types the top-level shape, and
answers the two questions every consumer (schema test now; get_rubric and the
P2 scorers later) must not re-derive — which dimensions score into the
weighted mean, and which dimension drives the soft veto. Scoring semantics
stay in the YAML; validation lives in tests/test_rubric_schema.py.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Rubric:
    version: str
    status: str
    scale: dict[str, Any]
    aggregation: dict[str, Any]
    dimensions: list[dict[str, Any]]

    @property
    def veto_dimension_id(self) -> str:
        trigger: str = self.aggregation["soft_veto"]["trigger_dimension"]
        return trigger

    @property
    def scoring_dimensions(self) -> list[dict[str, Any]]:
        """Dimensions that enter the weighted mean — the veto dimension never does."""
        return [d for d in self.dimensions if d["id"] != self.veto_dimension_id]


def load_rubric(path: Path) -> Rubric:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} did not parse to a mapping")
    return Rubric(
        version=raw["version"],
        status=raw["status"],
        scale=raw["scale"],
        aggregation=raw["aggregation"],
        dimensions=raw["dimensions"],
    )
