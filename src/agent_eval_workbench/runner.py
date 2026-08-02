"""Controlled scenario runner with deterministic and opt-in API backends."""

from __future__ import annotations

import json
import os
from importlib import import_module
from pathlib import Path
from typing import Any

import yaml

from agent_eval_workbench.schema import SCHEMA_VERSION, validate_document


def load_scenarios(path: str | Path) -> dict[str, Any]:
    document = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("scenario file must contain a mapping")
    validate_document(document, "scenario")
    return document


def _mock_trial(scenario: dict[str, Any], trial_index: int) -> dict[str, Any]:
    mock = dict(scenario.get("mock", {}))
    answer = str(mock.get("final_answer", ""))
    events = [dict(event) for event in mock.get("events", [])]
    tools = [
        str(event["name"])
        for event in events
        if event.get("type") == "tool_call" and event.get("name")
    ]
    expected = [str(item).lower() for item in scenario.get("expected_contains", [])]
    success = bool(answer.strip()) and all(item in answer.lower() for item in expected)
    return {
        "tools_called": tools,
        "events": events,
        "final_answer": answer,
        "success": success,
        "metadata": {"backend": "mock", "trial_index": trial_index, "cost_usd": 0.0},
    }


def _openai_trial(
    scenario: dict[str, Any], trial_index: int, model: str
) -> dict[str, Any]:
    try:
        openai_module = import_module("openai")
    except ImportError as exc:
        raise RuntimeError("install the llm extra: pip install -e '.[llm]'") from exc
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for --backend openai")
    response = openai_module.OpenAI().responses.create(
        model=model, input=str(scenario["prompt"])
    )
    answer = str(response.output_text)
    expected = [str(item).lower() for item in scenario.get("expected_contains", [])]
    success = bool(answer.strip()) and all(item in answer.lower() for item in expected)
    usage = getattr(response, "usage", None)
    metadata = {
        "backend": "openai",
        "model": model,
        "trial_index": trial_index,
        "cost_usd": None,
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
    }
    return {
        "tools_called": [],
        "events": [{"type": "message", "content": answer}],
        "final_answer": answer,
        "success": success,
        "metadata": metadata,
    }


def run_scenarios(
    scenario_path: str | Path,
    backend: str = "mock",
    model: str = "gpt-4.1-mini",
) -> dict[str, Any]:
    """Execute all scenarios and return a schema-valid evaluation bundle."""
    document = load_scenarios(scenario_path)
    tasks = []
    for scenario in document["scenarios"]:
        trials = []
        for trial_index in range(int(scenario.get("trials", 1))):
            if backend == "mock":
                trials.append(_mock_trial(scenario, trial_index))
            elif backend == "openai":
                trials.append(_openai_trial(scenario, trial_index, model))
            else:
                raise ValueError(f"unknown backend: {backend}")
        tasks.append(
            {
                "task_id": scenario["id"],
                "expected_tools": list(scenario.get("expected_tools", [])),
                "forbidden_tools": list(scenario.get("forbidden_tools", [])),
                "expected_tool_order": list(
                    scenario.get("expected_tool_order", scenario.get("expected_tools", []))
                ),
                "expected_contains": list(scenario.get("expected_contains", [])),
                "allowed_citations": list(scenario.get("allowed_citations", [])),
                "demographic_tag": scenario.get("demographic_tag"),
                "trials": trials,
            }
        )
    bundle = {"schema_version": SCHEMA_VERSION, "tasks": tasks}
    validate_document(bundle, "bundle")
    return bundle


def write_bundle(bundle: dict[str, Any], path: str | Path) -> None:
    Path(path).write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
