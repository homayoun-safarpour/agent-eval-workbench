# Interview gate — agent-eval-workbench

## Three questions

1. **Why score reliability separately from success rate?**  
   A single lucky trial can show success=true. Reliability asks whether repeated trials on the same task agree. Flaky agents look "good" on success and bad on reliability.

2. **What does `bias_gap` actually compute?**  
   Absolute difference between max and min success rates across `demographic_tag` groups. It is a screening signal, not a causal fairness proof.

3. **How does this relate to trace-gate?**  
   Workbench = multi-axis diagnosis on a bundle. trace-gate = freeze a trajectory score and fail deploy if it regresses. Feed workbench outputs into human review; pin tool-use contracts with trace-gate.

## Two-minute demo

```bash
git clone https://github.com/homayoun-safarpour/agent-eval-workbench
cd agent-eval-workbench
pip install -e ".[dev]"
agent-eval score examples/bundle_good.json --min-composite 0.9
agent-eval score examples/bundle_mixed.json --min-composite 0.95
pytest -q
```

Expect: first command exit 0, second exit 2, tests green.

## One limitation

Failure modes such as `hallucinated_citation` and `infinite_loop` currently read metadata flags from the exporter. A production tracer must set those flags; this repo does not infer them from free text.
