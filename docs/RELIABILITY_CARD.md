# Reliability card — agent-eval-workbench

| Field | Value |
| --- | --- |
| **Job** | Run controlled agent scenarios and score failure modes from trace evidence |
| **Primary signals** | Detector rates + composite score + Wilson gaps |
| **Exit codes** | `0` pass / `2` fail closed (`--min-composite`) |
| **Fixtures** | `examples/scenarios/` |
| **Claim** | A single pass rate hides looping, forbidden tools, bad citations, and group gaps |
| **Not claimed** | Replaces LLM-as-judge platforms; no PyTorch training loop |

## Field alignment

Matches agentic-platform hire language: multi-layer harness, deterministic detectors first, CI gate. Complements `trace-gate` (deploy pin) with scenario/detector evidence.
