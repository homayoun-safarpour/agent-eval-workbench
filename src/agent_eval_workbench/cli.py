"""CLI for agent-eval-workbench."""

from __future__ import annotations

import argparse
import json
import sys

from agent_eval_workbench.bundle import load_bundle
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

    args = parser.parse_args(argv)
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
