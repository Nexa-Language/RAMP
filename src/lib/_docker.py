from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class DockerResult:
    returncode: int
    stdout: str
    stderr: str


def run_docker(args: list[str], *, check: bool = False, timeout: int | None = None) -> DockerResult:
    proc = subprocess.run(
        ["docker", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"docker {' '.join(args)} failed")
    return DockerResult(proc.returncode, proc.stdout, proc.stderr)


def container_name(run_id: str) -> str:
    return f"oh-{run_id}"


def inspect_container(name: str) -> dict | None:
    result = run_docker(["inspect", name])
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if isinstance(data, list) and data:
        return data[0]
    return None


def container_status(name: str) -> str:
    data = inspect_container(name)
    state = data.get("State") if isinstance(data, dict) else None
    if isinstance(state, dict):
        return str(state.get("Status") or "")
    return ""


def remove_container(name: str) -> None:
    run_docker(["rm", "-f", name])


def stop_container(name: str) -> None:
    run_docker(["stop", name])


def wait_container(name: str) -> int:
    result = run_docker(["wait", name], check=False)
    try:
        return int(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return result.returncode
