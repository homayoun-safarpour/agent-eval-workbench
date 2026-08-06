# Interview talking points — agent-eval-workbench

Five CLI-backed points for a technical screen (no resume recap).

- **`agent-eval run examples/scenarios/benchmark.yaml --output /tmp/run.json`** — executes versioned YAML scenarios (mock backend in CI) and writes a schema-valid run bundle.
- **`agent-eval score /tmp/run.json --json`** — prints success, reliability, fairness diagnostics, and failure-mode detector hits on one composite card.
- **`agent-eval run examples/scenarios/forbidden-plus-missing.yaml --output examples/forbidden_plus_missing_OUTPUT.json --min-composite 0.99`** — fail-closed demo (exit `2`); see `examples/forbidden_plus_missing_CLI.txt`. Same floor pattern as `score --min-composite`.
- **`agent-eval validate BUNDLE.json --kind bundle`** — jsonschema gate before you merge an exported trace bundle from another runner.
- **`agent-eval adapt TRACE.json --adapter openai-agents --output events.json`** — normalizes framework traces into the event shape the detectors expect.

## Three questions

1. **Why score reliability separately from success rate?**  
   A single lucky trial can show success=true. Reliability asks whether repeated trials on the same task agree. Flaky agents look "good" on success and bad on reliability.

2. **What does the fairness output establish?**  
   It reports group counts, success rates, 95% Wilson intervals, an absolute gap, and a disparity ratio. Small groups trigger warnings. These are descriptive diagnostics, not causal estimates.

3. **How does this relate to trace-gate?**  
   Workbench = multi-axis diagnosis on a bundle. trace-gate = freeze a trajectory score and fail deploy if it regresses. Feed workbench outputs into human review; pin tool-use contracts with trace-gate.

## One limitation

The public benchmark is synthetic and tests known detector boundaries. Citation checks validate URLs against an allowlist, not the semantic truth of a source. Fairness diagnostics are non-causal.
