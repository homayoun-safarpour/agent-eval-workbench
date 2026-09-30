# LinkedIn draft (public-safe) - workbench first-screen restyle 2026-09-30

Field pain first. Homayoun posts himself.
Paste verified 2026-09-30 on examples/forbidden_plus_missing_OUTPUT.json: composite=0.0000, exit 2.

---

Paste block (copy from the next line to the URL):

A pass rate of 1.0 can still hide a forbidden tool call.

agent-eval-workbench scores the trace, not the smile.

The stranger run is the FAIL floor:

git clone https://github.com/homayoun-safarpour/agent-eval-workbench
cd agent-eval-workbench && pip install -e .
agent-eval score examples/forbidden_plus_missing_OUTPUT.json --min-composite 0.99

composite=0.0000 success=1.0000
  fail:missing_tool=1.0000
  fail:forbidden_tool=1.0000
verdict: FAIL composite=0.0000 < floor=0.9900

Exit 2. Success was 1.0. The composite was 0.0.

The limit: mock scenarios, not open-world agent quality. No LLM in the default path.

Repo:
https://github.com/homayoun-safarpour/agent-eval-workbench
