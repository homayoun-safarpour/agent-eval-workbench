# Interview gate: agent-eval-workbench

## Three questions

1. **Why score reliability separately from success rate?**  
   A single lucky trial can show success=true. Reliability asks whether repeated trials on the same task agree. Flaky agents look "good" on success and bad on reliability.

2. **What does the fairness output establish?**
   It reports group counts, success rates, 95% Wilson intervals, an absolute gap, and a disparity
   ratio. Small groups trigger warnings. These are descriptive diagnostics, not causal estimates.

3. **How does this relate to trace-gate?**  
   Workbench = multi-axis diagnosis on a bundle. trace-gate = freeze a trajectory score and fail deploy if it regresses. Feed workbench outputs into human review; pin tool-use contracts with trace-gate.

## Two-minute run

```bash
git clone https://github.com/homayoun-safarpour/agent-eval-workbench
cd agent-eval-workbench
pip install -e ".[dev]"
agent-eval run examples/scenarios/benchmark.yaml --output /tmp/run.json
agent-eval score /tmp/run.json --json
python scripts/run_benchmark.py
pytest -q
```

Expect: a schema-valid 24-scenario bundle, measured detector metrics, and green tests.

## One limitation

The public benchmark is synthetic and tests known detector boundaries. Citation checks validate
URLs against an allowlist, not the semantic truth of a source. Fairness diagnostics are non-causal.
