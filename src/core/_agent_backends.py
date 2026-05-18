from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from lib._agent_events import append_agent_event
from lib._kimi_stream_json import kimi_stream_json_assistant_lines


SUPPORTED_BACKENDS = ("openhands", "kimi", "claude", "codex")


@dataclass(frozen=True)
class BackendContext:
    backend: str
    model: str
    api_key: str
    api_base: str
    workspace: Path
    output_dir: Path
    run_id: str
    max_iterations: int
    context_mode: str = "per-task"


def ensure_backend(name: str) -> str:
    if name not in SUPPORTED_BACKENDS:
        raise ValueError(f"不支持的 backend: {name}，可选: {', '.join(SUPPORTED_BACKENDS)}")
    return name


def _base_env(ctx: BackendContext) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "OPENAI_API_KEY": ctx.api_key,
            "OPENAI_BASE_URL": ctx.api_base,
            "OPENAI_API_BASE": ctx.api_base,
        }
    )
    return env


def _run_command(
    ctx: BackendContext,
    task_id: int,
    command: list[str],
    env: dict[str, str],
    *,
    llm_step_budget: int | None = None,
    pipeline_stage: str | None = None,
) -> None:
    event_path = ctx.output_dir / "agent-events" / f"task{task_id}.jsonl"
    start_payload: dict = {
        "event_type": "agent_start",
        "backend": ctx.backend,
        "task_id": task_id,
        "command": command[:2],
        "context_mode": ctx.context_mode,
        "pipeline_stage": pipeline_stage,
    }
    if llm_step_budget is not None:
        start_payload["llm_step_budget"] = llm_step_budget
    append_agent_event(event_path, start_payload)
    if ctx.backend == "kimi":
        sub_timeout: int | None = None
    elif ctx.max_iterations > 0:
        sub_timeout = ctx.max_iterations * 300
    else:
        sub_timeout = None
    proc = subprocess.run(
        command,
        cwd=ctx.workspace,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=sub_timeout,
    )
    out = proc.stdout or ""
    if ctx.backend == "kimi" and out.strip():
        assistant_lines = kimi_stream_json_assistant_lines(out)
        if assistant_lines:
            for i, snippet in enumerate(assistant_lines):
                append_agent_event(
                    event_path,
                    {
                        "event_type": "llm_response",
                        "backend": ctx.backend,
                        "task_id": task_id,
                        "llm_response_id": str(uuid.uuid4()),
                        "kimi_stream_json": True,
                        "kimi_assistant_index": i,
                        "message": snippet[:12000],
                    },
                )
        else:
            append_agent_event(
                event_path,
                {
                    "event_type": "llm_response",
                    "backend": ctx.backend,
                    "task_id": task_id,
                    "llm_response_id": str(uuid.uuid4()),
                    "kimi_stream_json": False,
                    "message": out[-8000:],
                },
            )
    elif out:
        append_agent_event(
            event_path,
            {
                "event_type": "llm_response",
                "backend": ctx.backend,
                "task_id": task_id,
                "llm_response_id": str(uuid.uuid4()),
                "message": out[-8000:],
            },
        )
    if proc.stderr:
        append_agent_event(
            event_path,
            {
                "event_type": "agent_stderr",
                "backend": ctx.backend,
                "task_id": task_id,
                "detail": proc.stderr[-8000:],
            },
        )
    append_agent_event(
        event_path,
        {
            "event_type": "agent_exit",
            "backend": ctx.backend,
            "task_id": task_id,
            "returncode": proc.returncode,
        },
    )
    if proc.returncode != 0:
        append_agent_event(
            event_path,
            {
                "event_type": "error",
                "backend": ctx.backend,
                "task_id": task_id,
                "code": f"{ctx.backend}.exit_{proc.returncode}",
                "kind": "AgentProcessError",
                "detail": (proc.stderr or proc.stdout)[-8000:],
            },
        )
        raise RuntimeError(f"{ctx.backend} backend exited with {proc.returncode}")


