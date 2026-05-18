"""解析 Kimi Code CLI `--output-format=stream-json` 的 JSONL 输出。

官方说明：每行一条 JSON；模型每轮产出为 `role: "assistant"` 的消息（可含 `tool_calls`），
随后可有 `role: "tool"`。统计 assistant 行数 ≈ 模型采样轮数（与 EvoBench `--max-iterations` 对齐）。
参见: https://moonshotai.github.io/kimi-cli/en/customization/print-mode.html
"""

from __future__ import annotations

import json
from typing import Any


def kimi_stream_json_assistant_lines(stdout: str) -> list[str]:
    """返回原始 JSON 行（仅 `role == assistant`），用于逐轮写入 agent-events。"""
    lines_out: list[str] = []
    if not stdout:
        return lines_out
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            obj: Any = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("role") == "assistant":
            lines_out.append(line)
    return lines_out


def kimi_stream_json_assistant_step_count(stdout: str) -> int:
    """模型步进数（assistant 消息条数）；无有效 JSONL 时返回 0。"""
    return len(kimi_stream_json_assistant_lines(stdout))
