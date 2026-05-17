from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from lib._metrics import prior_non_full_score_count


def build_report(
    *,
    backend: str = "openhands",
    model: str,
    context_mode: str,
    run_id: str,
    results: list[dict[str, Any]],
    total_elapsed: float,
    error: str = "",
) -> dict[str, Any]:
    scores = [0.0] * 6
    for result in results:
        task_id = result.get("task_id")
        if isinstance(task_id, int) and 0 <= task_id <= 5:
            scores[task_id] = float(result.get("score") or 0)
    report = {
        "benchmark": "EvoBench-v2",
        "agent_backend": backend,
        "agent_model": model,
        "context_mode": context_mode,
        "run_id": run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_elapsed_seconds": total_elapsed,
        "tasks": results,
        "metrics": {
            "zero_shot_pass": all(score >= 60.0 for score in scores),
            "prior_non_full_score_count": prior_non_full_score_count(scores),
            "total_iterations": "",
        },
    }
    if error:
        report["_error"] = error
    return report


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
