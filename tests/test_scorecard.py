from __future__ import annotations

import json
from pathlib import Path

from agent_eval_workbench.bundle import load_bundle
from agent_eval_workbench.failures import detect_failures
from agent_eval_workbench.scorecard import score_bundle

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "examples"


def test_good_bundle_high_composite():
    runs = load_bundle(EX / "bundle_good.json")
    card = score_bundle(runs)
    assert card.task_success_rate == 1.0
    assert card.reliability == 1.0
    assert card.bias_gap == 0.0
    assert card.composite == 1.0
    assert card.failure_rates["forbidden_tool"] == 0.0


def test_mixed_bundle_flags_failure_modes():
    runs = load_bundle(EX / "bundle_mixed.json")
    card = score_bundle(runs)
    assert card.task_success_rate < 1.0
    assert card.failure_rates["forbidden_tool"] > 0
    assert card.failure_rates["hallucinated_citation"] > 0
    assert card.failure_rates["infinite_loop"] > 0
    assert card.composite < 0.9


def test_detect_missing_and_forbidden_tools():
    runs = load_bundle(EX / "bundle_mixed.json")
    bad = runs[-1]
    hits = detect_failures(bad, bad.trials[0])
    modes = {h.mode for h in hits}
    assert "forbidden_tool" in modes
    assert "missing_tool" in modes


def test_bias_gap_when_groups_diverge(tmp_path: Path):
    data = {
        "tasks": [
            {
                "task_id": "a1",
                "expected_tools": [],
                "forbidden_tools": [],
                "demographic_tag": "group_a",
                "trials": [{"tools_called": [], "final_answer": "ok", "success": True}],
            },
            {
                "task_id": "b1",
                "expected_tools": [],
                "forbidden_tools": [],
                "demographic_tag": "group_b",
                "trials": [{"tools_called": [], "final_answer": "no", "success": False}],
            },
        ]
    }
    path = tmp_path / "bias.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    card = score_bundle(load_bundle(path))
    assert card.bias_gap == 1.0
