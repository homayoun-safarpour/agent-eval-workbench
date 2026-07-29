"""Named failure-mode detectors for agent trajectories."""

from __future__ import annotations

from dataclasses import dataclass

from agent_eval_workbench.bundle import TaskRun, Trial


@dataclass(frozen=True)
class FailureHit:
    mode: str
    detail: str


def detect_failures(run: TaskRun, trial: Trial) -> list[FailureHit]:
    hits: list[FailureHit] = []
    if not trial.success:
        hits.append(FailureHit("task_fail", "trial marked success=false"))
    expected = set(run.expected_tools)
    called = set(trial.tools_called)
    missing = expected - called
    if missing:
        hits.append(FailureHit("missing_tool", f"missing expected tools: {sorted(missing)}"))
    forbidden = set(run.forbidden_tools) & called
    if forbidden:
        hits.append(FailureHit("forbidden_tool", f"called forbidden: {sorted(forbidden)}"))
    # Order: expected tools should appear in the same relative order when present
    if run.expected_tools:
        positions = []
        ok = True
        for tool in run.expected_tools:
            if tool not in trial.tools_called:
                ok = False
                break
            positions.append(trial.tools_called.index(tool))
        if ok and positions != sorted(positions):
            hits.append(FailureHit("tool_order", "expected tools out of order"))
    if trial.metadata.get("hallucinated_citation"):
        hits.append(FailureHit("hallucinated_citation", "metadata flag set"))
    if trial.metadata.get("loop_detected"):
        hits.append(FailureHit("infinite_loop", "metadata flag set"))
    return hits


FAILURE_MODES = (
    "task_fail",
    "missing_tool",
    "forbidden_tool",
    "tool_order",
    "hallucinated_citation",
    "infinite_loop",
)
