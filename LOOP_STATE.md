# Agent Evaluation Workbench delivery gate

## BENCHMARK GATE

- [x] CI matrix covers Python 3.10, 3.11, and 3.12.
- [x] Named claim tests cover scenarios, adapters, evidence detectors, fairness, and schemas.
- [x] `examples/benchmark_results.json` is measured output from 24 controlled scenarios.
- [x] README quickstart runs offline with no API key.
- [x] Sole-contributor and public-doc hygiene checked before push.
- [x] README uses direct engineering language.
- [x] `docs/INTERVIEW.md` contains three questions, a two-minute run, and limitations.
- [x] Docker builds a non-root image and executes the scenario path.

External field benchmark: N/A. The repository does not claim parity with a named field suite.
Its pinned benchmark is a public synthetic detector test set.

## Threat model

The workbench can be fooled by traces that omit events, aliases that adapters do not normalize,
citations requiring semantic verification, and demographic labels that encode confounding factors.
Schema validation catches malformed input, not dishonest instrumentation.

## Delivery ticks

- [x] W1: versioned bundle and scenario schema validation.
- [x] W2: generic and OpenAI Agents SDK export adapters.
- [x] W3: controlled YAML runner with deterministic mock backend.
- [x] W4: trace-derived tool, order, loop, citation, and completion detectors.
- [x] W5: Wilson intervals, group counts, disparity ratio, and sample warnings.
- [x] W6: 24-scenario benchmark, measured report, and model-dependency verdict.
- [x] W7: CI, non-root Docker, documentation, interview gate, and contribution path.

## Interview gate

1. Why is an exporter-supplied `loop_detected=true` weaker evidence than repeated event signatures?
2. Why do group success gaps need confidence intervals and sample warnings?
3. When would a learned trajectory scorer justify its operational cost?

Two-minute run:

```bash
pip install -e ".[dev]"
agent-eval run examples/scenarios/benchmark.yaml --output /tmp/run.json
python scripts/run_benchmark.py
```

Limitation: synthetic labels establish detector behavior only. They do not estimate performance on
open-world production traces.

**NEXT TICK:** Add a second framework adapter when a public trace fixture is available.
