# Contributing

## Local checks

```bash
python -m pip install -e ".[dev]"
ruff check src tests scripts
pytest -q
python scripts/run_benchmark.py --output /tmp/results.json --bundle-output /tmp/bundle.json
```

Pull requests should add a named test for each behavior claim. New detectors need:

1. a clean negative fixture;
2. a labeled positive fixture under `examples/scenarios/`;
3. a trace-derived signal rather than an exporter-supplied verdict;
4. an explicit limitation in the documentation.

Good first extensions include adapters for LangChain or OpenTelemetry exports and new citation
resolvers. Do not add a model dependency unless a pinned benchmark shows an improvement over the
deterministic baseline.
