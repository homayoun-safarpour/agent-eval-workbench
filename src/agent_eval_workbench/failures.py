"""Named failure-mode detectors for agent trajectories."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from agent_eval_workbench.bundle import TaskRun, Trial

MIN_LOOP_REPEATS = 3
_HOSTNAME = re.compile(r"[a-z0-9-]+(\.[a-z0-9-]+)*")


@dataclass(frozen=True)
class FailureHit:
    mode: str
    detail: str


def _tool_calls(trial: Trial) -> list[str]:
    event_tools = [
        str(event.get("name", ""))
        for event in trial.events
        if event.get("type") == "tool_call" and event.get("name")
    ]
    return event_tools or trial.tools_called


def _event_signature(event: dict[str, object]) -> str:
    return json.dumps(
        {
            "type": event.get("type"),
            "name": event.get("name"),
            "content": event.get("content"),
            "arguments": event.get("arguments"),
        },
        sort_keys=True,
        default=str,
    )


def _has_repeated_loop(trial: Trial) -> bool:
    signatures = [_event_signature(event) for event in trial.events]
    if len(signatures) < MIN_LOOP_REPEATS:
        return False
    if any(
        signatures[index] == signatures[index + 1] == signatures[index + 2]
        for index in range(len(signatures) - 2)
    ):
        return True
    for cycle_size in (2, 3):
        if len(signatures) >= cycle_size * 3:
            tail = signatures[-cycle_size:]
            if signatures[-cycle_size * 3 :] == tail * 3:
                return True
    return False


def _citation_urls(trial: Trial) -> set[str]:
    urls = set(re.findall(r"https?://[^\s)\]}>,]+", trial.final_answer))
    urls.update(
        str(event["url"])
        for event in trial.events
        if event.get("type") == "citation" and event.get("url")
    )
    return {url.rstrip(".,;") for url in urls}


def _citation_allowed(url: str, allowed: list[str]) -> bool:
    normalized = url.rstrip("/")
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    # A backslash or userinfo in the authority lets a browser resolve a different
    # host than the one the string appears to end with, so it is never allowed.
    if "\\" in parts.netloc or "@" in parts.netloc or not _HOSTNAME.fullmatch(host):
        return False
    return any(
        normalized == item.rstrip("/")
        or host == item.lower()
        or host.endswith(f".{item.lower()}")
        for item in allowed
    )


def _missing_content(run: TaskRun, trial: Trial) -> list[str]:
    return [
        phrase
        for phrase in run.expected_contains
        if phrase.lower() not in trial.final_answer.lower()
    ]


def trial_succeeded(run: TaskRun, trial: Trial) -> bool:
    """A trial succeeds only when it claims success, gives a non-empty answer and
    contains every `expected_contains` phrase. With no `expected_contains`, the
    run's own success flag (plus a non-empty answer) is all there is to check."""
    return bool(
        trial.success and trial.final_answer.strip() and not _missing_content(run, trial)
    )


def detect_failures(run: TaskRun, trial: Trial) -> list[FailureHit]:
    hits: list[FailureHit] = []
    missing_content = _missing_content(run, trial)
    if not trial_succeeded(run, trial):
        detail = (
            f"answer missing expected content: {missing_content}"
            if missing_content
            else "empty answer or trial outcome failed"
        )
        hits.append(FailureHit("task_fail", detail))
    expected = set(run.expected_tools)
    ordered_calls = _tool_calls(trial)
    called = set(ordered_calls)
    missing = expected - called
    if missing:
        hits.append(FailureHit("missing_tool", f"missing expected tools: {sorted(missing)}"))
    # A forbidden tool counts if either source records it: events and tools_called
    # can disagree, and dropping one of them would hide the call.
    forbidden = set(run.forbidden_tools) & (called | set(trial.tools_called))
    if forbidden:
        hits.append(FailureHit("forbidden_tool", f"called forbidden: {sorted(forbidden)}"))
    # Order: expected tools should appear in the same relative order when present
    if run.expected_tool_order:
        positions = []
        ok = True
        for tool in run.expected_tool_order:
            if tool not in ordered_calls:
                ok = False
                break
            positions.append(ordered_calls.index(tool))
        if ok and positions != sorted(positions):
            hits.append(FailureHit("tool_order", "expected tools out of order"))
    unsupported = sorted(
        url
        for url in _citation_urls(trial)
        if not _citation_allowed(url, run.allowed_citations)
    )
    if unsupported:
        hits.append(
            FailureHit("unsupported_citation", f"citation not in allowlist: {unsupported}")
        )
    if _has_repeated_loop(trial):
        hits.append(FailureHit("repeated_step_loop", "repeated event cycle found in trace"))
    return hits


FAILURE_MODES = (
    "task_fail",
    "missing_tool",
    "forbidden_tool",
    "tool_order",
    "unsupported_citation",
    "repeated_step_loop",
    "non_reproducible",
)
