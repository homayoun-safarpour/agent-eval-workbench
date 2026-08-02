# Schema contracts

Both document types use JSON Schema Draft 2020-12 and require `schema_version: "1.0"`.
Validation fails closed on unknown top-level and task/scenario fields.

## Bundle 1.0

A bundle contains evaluated tasks and one or more trials. Trial evidence can include:

- `tools_called`: compatibility path for generic exporters;
- `events`: normalized `tool_call`, `tool_result`, `message`, `step`, or `citation` records;
- `final_answer` and `success`;
- operational metadata such as backend, trial index, model, tokens, and recorded cost.

Task contracts define expected, forbidden, and ordered tools; required answer text; allowed citation
URLs or hosts; and an optional group tag.

```bash
agent-eval validate examples/bundle_good.json --kind bundle
```

## Scenario 1.0

A scenario supplies a prompt and the same task contract. `mock` contains deterministic events and
an answer. The optional OpenAI backend sends the prompt through the Responses API and records model
and token metadata; it does not run arbitrary local tools.

```bash
agent-eval run examples/scenarios/benchmark.yaml --output /tmp/run.json
```

The executable schemas are defined in `src/agent_eval_workbench/schema.py`. Changing a required
field or its meaning requires a new schema version.
