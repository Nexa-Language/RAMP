from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core._agent_backends import BackendContext, SUPPORTED_BACKENDS, ensure_backend, run_cli_backend_task
from core._prompt import TaskGuides, build_task_prompt
from core._report import build_report, write_report
from core._score import build_and_score, build_answers, configure_workspace
from core.runner import cmd_emit_report, cmd_score, prepare_workspace, run_openhands
from lib._api_keys import load_api_keys, select_api_key
from lib._paths import DEFAULT_API_KEYS_FILE, ROOT
from lib._run_budget import format_wall_remaining_display, remaining_iterations_budget, remaining_wall_seconds
from lib._specs import parse_tasks, safe_name


def run_cli_backend(args: argparse.Namespace) -> int:
    backend = ensure_backend(args.backend)
    if backend == "openhands":
        return run_openhands(args)
    output_dir = Path(args.output_dir) if args.output_dir else ROOT / "eval" / "results" / safe_name(args.model)
    output_dir.mkdir(parents=True, exist_ok=True)
    workspace = prepare_workspace(Path(args.workspace) if args.workspace else None)
    tasks = parse_tasks(args.tasks)
    run_id = args.run_id or f"{safe_name(args.model)}-{time.strftime('%Y%m%d-%H%M%S')}"
    key_entry = select_api_key(load_api_keys(Path(args.api_keys)), args.model)
    api_key = os.getenv("OPENAI_API_KEY") or key_entry.key
    results: list[dict[str, Any]] = []
    start = time.time()
    error = ""
    report_path = output_dir / "openhands_report.json"

    def _handle_stop(signum: int, _frame: Any) -> None:
        raise KeyboardInterrupt(f"received signal {signum}")

    old_int = signal.signal(signal.SIGINT, _handle_stop)
    old_term = signal.signal(signal.SIGTERM, _handle_stop)
    try:
        print("=" * 70)
        print(f"{backend} Agent EvoBench Runner")
        print(f"模型: {args.model}")
        print(f"任务: {tasks}")
        print(f"上下文模式: {args.context_mode}")
        print(f"最大迭代: {args.max_iterations}")
        print(f"Run ID: {run_id}")
        print(f"输出目录: {output_dir}")
        print("=" * 70)
        print("[初始化] CMake 配置（TASK*_REVIVE=ON）...")
        configure_workspace(workspace)
        print("[初始化] 生成标准答案...")
        build_answers(workspace)
        guides = TaskGuides(ROOT)
        ctx = BackendContext(
            backend=backend,
            model=args.model,
            api_key=api_key,
            api_base=key_entry.base_url,
            workspace=workspace,
            output_dir=output_dir,
            run_id=run_id,
            max_iterations=args.max_iterations,
        )
        first_pipeline_task = True
        for task_id in tasks:
            task_start = time.time()
            print(f"[Task {task_id}] 开始")
            if args.context_mode == "pipeline":
                stage = "first" if first_pipeline_task else "continue"
                first_pipeline_task = False
            else:
                stage = None
            wall_sec = remaining_wall_seconds(output_dir)
            prompt = build_task_prompt(
                task_id=task_id,
                context_mode=args.context_mode,
                workspace=workspace,
                guides=guides,
                pipeline_stage=stage,
                budget_wall_display=format_wall_remaining_display(wall_sec),
                budget_remaining_iterations=remaining_iterations_budget(
                    output_dir, args.context_mode, args.max_iterations
                ),
            )
            try:
                run_cli_backend_task(ctx, task_id, prompt)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                print(f"[Task {task_id}] Agent 异常: {error}")
            score = build_and_score(workspace, task_id)
            entry = {
                "task_id": task_id,
                "score": score.get("score", 0),
                "max_score": score.get("max_score", 100),
                "passed": score.get("passed", False),
                "test_count": score.get("test_count", 0),
                "passed_count": score.get("passed_count", 0),
                "elapsed_seconds": time.time() - task_start,
                "backend": backend,
            }
            if score.get("error"):
                entry["error"] = score["error"]
            results.append(entry)
            print(f"[Task {task_id}] score={entry['score']:.1f}/100 passed={entry['passed']}")
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        signal.signal(signal.SIGINT, old_int)
        signal.signal(signal.SIGTERM, old_term)
        report = build_report(
            backend=backend,
            model=args.model,
            context_mode=args.context_mode,
            run_id=run_id,
            results=results,
            total_elapsed=time.time() - start,
            error=error,
        )
        report["metrics"]["total_iterations"] = len(tasks) * args.max_iterations
        write_report(report_path, report)
        print(f"[报告] {report_path}")
    return 0


def _add_backend_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser], backend: str) -> None:
    parser = sub.add_parser(backend, help=f"运行 {backend} 评测")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL_NAME", "mimo-v2.5-pro"))
    parser.add_argument("--api-keys", default=str(DEFAULT_API_KEYS_FILE), help="含 base_url 列的 Markdown 密钥表路径")
    parser.add_argument("--tasks", default="0-5")
    parser.add_argument("--max-iterations", type=int, default=50)
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--context-mode", choices=["per-task", "pipeline"], default="per-task")
    parser.add_argument("--no-caching-prompt", action="store_true")
    parser.add_argument("--prompt-cache-retention", default=os.getenv("OPENHANDS_PROMPT_CACHE_RETENTION") or "24h")
    parser.set_defaults(func=run_cli_backend, backend=backend)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EvoBench internal container runner")
    sub = parser.add_subparsers(dest="runner_cmd", required=True)
    for backend in SUPPORTED_BACKENDS:
        _add_backend_parser(sub, backend)
    score = sub.add_parser("score", help="构建并评分单个 task")
    score.add_argument("--workspace", required=True)
    score.add_argument("--task", type=int, required=True)
    score.set_defaults(func=cmd_score)
    report = sub.add_parser("emit-report", help="写一个空 partial report")
    report.add_argument("--output-dir", required=True)
    report.add_argument("--model", default="")
    report.add_argument("--run-id", default="")
    report.add_argument("--context-mode", default="per-task")
    report.add_argument("--backend", default="openhands")
    report.set_defaults(func=cmd_emit_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
