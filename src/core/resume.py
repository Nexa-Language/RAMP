from __future__ import annotations

import argparse
from pathlib import Path

from core.job_manage import trace_run
from core.summarize import collect_one
from lib import _docker
from lib._paths import DEFAULT_RUNS_DIR


def resume_run(run_id: str, runs_dir: Path = DEFAULT_RUNS_DIR, *, dry_run: bool = False) -> int:
    trace = trace_run(run_id, runs_dir)
    if not trace.output_dir_exists:
        print(f"找不到输出目录: {trace.output_dir}")
        return 2
    row = collect_one(Path(trace.output_dir))
    if str(row.get("termination_status", "")).startswith("success_"):
        print(f"{run_id} 已正常结束，不需要断点重续。")
        return 0
    print(
        f"run_id={run_id} status={row.get('termination_status')} "
        f"remaining_iterations={row.get('remaining_iterations')} container={trace.container_status}"
    )
    if dry_run:
        return 0
    if not trace.container_exists:
        print("容器不存在，无法按计划复用同一容器续跑。")
        return 2
    result = _docker.run_docker(["start", "-a", trace.container], check=False)
    (Path(trace.output_dir) / "resume_exit_code").write_text(str(result.returncode), encoding="utf-8")
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("resume", help="复用已有容器和输出目录续跑异常 run")
    parser.add_argument("run_id")
    parser.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR))
    parser.add_argument("--max-iterations", type=int, default=0, help="预留参数：当前实现优先复用原容器命令")
    parser.add_argument("--max-agent-hours", type=int, default=0, help="预留参数：当前实现优先复用原容器命令")
    parser.add_argument("--dry-run", action="store_true")
    parser.set_defaults(func=cmd_resume)


def cmd_resume(args: argparse.Namespace) -> int:
    return resume_run(args.run_id, Path(args.runs_dir), dry_run=args.dry_run)
