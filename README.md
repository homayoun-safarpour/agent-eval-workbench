# agent-eval-workbench

**Unit tests say the agent imported cleanly. Production still needs a scorecard for task success, repeatability, demographic gaps, and named failure modes. This workbench scores all four from the same run bundle.**

[![CI](https://github.com/homayoun-safarpour/agent-eval-workbench/actions/workflows/ci.yml/badge.svg)](https://github.com/homayoun-safarpour/agent-eval-workbench/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## The problem

Agent demos report a single "success rate". That number hides flaky retries, group performance gaps, and *why* trials failed (forbidden tools, missing tools, loops, invented citations). Interviewers and on-call engineers need a multi-axis scorecard with exit codes, not a screenshot of a chat.

## Threat model (when this fails in production)

| Failure | What it looks like | What this repo does |
| --- | --- | --- |
| Success-only reporting | 80% pass; half the failures are forbidden tools | Named failure-mode rates on every scorecard |
| Flaky agent treated as stable | One lucky trial greenlights a PR | Reliability = agreement across repeated trials |
| Hidden demographic gap | Aggregate success hides group_a vs group_b | `bias_gap` = max-min success across tags |
| Soft floor | Composite printed, never gated | `--min-composite` → exit `2` |
| Trajectory gate confusion | Mixing tool-order CI with bias analysis | This is the scorecard layer; [trace-gate](https://github.com/homayoun-safarpour/trace-gate) is the deploy pin |

## Install

```bash
git clone https://github.com/homayoun-safarpour/agent-eval-workbench
cd agent-eval-workbench
pip install -e ".[dev]"
```

Python 3.10+. Zero runtime dependencies. Optional Docker image included.

## Quickstart

```bash
agent-eval score examples/bundle_good.json
agent-eval score examples/bundle_mixed.json --min-composite 0.95
```

Real output from this repository:

```
$ agent-eval score examples/bundle_good.json
composite=1.0000 success=1.0000 reliability=1.0000 bias_gap=0.0000

$ agent-eval score examples/bundle_mixed.json --json
(see examples/scorecard_mixed.json)
```

## How we did it

1. **Chose upstream patterns.** Trajectory eval demand is proven by [langchain-ai/agentevals](https://github.com/langchain-ai/agentevals) (MIT) and broader agent benches such as [reworkd/bananalyzer](https://github.com/reworkd/bananalyzer) (MIT). Full benches are too heavy for a 30-minute fork.
2. **Restyled into one instrument.** MIT package `agent-eval-workbench`: JSON run bundles, repeated trials, demographic tags, deterministic detectors.
3. **Sharp improvement.** Multi-axis scorecard with a named failure-mode taxonomy (`forbidden_tool`, `missing_tool`, `tool_order`, `hallucinated_citation`, `infinite_loop`) plus `bias_gap` and reliability. Named tests: `test_mixed_bundle_flags_failure_modes`, `test_bias_gap_when_groups_diverge`.
4. **Reproduce committed artifacts:**

```bash
agent-eval score examples/bundle_mixed.json --json > examples/scorecard_mixed.json
```

## Compose with the rest of the stack

| Repo | Role next to this |
| --- | --- |
| [trace-gate](https://github.com/homayoun-safarpour/trace-gate) | Pin trajectory scores and fail CI on regression |
| [judge-reliability-kit](https://github.com/homayoun-safarpour/judge-reliability-kit) | When a human/LLM judge labels outcomes, diagnose disagreement |
| [judge-drift-sentinel](https://github.com/homayoun-safarpour/judge-drift-sentinel) | Detect judge drift on frozen anchors |
| [agent-loop-engine](https://github.com/homayoun-safarpour/agent-loop-engine) | Use `--min-composite` exit `2` as a quality gate |

## Docker (optional)

```bash
docker build -t agent-eval-workbench .
docker run --rm agent-eval-workbench score examples/bundle_good.json
```

## Topics

`agents` · `evaluation` · `bias` · `reliability` · `llm` · `python` · `ci-cd`

## License

MIT. Author: Homayoun Safarpour · [LinkedIn](https://www.linkedin.com/in/homayoun-safarpour/)