def run_cli_backend_task(
    ctx: BackendContext,
    task_id: int,
    prompt: str,
    *,
    llm_step_budget: int | None = None,
    pipeline_stage: str | None = None,
) -> None:
    ensure_backend(ctx.backend)
    if ctx.backend == "openhands":
        raise ValueError("OpenHands backend is handled by the OpenHands SDK runner")
    env = _base_env(ctx)
    if ctx.backend == "claude":
        if shutil.which("cc-switch") is None:
            raise RuntimeError("Claude backend 需要镜像内安装 cc-switch 以适配 OpenAI-compatible 协议")
        if shutil.which("claude") is None:
            raise RuntimeError("Claude backend 需要镜像内安装 Claude Code CLI: claude")
        # Claude Code must reach OpenAI-compatible gateways through cc-switch.
        env.update(
            {
                "ANTHROPIC_MODEL": ctx.model,
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
                "DISABLE_AUTOUPDATER": "1",
            }
        )
        cc_home = ctx.output_dir / "agent-state" / "claude" / "cc-switch"
        claude_home = ctx.output_dir / "agent-state" / "claude" / "claude"
        cc_home.mkdir(parents=True, exist_ok=True)
        claude_home.mkdir(parents=True, exist_ok=True)
        env["CC_SWITCH_HOME"] = str(cc_home)
        env["CLAUDE_CONFIG_DIR"] = str(claude_home)
        env["CC_SWITCH_OPENAI_BASE_URL"] = ctx.api_base
        env["CC_SWITCH_OPENAI_API_KEY"] = ctx.api_key
        env["CC_SWITCH_MODEL"] = ctx.model
        command = [
            "claude",
            "--bare",
            "-p",
            prompt,
            "--allowedTools",
            "Read,Edit,Write,Bash,Glob,Grep",
            "--max-turns",
            str(max(ctx.max_iterations, 1)),
        ]
    elif ctx.backend == "codex":
        if shutil.which("codex") is None:
            raise RuntimeError("Codex backend 需要镜像内安装 Codex CLI: codex")
        codex_home = ctx.output_dir / "agent-state" / "codex"
        codex_home.mkdir(parents=True, exist_ok=True)
        env["CODEX_HOME"] = str(codex_home)
        config = codex_home / "config.toml"
        config.write_text(
            "\n".join(
                [
                    f'model = "{ctx.model}"',
                    'model_provider = "evobench"',
                    'approval_policy = "never"',
                    '[model_providers.evobench]',
                    'name = "EvoBench OpenAI-compatible"',
                    f'base_url = "{ctx.api_base}"',
                    'env_key = "OPENAI_API_KEY"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        command = ["codex", "exec", "--sandbox", "workspace-write", "--json", prompt]
    elif ctx.backend == "kimi":
        if shutil.which("kimi") is None:
            raise RuntimeError("Kimi backend 需要镜像内安装 Kimi Code CLI: kimi")
        kimi_home = ctx.output_dir / "agent-state" / "kimi"
        kimi_home.mkdir(parents=True, exist_ok=True)
        env.update(
            {
                "KIMI_SHARE_DIR": str(kimi_home),
                "KIMI_CLI_NO_AUTO_UPDATE": "1",
                "KIMI_API_KEY": ctx.api_key,
                "KIMI_BASE_URL": ctx.api_base,
                "KIMI_MODEL_NAME": ctx.model,
            }
        )
        step_cap = max(1, llm_step_budget) if llm_step_budget is not None else max(ctx.max_iterations, 1)
        command = [
            "kimi",
            "--print",
            "-p",
            prompt,
            "--output-format=stream-json",
            "--max-steps-per-turn",
            str(step_cap),
        ]
    else:
        raise ValueError(f"不支持的 CLI backend: {ctx.backend}")
    _run_command(
        ctx,
        task_id,
        command,
        env,
        llm_step_budget=llm_step_budget,
        pipeline_stage=pipeline_stage,
    )
