"""Append-only trajectory writer (schema v0.2; D11).

Logger-side by design (decision 2): events are written as they happen, so a
crashed run keeps its trajectory up to the crash. The writer owns the
envelope (run_id, seq, ts) and nothing else — payload hygiene (invariant 7)
is the caller's contract, asserted by the e2e test with
validate_data_hygiene.
"""

import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def new_run_id(now: datetime | None = None) -> str:
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%S")
    return f"r{stamp}-{secrets.token_hex(3)}"


class TrajectoryWriter:
    def __init__(self, runs_dir: Path, run_id: str | None = None) -> None:
        self.run_id = run_id or new_run_id()
        self.path = runs_dir / self.run_id / "trajectory.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seq = 0

    def emit(self, type_: str, **fields: Any) -> None:
        event = {
            "run_id": self.run_id,
            "seq": self._seq,
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "type": type_,
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        self._seq += 1
