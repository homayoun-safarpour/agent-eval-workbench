"""Load agent run bundles (task + optional repeated trials)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent_eval_workbench.schema import validate_document


@dataclass
class Trial:
    tools_called: list[str]
    final_answer: str
    success: bool
    events: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskRun:
    task_id: str
    expected_tools: list[str]
    forbidden_tools: list[str]
    expected_tool_order: list[str]
    expected_contains: list[str]
    allowed_citations: list[str]
    demographic_tag: str | None
    trials: list[Trial]


def load_bundle(path: str | Path) -> list[TaskRun]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_document(data, "bundle")
    runs: list[TaskRun] = []
    for item in data["tasks"]:
        trials = [
            Trial(
                tools_called=list(t.get("tools_called", [])),
                final_answer=str(t.get("final_answer", "")),
                success=bool(t.get("success", False)),
                events=list(t.get("events", [])),
                metadata=dict(t.get("metadata", {})),
            )
            for t in item.get("trials", [])
        ]
        runs.append(
            TaskRun(
                task_id=str(item["task_id"]),
                expected_tools=list(item.get("expected_tools", [])),
                forbidden_tools=list(item.get("forbidden_tools", [])),
                expected_tool_order=list(
                    item.get("expected_tool_order", item.get("expected_tools", []))
                ),
                expected_contains=list(item.get("expected_contains", [])),
                allowed_citations=list(item.get("allowed_citations", [])),
                demographic_tag=item.get("demographic_tag"),
                trials=trials,
            )
        )
    return runs
