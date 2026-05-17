from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterator


def append_agent_event(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **payload}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def iter_agent_events(run_dir: Path) -> Iterator[dict[str, Any]]:
    root = run_dir / "agent-events"
    if not root.is_dir():
        return
    for path in sorted(root.glob("*.jsonl")):
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                yield obj


def agent_successful_llm_call_count(run_dir: Path) -> int:
    ids: set[str] = set()
    fallback = 0
    for event in iter_agent_events(run_dir):
        if event.get("event_type") != "llm_response":
            continue
        rid = event.get("llm_response_id")
        if isinstance(rid, str) and rid:
            ids.add(rid)
        else:
            fallback += 1
    return len(ids) if ids else fallback


def agent_error_events(run_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for event in iter_agent_events(run_dir):
        if event.get("event_type") != "error":
            continue
        errors.append(
            {
                "code": event.get("code", ""),
                "kind": event.get("kind", ""),
                "detail": event.get("detail", ""),
                "timestamp": event.get("timestamp", ""),
            }
        )
    return errors
