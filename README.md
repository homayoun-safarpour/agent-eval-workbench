# workbench

**An agent can keep a 100% pass rate while it calls a forbidden tool and skips a required one, because the pass rate never reads the trace.**

[![CI](https://github.com/homayoun-safarpour/agent-eval-workbench/actions/workflows/ci.yml/badge.svg)](https://github.com/homayoun-safarpour/agent-eval-workbench/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Score agent runs from their trace events and fail CI below a composite floor (exit 0 or 2).

agent-eval-workbench is a command-line tool that runs YAML agent scenarios or reads exported runs and scores what the agent did from its trace. We built it because a pass rate shows only whether a task succeeded, whereas a successful run can still call a forbidden tool, skip a required one or cite an unapproved source. Given a run bundle, it applies fixed rules to each trace and combines task success, agreement between repeated trials, the gap between groups and forbidden or missing tools into one composite score. It prints a rate for each failure type and returns exit 2 below the `--min-composite` floor, so that CI can stop the change.

```bash
git clone https://github.com/homayoun-safarpour/agent-eval-workbench
cd agent-eval-workbench && pip install -e .
agent-eval score examples/forbidden_plus_missing_OUTPUT.json --min-composite 0.99
```

```text
composite=0.0000 success=1.0000 reliability=1.0000 bias_gap=0.0000
  fail:missing_tool=1.0000
  fail:forbidden_tool=1.0000
verdict: FAIL composite=0.0000 < floor=0.9900
```

That command exits 2. The same command on `examples/bundle_good.json` exits 0.

## What each result means

| Result | Exit | Meaning |
|---|---|---|
| Scorecard only | 0 | The composite is at or above `--min-composite`, or no floor was given. |
| `verdict: FAIL` (stderr) | 2 | The composite is below the `--min-composite` floor. |
| Traceback | 1 | Bad input: an unknown `schema_version` or field, a missing file, or `--backend openai` without `OPENAI_API_KEY`. |

Above, success is 1.0 while the composite is 0.0, because both runs called the forbidden `delete_account` and skipped the required `lookup_policy`. Exit 0 shows that the composite met the floor under fixed rules. It does not show that an answer is correct beyond its required text or that a cited page supports it. Without `--min-composite` the command always exits 0. Claim limits: [`docs/RELIABILITY_CARD.md`](docs/RELIABILITY_CARD.md).

## Use this when

| Situation | Use workbench? |
| --- | --- |
| Your runs are exported as JSON events or OpenAI Agents SDK spans and you want a CI check on tool use | Yes |
| You want versioned YAML scenarios that run offline on a mock backend with no API key | Yes |
| You want a language-model judge to grade free-text quality | No. Use [langchain-ai/agentevals](https://github.com/langchain-ai/agentevals) |
| You want to freeze an approved run and fail when a new run scores worse | No. Use [trace-gate](https://github.com/homayoun-safarpour/trace-gate) |
| Your traces are in OpenTelemetry format | Not directly. Convert them to the JSON event shape first |

Python 3.10 or later. The runtime dependencies are PyYAML and jsonschema; the OpenAI client is an optional extra.

## The problem

Agent evaluations often report one success rate. That number hides flaky retries, gaps between groups, and the way a run failed. An exporter's own `loop_detected=true` is weak evidence, a cited link may point to an unapproved host, and a score that only prints never stops a build. The workbench reads each failure from the trace events and turns the composite into a gate.

## How it works

1. `agent-eval run` executes YAML scenarios on the mock backend and writes a versioned bundle.
2. `agent-eval score` runs the detectors on every trial of a bundle and prints the scorecard.
3. The composite is `0.5 × success + 0.5 × reliability − (group gap + forbidden-tool rate + 0.5 × missing-tool rate)`, kept between 0 and 1. Reliability is how far repeated trials of a task agree.

```bash
agent-eval run examples/scenarios/benchmark.yaml --output run.json --min-composite 0.10
```

```text
bundle=run.json backend=mock
composite=0.6667 success=0.8750 reliability=1.0000 bias_gap=0.0833
  fail:task_fail=0.1250
  fail:missing_tool=0.1250
  fail:forbidden_tool=0.1250
  fail:tool_order=0.1250
  fail:unsupported_citation=0.1250
  fail:repeated_step_loop=0.1250
```

That command exits 0, and CI runs it with the same floor. `agent-eval score run.json --json` adds each group's count, rate and 95% Wilson interval. Other commands:

```bash
agent-eval validate examples/bundle_good.json --kind bundle      # valid bundle schema_version=1.0
agent-eval adapt TRACE.json --adapter openai-agents --output events.json   # or --adapter generic
pip install -e ".[llm]" && OPENAI_API_KEY=... agent-eval run scenarios.yaml --backend openai --output api.json
```

| Module | What it does |
|---|---|
| `runner` | Runs YAML scenarios on the mock or OpenAI backend and writes a bundle |
| `adapters` | Turns generic JSON events or exported OpenAI Agents SDK spans into events, without the SDK |
| `schema` | JSON Schema 2020-12 contracts; unknown fields fail ([docs/SCHEMAS.md](docs/SCHEMAS.md)) |
| `failures` | Task failure, missing, forbidden and out-of-order tools, unapproved citations, repeated-step loops |
| `fairness` | Group counts, rates, Wilson intervals, gap, ratio, warnings for groups under 5 trials |
| `scorecard` | The composite, plus the non-reproducible check across trials |

Interview pack: [docs/INTERVIEW.md](docs/INTERVIEW.md), five commands and three questions.

## Public benchmark

`examples/scenarios/benchmark.yaml` holds 24 controlled scenarios with 18 labelled failures, three for each of six detectors.

```bash
python scripts/run_benchmark.py
```

```text
{
  "true_positive": 18,
  "false_positive": 0,
  "false_negative": 0,
  "precision": 1.0,
  "recall": 1.0,
  "errors": []
}
```

The script then prints the paths of the two files it rewrote, [`examples/benchmark_results.json`](examples/benchmark_results.json) and `examples/benchmark_bundle.json`, and exits 0 when every scenario matches its labels. Because the fixed rules found all 18 labels, the default path needs no learned model.

## Limits

- It is not a language-model judge. It checks tool calls, required text, citation hosts and repeated steps, and it does not grade the meaning of an answer.
- Only the group gap and forbidden or missing tools lower the composite directly. Loops, tool order and citation failures show as rates.
- The benchmark is synthetic. It tests detector behaviour, not agent quality on open-world traces.
- The citation check compares URLs and hosts with an allowlist. It does not check that the source supports the answer.
- Group output is descriptive. It does not identify causes or establish fairness.
- A trace that leaves out events, or uses tool names the adapters do not normalise, can pass. Schema validation catches malformed input, not dishonest instrumentation.
- The OpenAI backend sends only the prompt and runs no local tools, so the tool detectors see no tool calls on that path.

## Docker (optional)

```bash
docker build -t agent-eval-workbench .
docker run --rm agent-eval-workbench
```

The image runs as UID 10001. CI builds and runs it next to the Python 3.10 to 3.12 tests.

## How we did it

1. **Chose the upstream.** The trace-evaluation shape follows public work in [langchain-ai/agentevals](https://github.com/langchain-ai/agentevals) (MIT). This repository keeps a smaller offline execution path and defines its own versioned contracts.
2. **Read evidence from the trace.** Each detector reads events and answers, never a verdict the exporter supplied, and group output carries Wilson intervals and sample warnings.
3. **Made the floor a gate.** `--min-composite` returns exit `2`. Named tests: `test_mixed_bundle_flags_failure_modes`, `test_detect_missing_and_forbidden_tools`, `test_openai_agents_adapter_extracts_tool_evidence`, `test_versioned_bundle_rejects_unknown_schema`, `test_bias_gap_when_groups_diverge`, `test_readme_stranger_score_exits_2`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Adapter requests have a structured issue template.

## Related tools

- [trace-gate](https://github.com/homayoun-safarpour/trace-gate): fails CI when an agent run scores worse than a frozen baseline.
- [agent-loop-engine](https://github.com/homayoun-safarpour/agent-loop-engine): state, gates, the next-step decision and a journal for agent loops.
- [judge-field-guide](https://github.com/homayoun-safarpour/judge-field-guide): a link-checked map of tools for language-model judges.

## Citation

Use the "Cite this repository" button on GitHub, or:

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
