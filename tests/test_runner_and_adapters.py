from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from agent_eval_workbench.adapters import adapt_openai_agents_trace
from agent_eval_workbench.bundle import load_bundle
from agent_eval_workbench.runner import run_scenarios, write_bundle
from agent_eval_workbench.scorecard import score_bundle

ROOT = Path(__file__).resolve().parents[1]


def test_controlled_scenario_runs_end_to_end(tmp_path: Path):
    bundle = run_scenarios(ROOT / "examples" / "scenarios" / "benchmark.yaml")
    output = tmp_path / "run.json"
    write_bundle(bundle, output)
    runs = load_bundle(output)
    card = score_bundle(runs)
    assert card.n_tasks == 24
    assert card.failure_rates["repeated_step_loop"] > 0
    assert card.failure_rates["unsupported_citation"] > 0
    assert any(group.n >= 5 for group in card.fairness.groups)


def test_openai_agents_adapter_extracts_tool_evidence():
    trace = {
        "spans": [
            {
                "span_data": {
                    "type": "function",
                    "name": "lookup_policy",
                    "input": {"topic": "refund"},
                    "output": "30 days",
                }
            },
            {"span_data": {"type": "generation", "output": "Refunds close after 30 days."}},
        ]
    }
    events = adapt_openai_agents_trace(trace)
    assert events[0]["type"] == "tool_call"
    assert events[0]["name"] == "lookup_policy"
    assert events[-1]["type"] == "message"


def test_versioned_bundle_rejects_unknown_schema(tmp_path: Path):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({"schema_version": "2.0", "tasks": []}), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_bundle(path)
