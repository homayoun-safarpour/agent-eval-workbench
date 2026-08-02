"""Multi-axis scorecard: success, reliability, bias gap, failure rates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from agent_eval_workbench.bundle import TaskRun
from agent_eval_workbench.failures import FAILURE_MODES, detect_failures
from agent_eval_workbench.fairness import FairnessReport, analyze_fairness


@dataclass(frozen=True)
class Scorecard:
    n_tasks: int
    n_trials: int
    task_success_rate: float
    reliability: float
    bias_gap: float
    fairness: FairnessReport
    failure_rates: dict[str, float]
    composite: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _trial_success_consistent(run: TaskRun) -> float:
    """1.0 if all trials agree on success; else fraction of majority agreement."""
    if not run.trials:
        return 0.0
    flags = [t.success for t in run.trials]
    majority = sum(flags) >= (len(flags) / 2)
    return sum(1 for f in flags if f == majority) / len(flags)


def score_bundle(runs: list[TaskRun]) -> Scorecard:
    n_trials = sum(len(r.trials) for r in runs) or 1
    successes = sum(1 for r in runs for t in r.trials if t.success)
    task_success_rate = successes / n_trials

    reliabilities = [_trial_success_consistent(r) for r in runs if r.trials]
    reliability = sum(reliabilities) / len(reliabilities) if reliabilities else 0.0

    fairness = analyze_fairness(runs)
    bias_gap = fairness.absolute_gap

    fail_counts = {m: 0 for m in FAILURE_MODES}
    for r in runs:
        for t in r.trials:
            for hit in detect_failures(r, t):
                fail_counts[hit.mode] = fail_counts.get(hit.mode, 0) + 1
        signatures = {
            (
                trial.success,
                tuple(trial.tools_called),
            )
            for trial in r.trials
        }
        if len(signatures) > 1:
            fail_counts["non_reproducible"] += len(r.trials)
    failure_rates = {m: fail_counts[m] / n_trials for m in FAILURE_MODES}

    # Composite: reward success + reliability, penalize bias gap and forbidden/missing tools
    penalty = (
        bias_gap
        + failure_rates.get("forbidden_tool", 0.0)
        + 0.5 * failure_rates.get("missing_tool", 0.0)
    )
    composite = max(0.0, min(1.0, 0.5 * task_success_rate + 0.5 * reliability - penalty))

    return Scorecard(
        n_tasks=len(runs),
        n_trials=n_trials,
        task_success_rate=task_success_rate,
        reliability=reliability,
        bias_gap=bias_gap,
        fairness=fairness,
        failure_rates=failure_rates,
        composite=composite,
    )
