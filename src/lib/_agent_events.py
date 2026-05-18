from __future__ import annotations

import json
import re
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


_TASK_JSONL_RE = re.compile(r"^task(\d+)\.jsonl$")


def _count_llm_responses_in_task_file(path: Path) -> int:
    """与 `agent_successful_llm_call_count` 相同：按 `llm_response_id` 去重，无 id 时按事件条数累计。"""
    ids: set[str] = set()
    fallback = 0
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict) or obj.get("event_type") != "llm_response":
            continue
        rid = obj.get("llm_response_id")
        if isinstance(rid, str) and rid:
            ids.add(rid)
        else:
            fallback += 1
    return len(ids) if ids else fallback


def agent_events_per_task_llm_rounds(run_dir: Path) -> dict[str, Any]:
    """CLI backend 写入的 `agent-events/taskN.jsonl` 中每任务 LLM 轮次（OpenHands 事件路径不会填充）。"""
    out: dict[str, Any] = {f"task{tid}_agent_llm_rounds": "" for tid in range(6)}
    root = run_dir / "agent-events"
    if not root.is_dir():
        return out
    for path in sorted(root.glob("task*.jsonl")):
        match = _TASK_JSONL_RE.match(path.name)
        if not match:
            continue
        tid = int(match.group(1))
        if 0 <= tid <= 5:
            out[f"task{tid}_agent_llm_rounds"] = _count_llm_responses_in_task_file(path)
    return out


def _usage_rows_from_codex_json_message(message: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in message.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict) or obj.get("type") != "turn.completed":
            continue
        usage = obj.get("usage")
        if isinstance(usage, dict):
            rows.append(usage)
    return rows


def _snap_from_codex_usage(usage: dict[str, Any]) -> dict[str, int | float] | None:
    """将 Codex ``exec --json`` 中 ``turn.completed.usage`` 对齐到 OpenHands base_state 口径。"""
    inp = int(usage.get("input_tokens") or 0)
    cached = int(usage.get("cached_input_tokens") or 0)
    out_t = int(usage.get("output_tokens") or 0)
    reasoning = int(usage.get("reasoning_output_tokens") or 0)
    cost = float(usage.get("total_cost_usd") or usage.get("cost_usd") or 0.0)
    prompt = max(inp - cached, 0)
    if not (inp or cached or out_t or reasoning or cost):
        return None
    return {
        "prompt": prompt,
        "completion": out_t,
        "reasoning": reasoning,
        "cache_read": cached,
        "cache_write": 0,
        "cost": cost,
    }


def _add_usage(acc: dict[str, int | float], snap: dict[str, int | float]) -> None:
    for key in ("prompt", "completion", "reasoning", "cache_read", "cache_write"):
        acc[key] += int(snap[key])
    acc["cost"] += float(snap["cost"])


def _total_tokens(acc: dict[str, int | float]) -> int:
    return int(acc["prompt"] + acc["completion"] + acc["reasoning"] + acc["cache_read"] + acc["cache_write"])


def _zero_usage() -> dict[str, int | float]:
    return {"prompt": 0, "completion": 0, "reasoning": 0, "cache_read": 0, "cache_write": 0, "cost": 0.0}


def collect_llm_metrics_from_agent_events(run_dir: Path, context_mode: str) -> dict[str, Any]:
    """当无 ``openhands-state`` 时，从 ``agent-events`` 中 Codex JSON 流解析 token（及可选费用）。"""
    empty: dict[str, Any] = {}
    root = run_dir / "agent-events"
    if not root.is_dir():
        return empty

    run_acc = _zero_usage()
    per_task: dict[int, dict[str, int | float]] = {i: _zero_usage() for i in range(6)}
    hits = 0
    cm = (context_mode or "").lower()

    for path in sorted(root.glob("task*.jsonl")):
        match = _TASK_JSONL_RE.match(path.name)
        if not match:
            continue
        tid = int(match.group(1))
        if not (0 <= tid <= 5):
            continue
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
            if not isinstance(obj, dict) or obj.get("event_type") != "llm_response":
                continue
            msg = obj.get("message")
            if not isinstance(msg, str) or not msg.strip():
                continue
            for usage in _usage_rows_from_codex_json_message(msg):
                snap = _snap_from_codex_usage(usage)
                if snap is None:
                    continue
                hits += 1
                _add_usage(run_acc, snap)
                _add_usage(per_task[tid], snap)

    if hits == 0:
        return empty

    row: dict[str, Any] = {
        "llm_metrics_source": "agent-events",
        "llm_tokens_logged": True,
        "run_llm_cost_usd": round(float(run_acc["cost"]), 6) if run_acc["cost"] else "",
        "run_llm_prompt_tokens": int(run_acc["prompt"]),
        "run_llm_completion_tokens": int(run_acc["completion"]),
        "run_llm_reasoning_tokens": int(run_acc["reasoning"]),
        "run_llm_cache_read_tokens": int(run_acc["cache_read"]),
        "run_llm_cache_write_tokens": int(run_acc["cache_write"]),
        "run_llm_total_tokens": _total_tokens(run_acc),
    }
    for i in range(6):
        row[f"task{i}_llm_total_tokens"] = ""
        row[f"task{i}_llm_cost_usd"] = ""

    for tid in range(6):
        acc = per_task[tid]
        if _total_tokens(acc) or acc["cost"]:
            row[f"task{tid}_llm_total_tokens"] = _total_tokens(acc)
            row[f"task{tid}_llm_cost_usd"] = round(float(acc["cost"]), 6) if acc["cost"] else ""

    if cm == "pipeline":
        # 与 collect_llm_metrics(openhands) 一致：pipeline 不在各 task 列展开
        for tid in range(6):
            row[f"task{tid}_llm_total_tokens"] = ""
            row[f"task{tid}_llm_cost_usd"] = ""

    return row
