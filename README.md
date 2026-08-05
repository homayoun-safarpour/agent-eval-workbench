# agent-eval-workbench

**A pass rate cannot show whether an agent looped, skipped a required tool, cited an unapproved source, or failed one small group. This workbench executes controlled scenarios and evaluates the trace evidence.**

[![CI](https://github.com/homayoun-safarpour/agent-eval-workbench/actions/workflows/ci.yml/badge.svg)](https://github.com/homayoun-safarpour/agent-eval-workbench/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## The problem

Agent evaluations often report one success rate. That number hides flaky retries, group performance
gaps, and the failure mechanism. The workbench runs versioned YAML scenarios, exports a validated
bundle, detects failures from events and answers, and returns CI exit `0` or `2`.

## Threat model (when this fails in production)

| Failure | What it looks like | What this repo does |
| --- | --- | --- |
| Success-only reporting | A pass hides a forbidden tool | Named trace-derived detector rates |
| Exporter verdict trusted | `loop_detected=true` with no supporting trace | Repeated event and cycle signatures |
| Citation accepted on sight | Answer links to an unapproved host | URL and host allowlist validation |
| Hidden demographic gap | Aggregate rate hides small groups | Counts, Wilson intervals, gap, ratio, warnings |
| Soft floor | Score prints but never gates | `--min-composite` returns exit `2` |

## Install

```bash
git clone https://github.com/homayoun-safarpour/agent-eval-workbench
cd agent-eval-workbench
pip install -e ".[dev]"
```

Python 3.10+. Runtime dependencies are PyYAML and jsonschema. The OpenAI client is an optional extra.

## Quickstart

```bash
agent-eval run examples/scenarios/benchmark.yaml --output /tmp/benchmark.json
agent-eval score /tmp/benchmark.json --json
```

The default runner is deterministic and makes no API call. To opt into the Responses API:

```bash
pip install -e ".[llm]"
OPENAI_API_KEY=... agent-eval run scenarios.yaml --backend openai --output /tmp/api.json
```

## Trace inputs

- Generic JSON events through `agent-eval adapt --adapter generic`.
- OpenAI Agents SDK exported spans through `agent-eval adapt --adapter openai-agents`.
- Controlled YAML scenarios through `agent-eval run`.
- Existing versioned bundles through `agent-eval score`.

The SDK adapter consumes exported JSON and does not require the framework at runtime. Schema details
are in [docs/SCHEMAS.md](docs/SCHEMAS.md).

## How we did it

The trace-evaluation shape follows public work in
[langchain-ai/agentevals](https://github.com/langchain-ai/agentevals) (MIT). This repository keeps a
smaller offline execution path, defines its own versioned contracts, adds uncertainty-aware group
output, and normalizes OpenAI Agents SDK exports. A contributor can clone, install, run the 24
scenarios, and inspect the measured JSON in under 30 minutes using the Quickstart.

## Evidence detectors

- missing, forbidden, and relative-order tool checks use normalized `tool_call` events;
- repeated-step loops use consecutive signatures and repeated cycles;
- citation checks extract URLs from answers and citation events, then compare them with an allowlist;
- task completion checks non-empty answers and required text;
- reproducibility compares outcome and tool sequence across trials.

The named tests are
`test_controlled_scenario_runs_end_to_end`,
`test_mixed_bundle_flags_failure_modes`,
`test_openai_agents_adapter_extracts_tool_evidence`,
`test_versioned_bundle_rejects_unknown_schema`, and
`test_bias_gap_when_groups_diverge`.

## Public benchmark

`examples/scenarios/benchmark.yaml` contains 24 controlled scenarios with 18 labeled failures across
six detector classes. A measured local run produced:

```text
true_positive=18 false_positive=0 false_negative=0
precision=1.0000 recall=1.0000 recorded_cost_usd=0.00
```

Reproduce the committed report and bundle:

```bash
python scripts/run_benchmark.py
```

The full measured output, runtime, fairness intervals, scorecard, errors, and limitations are in
[`examples/benchmark_results.json`](examples/benchmark_results.json). This synthetic benchmark tests
detector behavior. It does not measure open-world agent quality.

## Fairness interpretation

Group output includes `n`, successes, rate, 95% Wilson interval, absolute gap, and disparity ratio.
Groups below the minimum sample size receive an explicit warning. These outputs describe observed
associations only. They do not identify causes or establish fairness.

## Why there is no learned scorer dependency

The pinned deterministic benchmark recovered all 18 labels with no false positives. A learned
trajectory anomaly scorer has not shown additional signal on that set, so no deep-learning
stack is required for the default path.

## Docker (optional)

```bash
docker build -t agent-eval-workbench .
docker run --rm agent-eval-workbench
```

The image runs as UID 10001. CI builds and executes this path alongside Python 3.10-3.12 tests.

## Exit codes

- `0`: command completed and any requested composite floor passed.
- `2`: score is below `--min-composite`.
- other nonzero codes: invalid schema, configuration, or runtime error.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Adapter requests have a structured issue template.

## Citation

```bibtex
@software{agent_eval_workbench,
  author = {Homayoun Safarpour},
  title = {Agent Evaluation Workbench},
  url = {https://github.com/homayoun-safarpour/agent-eval-workbench},
  version = {0.2.0},
  year = {2026}
}
```

## Topics

`agents` · `evaluation` · `bias` · `reliability` · `llm` · `python` · `ci-cd`

## License

MIT. Author: Homayoun Safarpour · [LinkedIn](https://www.linkedin.com/in/homayoun-safarpour/)
