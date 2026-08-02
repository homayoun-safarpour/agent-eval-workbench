"""Run the pinned synthetic trace benchmark and write measured output."""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

from agent_eval_workbench.bundle import load_bundle
from agent_eval_workbench.failures import detect_failures
from agent_eval_workbench.runner import load_scenarios, run_scenarios, write_bundle
from agent_eval_workbench.scorecard import score_bundle

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["mock", "openai"], default="mock")
    parser.add_argument("--model", default="gpt-4.1-mini")
    parser.add_argument("--output", default="examples/benchmark_results.json")
    parser.add_argument("--bundle-output", default="examples/benchmark_bundle.json")
    args = parser.parse_args()

    source = ROOT / "examples" / "scenarios" / "benchmark.yaml"
    start = time.perf_counter()
    bundle = run_scenarios(source, backend=args.backend, model=args.model)
    elapsed_ms = (time.perf_counter() - start) * 1000
    bundle_path = ROOT / args.bundle_output
    write_bundle(bundle, bundle_path)
    runs = load_bundle(bundle_path)
    card = score_bundle(runs)
    scenarios = load_scenarios(source)["scenarios"]

    true_positive = false_positive = false_negative = 0
    errors = []
    for scenario, run in zip(scenarios, runs, strict=True):
        expected = set(scenario.get("expected_failures", []))
        detected = {hit.mode for hit in detect_failures(run, run.trials[0])}
        true_positive += len(expected & detected)
        false_positive += len(detected - expected)
        false_negative += len(expected - detected)
        if expected != detected:
            errors.append(
                {
                    "scenario": scenario["id"],
                    "expected": sorted(expected),
                    "detected": sorted(detected),
                }
            )
    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 1.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else 1.0
    )
    costs = [
        trial.metadata.get("cost_usd")
        for run in runs
        for trial in run.trials
        if trial.metadata.get("cost_usd") is not None
    ]
    report = {
        "benchmark": {
            "name": "controlled-trace-failures",
            "version": "1.0",
            "scenario_count": len(scenarios),
            "failure_labels": 18,
            "backend": args.backend,
            "model": args.model if args.backend == "openai" else None,
            "python": platform.python_version(),
        },
        "detector_metrics": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "precision": precision,
            "recall": recall,
            "errors": errors,
        },
        "runtime": {
            "elapsed_ms": round(elapsed_ms, 3),
            "mean_scenario_ms": round(elapsed_ms / len(scenarios), 3),
            "recorded_cost_usd": sum(costs),
        },
        "scorecard": card.to_dict(),
        "limitations": [
            "Synthetic scenarios test detector behavior, not open-world agent quality.",
            "Fairness outputs are descriptive and non-causal.",
            "Mock timing is local execution overhead, not API latency.",
            "No trajectory anomaly model is claimed; deterministic rules achieved full labels.",
        ],
    }
    output = ROOT / args.output
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["detector_metrics"], indent=2))
    print(f"output={output} bundle={bundle_path}")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
