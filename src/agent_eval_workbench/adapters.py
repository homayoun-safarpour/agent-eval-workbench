"""Trace adapters for generic JSON and OpenAI Agents SDK-style exports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def adapt_generic_trace(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize an ``events`` array without changing evidence."""
    events = document.get("events", [])
    if not isinstance(events, list):
        raise ValueError("generic trace must contain an events array")
    return [dict(event) for event in events]


def adapt_openai_agents_trace(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize OpenAI Agents SDK trace spans into workbench events.

    The adapter accepts exported spans, so the SDK is not a runtime dependency.
    It recognizes function spans and generation/response spans while retaining
    unrecognized spans as evidence-bearing steps.
    """
    spans = document.get("spans", document.get("trace", []))
    if not isinstance(spans, list):
        raise ValueError("OpenAI trace must contain a spans or trace array")
    events: list[dict[str, Any]] = []
    for span in spans:
        data = span.get("span_data", span.get("data", span))
        span_type = str(data.get("type", span.get("type", "step")))
        if span_type in {"function", "function_call", "tool"}:
            events.append(
                {
                    "type": "tool_call",
                    "name": str(data.get("name", data.get("function_name", ""))),
                    "arguments": data.get("input", data.get("arguments", {})) or {},
                }
            )
            if data.get("output") is not None:
                events.append(
                    {
                        "type": "tool_result",
                        "name": str(data.get("name", data.get("function_name", ""))),
                        "content": str(data["output"]),
                    }
                )
        elif span_type in {"generation", "response", "message"}:
            content = data.get("output", data.get("content", ""))
            events.append({"type": "message", "content": str(content)})
        else:
            events.append(
                {
                    "type": "step",
                    "name": str(data.get("name", span_type)),
                    "content": str(data.get("input", data.get("content", ""))),
                }
            )
    return events


def load_trace(path: str | Path, adapter: str) -> list[dict[str, Any]]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if adapter == "openai-agents":
        return adapt_openai_agents_trace(document)
    if adapter == "generic":
        return adapt_generic_trace(document)
    raise ValueError(f"unknown adapter: {adapter}")
