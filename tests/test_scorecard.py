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
    assert card.failure_rates["unsupported_citation"] > 0
    assert card.failure_rates["repeated_step_loop"] > 0
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
        "schema_version": "1.0",
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
    assert card.fairness.disparity_ratio == 0.0
    assert len(card.fairness.warnings) == 2


def _write_bundle(tmp_path: Path, tasks: list[dict]) -> Path:
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps({"schema_version": "1.0", "tasks": tasks}), encoding="utf-8")
    return path


def test_claimed_success_with_empty_or_wrong_answer_is_not_a_success(tmp_path: Path):
    path = _write_bundle(
        tmp_path,
        [
            {
                "task_id": "refund",
                "expected_tools": [],
                "forbidden_tools": [],
                "expected_contains": ["refund approved"],
                "trials": [
                    {"tools_called": [], "final_answer": "", "success": True},
                    {"tools_called": [], "final_answer": "I cannot help", "success": True},
                ],
            }
        ],
    )
    card = score_bundle(load_bundle(path))
    assert card.task_success_rate == 0.0
    assert card.composite == 0.0


def test_without_expected_contains_the_score_trusts_the_success_flag(tmp_path: Path):
    """Limit by design: with no expected answer the run's own success flag is trusted."""
    path = _write_bundle(
        tmp_path,
        [
            {
                "task_id": "no-check",
                "expected_tools": [],
                "forbidden_tools": [],
                "trials": [{"tools_called": [], "final_answer": "anything", "success": True}],
            }
        ],
    )
    card = score_bundle(load_bundle(path))
    assert card.task_success_rate == 1.0
    assert card.composite == 1.0


def test_agent_that_fails_every_task_scores_composite_zero(tmp_path: Path):
    tasks = [
        {
            "task_id": f"t{index}",
            "expected_tools": [],
            "forbidden_tools": [],
            "trials": [{"tools_called": [], "final_answer": "wrong", "success": False}],
        }
        for index in range(3)
    ]
    card = score_bundle(load_bundle(_write_bundle(tmp_path, tasks)))
    assert card.task_success_rate == 0.0
    assert card.reliability == 1.0
    assert card.composite == 0.0


def test_forbidden_tool_in_tools_called_is_flagged_when_events_disagree(tmp_path: Path):
    path = _write_bundle(
        tmp_path,
        [
            {
                "task_id": "disagree",
                "expected_tools": [],
                "forbidden_tools": ["delete_account"],
                "trials": [
                    {
                        "tools_called": ["delete_account"],
                        "events": [{"type": "tool_call", "name": "lookup_policy"}],
                        "final_answer": "ok",
                        "success": True,
                    }
                ],
            }
        ],
    )
    runs = load_bundle(path)
    modes = {hit.mode for hit in detect_failures(runs[0], runs[0].trials[0])}
    assert "forbidden_tool" in modes
    assert score_bundle(runs).composite == 0.0


def test_citation_host_with_backslash_is_not_allowlisted(tmp_path: Path):
    answers = [
        "see http://evil.com\\.docs.example.com/x",
        "see http://docs.example.com\\@evil.com/x",
        "see http://docs.example.com@evil.com/x",
    ]
    tasks = [
        {
            "task_id": f"cite{index}",
            "expected_tools": [],
            "forbidden_tools": [],
            "allowed_citations": ["docs.example.com"],
            "trials": [{"tools_called": [], "final_answer": answer, "success": True}],
        }
        for index, answer in enumerate(answers)
    ]
    for run in load_bundle(_write_bundle(tmp_path, tasks)):
        modes = {hit.mode for hit in detect_failures(run, run.trials[0])}
        assert "unsupported_citation" in modes, run.trials[0].final_answer


def test_allowlisted_citation_host_still_passes(tmp_path: Path):
    tasks = [
        {
            "task_id": "cite-ok",
            "expected_tools": [],
            "forbidden_tools": [],
            "allowed_citations": ["docs.example.com"],
            "trials": [
                {
                    "tools_called": [],
                    "final_answer": "see https://api.docs.example.com/x and http://docs.example.com/y",
                    "success": True,
                }
            ],
        }
    ]
    run = load_bundle(_write_bundle(tmp_path, tasks))[0]
    assert "unsupported_citation" not in {h.mode for h in detect_failures(run, run.trials[0])}


def test_one_trial_groups_still_set_the_gap(tmp_path: Path):
    """Limit by design: groups under five trials still count in the gap (fails closed)."""
    tasks = [
        {
            "task_id": tag,
            "expected_tools": [],
            "forbidden_tools": [],
            "demographic_tag": tag,
            "trials": [{"tools_called": [], "final_answer": "x", "success": tag == "a"}],
        }
        for tag in ("a", "b")
    ]
    card = score_bundle(load_bundle(_write_bundle(tmp_path, tasks)))
    assert card.bias_gap == 1.0
    assert card.composite == 0.0
