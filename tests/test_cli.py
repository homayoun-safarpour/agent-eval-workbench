from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cli_score_good_passes_floor():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_eval_workbench.cli",
            "score",
            str(ROOT / "examples" / "bundle_good.json"),
            "--min-composite",
            "0.9",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "composite=1.0000" in proc.stdout


def test_cli_score_mixed_fails_floor():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_eval_workbench.cli",
            "score",
            str(ROOT / "examples" / "bundle_mixed.json"),
            "--min-composite",
            "0.95",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2


def test_cli_failed_floor_prints_group_wilson_rows():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_eval_workbench.cli",
            "score",
            str(ROOT / "examples" / "forbidden_plus_missing_OUTPUT.json"),
            "--min-composite",
            "0.99",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert "verdict: FAIL" in proc.stderr
    for group in ("group_a", "group_b"):
        assert f"group:{group} n=1 rate=1.0000" in proc.stdout
    assert "wilson95=[0.2065, 1.0000]" in proc.stdout
    assert "group_gap=0.0000" in proc.stdout
    assert "insufficient sample" in proc.stdout


def test_cli_failed_floor_json_remains_parseable():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_eval_workbench.cli",
            "score",
            str(ROOT / "examples" / "forbidden_plus_missing_OUTPUT.json"),
            "--min-composite",
            "0.99",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    assert len(json.loads(proc.stdout)["fairness"]["groups"]) == 2


def test_cli_run_scenario_exports_trace_and_json(tmp_path: Path):
    output = tmp_path / "run.json"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_eval_workbench.cli",
            "run",
            str(ROOT / "examples" / "scenarios" / "benchmark.yaml"),
            "--output",
            str(output),
            "--json",
            "--min-composite",
            "0.1",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["n_tasks"] == 24
    assert json.loads(output.read_text(encoding="utf-8"))["schema_version"] == "1.0"
