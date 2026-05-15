from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from core.summarize import collect_one
from lib import _docker
from lib._paths import DEFAULT_RUNS_DIR


@dataclass(frozen=True)
class RunTrace:
    run_id: str
    output_dir: str
    output_dir_exists: bool
    container: str
    container_exists: bool
    container_status: str
    termination_status: str = ""
    termination_reason: str = ""

    @property
    def has_conflict(self) -> bool:
        return self.output_dir_exists or self.container_exists


def trace_run(run_id: str, runs_dir: Path = DEFAULT_RUNS_DIR) -> RunTrace:
    output_dir = runs_dir / run_id
    container = _docker.container_name(run_id)
    data = _docker.inspect_container(container)
    termination_status = ""
    termination_reason = ""
    if output_dir.is_dir():
        row = collect_one(output_dir, include_tokens=False)
        termination_status = str(row.get("termination_status", ""))
        termination_reason = str(row.get("termination_reason", ""))
    return RunTrace(
        run_id=run_id,
        output_dir=str(output_dir),
        output_dir_exists=output_dir.is_dir(),
        container=container,
        container_exists=data is not None,
        container_status=_docker.container_status(container) if data else "",
        termination_status=termination_status,
        termination_reason=termination_reason,
    )


def list_traces(runs_dir: Path = DEFAULT_RUNS_DIR) -> list[RunTrace]:
    traces: list[RunTrace] = []
    if runs_dir.is_dir():
        for path in sorted(runs_dir.iterdir()):
            if path.is_dir():
                traces.append(trace_run(path.name, runs_dir))
    return traces


def check_conflicts(run_ids: list[str], runs_dir: Path = DEFAULT_RUNS_DIR) -> list[RunTrace]:
    return [trace for trace in (trace_run(run_id, runs_dir) for run_id in run_ids) if trace.has_conflict]


def delete_trace(run_id: str, runs_dir: Path = DEFAULT_RUNS_DIR, *, force: bool = False) -> RunTrace:
    trace = trace_run(run_id, runs_dir)
    if not force:
        answer = input(f"将删除容器 {trace.container} 和目录 {trace.output_dir}，确认? [y/N] ")
        if answer.strip().lower() not in {"y", "yes"}:
            raise RuntimeError("用户取消删除")
    if trace.container_exists:
        _docker.remove_container(trace.container)
    if trace.output_dir_exists:
        shutil.rmtree(trace.output_dir)
    return trace


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("job_manage", help="管理 run_id 容器和输出目录")
    sub = parser.add_subparsers(dest="job_cmd", required=True)
    show = sub.add_parser("show", help="展示 run 痕迹")
    show.add_argument("run_id", nargs="?")
    show.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR))
    show.set_defaults(func=cmd_show)
    list_cmd = sub.add_parser("list", help="列出 run 痕迹")
    list_cmd.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR))
    list_cmd.set_defaults(func=cmd_show)
    delete = sub.add_parser("delete", help="删除指定 run 痕迹")
    delete.add_argument("run_id")
    delete.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR))
    delete.add_argument("--force", action="store_true")
    delete.set_defaults(func=cmd_delete)
    conflicts = sub.add_parser("conflicts", help="检查 run_id 冲突")
    conflicts.add_argument("--run-id", action="append", required=True)
    conflicts.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR))
    conflicts.set_defaults(func=cmd_conflicts)


def cmd_show(args: argparse.Namespace) -> int:
    runs_dir = Path(args.runs_dir)
    if getattr(args, "run_id", None):
        data = asdict(trace_run(args.run_id, runs_dir))
    else:
        data = [asdict(trace) for trace in list_traces(runs_dir)]
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    trace = delete_trace(args.run_id, Path(args.runs_dir), force=args.force)
    print(json.dumps(asdict(trace), ensure_ascii=False, indent=2))
    return 0


def cmd_conflicts(args: argparse.Namespace) -> int:
    conflicts = check_conflicts(args.run_id, Path(args.runs_dir))
    print(json.dumps([asdict(trace) for trace in conflicts], ensure_ascii=False, indent=2))
    return 1 if conflicts else 0
