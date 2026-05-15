from __future__ import annotations

import argparse
from pathlib import Path

from core.job_manage import check_conflicts
from core.launch import run_batch
from core.summarize import collect_one
from lib._api_keys import load_api_keys
from lib._paths import DEFAULT_IMAGE, load_api_base
from lib._specs import ExperimentSpec, safe_name


def test_cache(args: argparse.Namespace) -> int:
    model = args.model[-1] if isinstance(args.model, list) and args.model else args.model
    if not model:
        raise ValueError("launch test-cache 需要 --model")
    run_id = args.run_id or f"test-cache-{safe_name(model)}"
    spec = ExperimentSpec(model=model, tasks=args.tasks, run_id=run_id)
    output_root = Path(args.output_dir)
    conflicts = check_conflicts([run_id], output_root)
    if conflicts and not args.dry_run:
        print("存在 run_id 冲突，未启动 test-cache。")
        return 2
    key_entries = load_api_keys(Path(args.api_keys))
    if args.dry_run:
        print(f"test-cache dry-run: model={spec.model} tasks={spec.tasks} run_id={spec.run_id}")
        return 0
    code = run_batch(
        specs=[spec],
        key_entries=key_entries,
        output_root=output_root,
        image=args.image or DEFAULT_IMAGE,
        api_base=load_api_base(explicit=args.api_base),
        context_mode=args.context_mode,
        max_iterations=args.max_iterations,
        prompt_cache_retention=args.prompt_cache_retention,
        litellm_log_level=args.litellm_log_level,
        max_agent_hours=args.max_agent_hours,
        parallel=1,
    )
    row = collect_one(output_root / run_id)
    print(
        f"cache_hit={row.get('cache_hit')} "
        f"cache_read={row.get('cache_hit_tokens')} cache_write={row.get('cache_write_tokens')}"
    )
    return code
