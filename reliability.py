"""Reliability: pass@k vs pass^k (GUIDE §6.3) — the headline insight.

Operational definitions (empirical, no i.i.d. assumption):
  For each case run k times with c successes:
    * counts toward pass@k  if c >= 1   (at least one success)
    * counts toward pass^k  if c == k   (all successes)
  Dataset pass@k / pass^k = mean over cases.
  reliability_gap = pass@k - pass^k.

pass@k rises with k (capability/best-case); pass^k falls with k (reliability).
Production reliability lives on pass^k. This module is pure Python and self-tests below.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReliabilityResult:
    k: int
    pass_at_k: float
    pass_caret_k: float

    @property
    def reliability_gap(self) -> float:
        return self.pass_at_k - self.pass_caret_k


def reliability(successes_per_case: list[list[bool]], k: int | None = None) -> ReliabilityResult:
    """successes_per_case: for each case, a list of per-run success booleans (length k).

    Pass k to truncate/validate to a fixed run count; defaults to the min length seen.
    """
    if not successes_per_case:
        raise ValueError("no cases")
    run_count = k or min(len(runs) for runs in successes_per_case)
    if run_count < 1:
        raise ValueError("need >= 1 run per case")

    at_k_hits = 0
    caret_k_hits = 0
    for runs in successes_per_case:
        r = runs[:run_count]
        c = sum(r)
        at_k_hits += 1 if c >= 1 else 0
        caret_k_hits += 1 if c == run_count else 0

    n = len(successes_per_case)
    return ReliabilityResult(
        k=run_count,
        pass_at_k=at_k_hits / n,
        pass_caret_k=caret_k_hits / n,
    )


def reliability_curve(successes_per_case: list[list[bool]], ks: list[int]) -> list[ReliabilityResult]:
    """pass@k / pass^k across several k values — the table you put in the report."""
    return [reliability(successes_per_case, k=k) for k in ks]


# --------------------------------------------------------------------------------------
# Self-test: runs with no dependencies. `python -m src.eval.reliability`
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    # 5 cases, 5 runs each. Per-run success rate ~0.9 but spread out so the gap shows.
    demo = [
        [True, True, True, True, True],    # rock solid
        [True, True, True, True, False],   # one flake
        [True, False, True, True, True],   # one flake
        [True, True, True, True, True],    # rock solid
        [False, True, True, True, True],   # one flake
    ]
    print("k  pass@k  pass^k  gap")
    for res in reliability_curve(demo, ks=[1, 3, 5]):
        print(f"{res.k}  {res.pass_at_k:.2f}    {res.pass_caret_k:.2f}    {res.reliability_gap:.2f}")
    # Expect: pass@k stays high (~1.0), pass^k drops as k grows (3 of 5 cases flake somewhere),
    # so the reliability gap widens with k — the whole point.
