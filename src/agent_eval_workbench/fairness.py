"""Descriptive fairness diagnostics with uncertainty and sample warnings."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

from agent_eval_workbench.bundle import TaskRun

MIN_COMPARISON_GROUPS = 2


@dataclass(frozen=True)
class GroupEstimate:
    group: str
    n: int
    successes: int
    rate: float
    ci_low: float
    ci_high: float
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class FairnessReport:
    groups: tuple[GroupEstimate, ...]
    absolute_gap: float
    disparity_ratio: float | None
    warnings: tuple[str, ...]
    interpretation: str = (
        "Descriptive association only. Group labels and outcomes do not establish causality."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    rate = successes / n
    denominator = 1 + z * z / n
    centre = (rate + z * z / (2 * n)) / denominator
    margin = z * math.sqrt(rate * (1 - rate) / n + z * z / (4 * n * n)) / denominator
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def analyze_fairness(runs: list[TaskRun], min_group_n: int = 5) -> FairnessReport:
    by_group: dict[str, list[bool]] = {}
    for run in runs:
        if run.demographic_tag is not None:
            by_group.setdefault(str(run.demographic_tag), []).extend(
                trial.success for trial in run.trials
            )
    estimates = []
    global_warnings: list[str] = []
    for group, outcomes in sorted(by_group.items()):
        successes = sum(outcomes)
        n = len(outcomes)
        low, high = _wilson(successes, n)
        warnings = ()
        if n < min_group_n:
            warnings = (f"insufficient sample: n={n} < {min_group_n}",)
            global_warnings.append(f"{group}: {warnings[0]}")
        estimates.append(
            GroupEstimate(group, n, successes, successes / n, low, high, warnings)
        )
    rates = [estimate.rate for estimate in estimates]
    gap = max(rates) - min(rates) if len(rates) > 1 else 0.0
    ratio = None
    if len(rates) > 1:
        ratio = min(rates) / max(rates) if max(rates) > 0 else None
    if len(estimates) < MIN_COMPARISON_GROUPS:
        global_warnings.append("fewer than two groups; disparity is not estimable")
    return FairnessReport(tuple(estimates), gap, ratio, tuple(global_warnings))
