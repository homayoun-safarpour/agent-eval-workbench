"""Load agent run bundles (task + optional repeated trials)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Trial:
    tools_called: list[str]
    final_answer: str
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskRun:
    task_id: str
    expected_tools: list[str]
    forbidden_tools: list[str]
    demographic_tag: str | None
    trials: list[Trial]


def load_bundle(path: str | Path) -> list[TaskRun]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    runs: list[TaskRun] = []
    for item in data["tasks"]:
        trials = [
            Trial(
                tools_called=list(t.get("tools_called", [])),
                final_answer=str(t.get("final_answer", "")),
                success=bool(t.get("success", False)),
                metadata=dict(t.get("metadata", {})),
            )
            for t in item.get("trials", [])
        ]
        runs.append(
            TaskRun(
                task_id=str(item["task_id"]),
                expected_tools=list(item.get("expected_tools", [])),
                forbidden_tools=list(item.get("forbidden_tools", [])),
                demographic_tag=item.get("demographic_tag"),
                trials=trials,
            )
        )
    return runs
