# CV evidence

## Defensible stack

Python 3.10-3.12, JSON Schema Draft 2020-12, PyYAML, pytest, Ruff, Docker, GitHub Actions,
OpenAI Responses API (optional integration), OpenAI Agents SDK trace-export adapter, Wilson score
intervals, deterministic trace analysis.

## Approved wording

Built a controlled agent-evaluation workbench with versioned trace schemas, OpenAI Agents
SDK export normalization, reproducible YAML scenarios, evidence-based tool/loop/citation checks,
uncertainty-aware group diagnostics, CI on Python 3.10-3.12, and a non-root Docker path; the pinned
24-scenario detector benchmark recovered 18/18 labeled failures with no false positives.

## Excluded wording

Do not list PyTorch, learned trajectory anomaly detection, causal fairness analysis, hosted service,
or production-scale agent benchmarking for this repository. The deterministic rules recovered all
labels in the pinned benchmark, so a learned scorer has not shown incremental value and PyTorch is
not a dependency.
