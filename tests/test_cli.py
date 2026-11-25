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


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agent_eval_workbench.cli", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_non_finite_or_out_of_range_floor_is_refused():
    bundle = str(ROOT / "examples" / "forbidden_plus_missing_OUTPUT.json")
    for floor in ("nan", "inf", "-inf", "1.5", "-0.1", "abc"):
        proc = _cli("score", bundle, "--min-composite", floor)
        assert proc.returncode == 1, (floor, proc.returncode, proc.stderr)
        assert "--min-composite" in proc.stderr
        assert len(proc.stderr.strip().splitlines()) == 1
        assert "verdict" not in proc.stdout + proc.stderr


def test_nan_floor_is_refused_on_run_before_running(tmp_path: Path):
    output = tmp_path / "unused.json"
    proc = _cli(
        "run",
        str(ROOT / "examples" / "scenarios" / "benchmark.yaml"),
        "--output",
        str(output),
        "--min-composite",
        "nan",
    )
    assert proc.returncode == 1
    assert not output.exists()


def test_argument_error_exits_1_not_the_fail_code():
    proc = _cli("score")
    assert proc.returncode == 1
    assert "error" in proc.stderr
    assert len(proc.stderr.strip().splitlines()) == 1
    assert _cli("score", "x.json", "--no-such-flag").returncode == 1
