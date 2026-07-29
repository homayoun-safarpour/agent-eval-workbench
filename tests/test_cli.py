from __future__ import annotations

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
