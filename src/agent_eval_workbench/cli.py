"""CLI for agent-eval-workbench."""

from __future__ import annotations

import argparse
import json
import sys

from agent_eval_workbench.adapters import load_trace
from agent_eval_workbench.bundle import load_bundle
from agent_eval_workbench.runner import run_scenarios, write_bundle
from agent_eval_workbench.schema import validate_document
from agent_eval_workbench.scorecard import score_bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-eval",
        description="Score agent run bundles on success, reliability, bias, failure modes.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sc = sub.add_parser("score", help="print multi-axis scorecard")
    sc.add_argument("bundle", help="path to bundle JSON")
    sc.add_argument("--json", action="store_true")
    sc.add_argument(
        "--min-composite",
        type=float,
        default=None,
        help="if set, exit 2 when composite falls below this floor",
    )

    run = sub.add_parser("run", help="execute controlled YAML scenarios and score the traces")
    run.add_argument("scenario", help="path to scenario YAML")
    run.add_argument("--output", required=True, help="write the versioned run bundle here")
    run.add_argument("--backend", choices=["mock", "openai"], default="mock")
    run.add_argument("--model", default="gpt-4.1-mini")
    run.add_argument("--min-composite", type=float, default=None)
    run.add_argument("--json", action="store_true")

    validate = sub.add_parser("validate", help="validate a versioned JSON document")
    validate.add_argument("document")
    validate.add_argument("--kind", choices=["bundle", "scenario"], default="bundle")

    adapt = sub.add_parser("adapt", help="normalize an exported framework trace")
    adapt.add_argument("trace")
    adapt.add_argument("--adapter", choices=["generic", "openai-agents"], required=True)
    adapt.add_argument("--output", required=True)

    args = parser.parse_args(argv)
    if args.cmd == "validate":
        with open(args.document, encoding="utf-8") as handle:
            validate_document(json.load(handle), args.kind)
        print(f"valid {args.kind} schema_version=1.0")
        return 0
    if args.cmd == "adapt":
        events = load_trace(args.trace, args.adapter)
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump({"events": events}, handle, indent=2)
            handle.write("\n")
        print(f"adapted={len(events)} output={args.output}")
        return 0
    if args.cmd == "run":
        bundle = run_scenarios(args.scenario, backend=args.backend, model=args.model)
        write_bundle(bundle, args.output)
        runs = load_bundle(args.output)
        if not args.json:
            print(f"bundle={args.output} backend={args.backend}")
    else:
        runs = load_bundle(args.bundle)
    card = score_bundle(runs)
    payload = card.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(
            f"composite={card.composite:.4f} "
            f"success={card.task_success_rate:.4f} "
            f"reliability={card.reliability:.4f} "
            f"bias_gap={card.bias_gap:.4f}"
        )
        for mode, rate in card.failure_rates.items():
            if rate > 0:
                print(f"  fail:{mode}={rate:.4f}")

    if args.min_composite is not None and card.composite < args.min_composite:
        print(
            f"verdict: FAIL composite={card.composite:.4f} < floor={args.min_composite:.4f}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
