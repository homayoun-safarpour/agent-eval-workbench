"""Versioned JSON Schema validation for bundles and controlled scenarios."""

from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_VERSION = "1.0"

EVENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["type"],
    "properties": {
        "type": {"enum": ["tool_call", "tool_result", "message", "step", "citation"]},
        "name": {"type": "string"},
        "content": {"type": "string"},
        "arguments": {"type": "object"},
        "url": {"type": "string"},
    },
    "additionalProperties": True,
}

TRIAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["final_answer", "success"],
    "properties": {
        "tools_called": {"type": "array", "items": {"type": "string"}},
        "events": {"type": "array", "items": EVENT_SCHEMA},
        "final_answer": {"type": "string"},
        "success": {"type": "boolean"},
        "metadata": {"type": "object"},
    },
    "additionalProperties": False,
}

BUNDLE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://homayoun-safarpour.github.io/agent-eval-workbench/bundle-1.0.json",
    "title": "Agent Evaluation Bundle 1.0",
    "type": "object",
    "required": ["schema_version", "tasks"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "tasks": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["task_id", "trials"],
                "properties": {
                    "task_id": {"type": "string", "minLength": 1},
                    "expected_tools": {"type": "array", "items": {"type": "string"}},
                    "forbidden_tools": {"type": "array", "items": {"type": "string"}},
                    "expected_tool_order": {"type": "array", "items": {"type": "string"}},
                    "expected_contains": {"type": "array", "items": {"type": "string"}},
                    "allowed_citations": {"type": "array", "items": {"type": "string"}},
                    "demographic_tag": {"type": ["string", "null"]},
                    "trials": {"type": "array", "minItems": 1, "items": TRIAL_SCHEMA},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}

SCENARIO_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://homayoun-safarpour.github.io/agent-eval-workbench/scenario-1.0.json",
    "title": "Agent Evaluation Scenario 1.0",
    "type": "object",
    "required": ["schema_version", "scenarios"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "scenarios": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id", "prompt"],
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                    "prompt": {"type": "string", "minLength": 1},
                    "trials": {"type": "integer", "minimum": 1, "maximum": 20},
                    "expected_tools": {"type": "array", "items": {"type": "string"}},
                    "forbidden_tools": {"type": "array", "items": {"type": "string"}},
                    "expected_tool_order": {"type": "array", "items": {"type": "string"}},
                    "expected_contains": {"type": "array", "items": {"type": "string"}},
                    "allowed_citations": {"type": "array", "items": {"type": "string"}},
                    "expected_failures": {"type": "array", "items": {"type": "string"}},
                    "demographic_tag": {"type": ["string", "null"]},
                    "mock": {
                        "type": "object",
                        "properties": {
                            "events": {"type": "array", "items": EVENT_SCHEMA},
                            "final_answer": {"type": "string"},
                        },
                        "required": ["final_answer"],
                        "additionalProperties": False,
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}


def validate_document(document: dict[str, Any], kind: str) -> None:
    """Raise a precise validation error for an unsupported or malformed document."""
    schema = BUNDLE_SCHEMA if kind == "bundle" else SCENARIO_SCHEMA
    Draft202012Validator(schema).validate(document)
