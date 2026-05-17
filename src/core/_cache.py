from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.job_manage import check_conflicts
from core.launch import run_batch
from core.summarize import collect_one
from lib._api_keys import load_api_keys
from lib._paths import DEFAULT_IMAGE
from lib._specs import ExperimentSpec, add_csv_models, safe_name


def _default_test_cache_run_id(args: argparse.Namespace, model: str) -> str:
    prefix = getattr(args, "run_prefix", "") or "test-cache"
    return safe_name(f"{prefix}-{model}-tasks-{args.tasks}")


def _test_cache_model_list(args: argparse.Namespace) -> list[str]:
    selected: list[str] = []
    for m in args.model or []:
        if m and str(m).strip():
            selected.append(str(m).strip())
    add_csv_models(selected, getattr(args, "models", "") or "")
    return selected


def _test_cache_specs(args: argparse.Namespace, models: list[str]) -> list[ExperimentSpec]:
    if len(models) > 1 and str(getattr(args, "run_id", "") or "").strip():
        raise ValueError("launch test-cache 指定多个模型时不能使用 --run-id，请用 --run-prefix 区分批次。")
    if len(models) == 1 and str(getattr(args, "run_id", "") or "").strip():
        model = models[0]
        rid = safe_name(args.run_id)
        return [ExperimentSpec(model=model, tasks=args.tasks, run_id=rid)]
    return [
        ExperimentSpec(model=model, tasks=args.tasks, run_id=_default_test_cache_run_id(args, model))
        for model in models
    ]


def test_cache(args: argparse.Namespace) -> int:
    models = _test_cache_model_list(args)
    if not models:
        raise ValueError("launch test-cache 需要至少一个模型：使用 --model（可多次）或 --models a,b,c")
    specs = _test_cache_specs(args, models)
    output_root = Path(args.output_dir)
    conflicts = check_conflicts([s.run_id for s in specs], output_root)
    if conflicts and not args.dry_run:
        print("存在 run_id 冲突，未启动 test-cache。")
        for trace in conflicts:
            print(json.dumps(trace.__dict__, ensure_ascii=False))
        return 2
    key_entries = load_api_keys(Path(args.api_keys))
    if args.dry_run:
        for spec in specs:
            print(f"test-cache dry-run: model={spec.model} tasks={spec.tasks} run_id={spec.run_id}")
        return 0
    parallel = max(1, min(int(getattr(args, "parallel", 1) or 1), len(specs)))
    code = run_batch(
        specs=specs,
        key_entries=key_entries,
        output_root=output_root,
        image=args.image or DEFAULT_IMAGE,
        context_mode=args.context_mode,
        max_iterations=args.max_iterations,
        prompt_cache_retention=args.prompt_cache_retention,
        litellm_log_level=args.litellm_log_level,
        max_agent_hours=args.max_agent_hours,
        parallel=parallel,
    )
    for spec in specs:
        row = collect_one(output_root / spec.run_id)
        print(
            f"[test-cache] {spec.model} run_id={spec.run_id} "
            f"cache_hit={row.get('cache_hit')} "
            f"cache_read={row.get('cache_hit_tokens')} cache_write={row.get('cache_write_tokens')}"
        )
    return code
