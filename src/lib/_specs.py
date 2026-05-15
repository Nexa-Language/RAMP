from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path


DEFAULT_TASKS = "0-5"


@dataclass(frozen=True)
class ExperimentSpec:
    model: str
    tasks: str
    run_id: str


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return value or "run"


def parse_tasks(value: str) -> list[int]:
    tasks: set[int] = set()
    for raw in value.split(","):
        part = raw.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start, end = int(start_s), int(end_s)
            if end < start:
                raise ValueError(f"非法任务范围: {part}")
            tasks.update(range(start, end + 1))
        else:
            tasks.add(int(part))
    result = sorted(tasks)
    if not result:
        raise ValueError("任务范围为空")
    for task_id in result:
        if task_id < 0 or task_id > 5:
            raise ValueError(f"任务编号超出范围: {task_id}")
    return result


def load_models(models_file: Path) -> list[str]:
    data = json.loads(models_file.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{models_file} must contain a JSON array")
    return [str(item).strip() for item in data if isinstance(item, str) and item.strip()]


def add_csv_models(models: list[str], csv: str) -> None:
    for item in csv.split(","):
        model = item.strip()
        if model:
            models.append(model)


def read_experiment_file(path: Path) -> list[str]:
    specs: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            specs.append(line)
    return specs


def parse_experiment_specs(
    *,
    selected_models: list[str],
    explicit_specs: list[str],
    default_tasks: str = DEFAULT_TASKS,
    run_prefix: str | None = None,
) -> list[ExperimentSpec]:
    specs = list(explicit_specs)
    specs.extend(f"{model}:{default_tasks}" for model in selected_models)
    if not specs:
        raise ValueError("没有选择实验。请使用 --model、--models、--experiment、--experiments-file 或 --all-models。")
    prefix = run_prefix or f"run-{time.strftime('%Y%m%d-%H%M%S')}"
    seen: set[str] = set()
    out: list[ExperimentSpec] = []
    for spec in specs:
        parts = spec.split(":", 3)
        model = parts[0].strip() if len(parts) > 0 else ""
        tasks = parts[1].strip() if len(parts) > 1 and parts[1].strip() else default_tasks
        run_id = parts[2].strip() if len(parts) > 2 else ""
        if not model:
            raise ValueError(f"实验缺少模型名: {spec}")
        parse_tasks(tasks)
        if not run_id:
            run_id = f"{prefix}-{safe_name(model)}-tasks-{safe_name(tasks)}"
        run_id = safe_name(run_id)
        if run_id in seen:
            raise ValueError(f"run id 重复: {run_id}")
        seen.add(run_id)
        out.append(ExperimentSpec(model=model, tasks=tasks, run_id=run_id))
    return out
