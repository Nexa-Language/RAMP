from __future__ import annotations

import os
from pathlib import Path


def find_repo_root(start: Path | str | None = None) -> Path:
    """Find the EvoBench repository root from a starting path."""
    cur = Path(start or __file__).resolve()
    if cur.is_file():
        cur = cur.parent
    for path in (cur, *cur.parents):
        if (path / "models.json").is_file() and (path / "data" / "YatCC").is_dir():
            return path
    raise FileNotFoundError("无法定位 EvoBench 项目根目录")


ROOT = find_repo_root()
DEFAULT_RUNS_DIR = ROOT / "eval" / "container-runs"
DEFAULT_SUMMARY_PREFIX = ROOT / "eval" / "container-runs-summary"
DEFAULT_MODELS_FILE = ROOT / "models.json"
DEFAULT_API_KEYS_FILE = ROOT / "api_keys.local.md"
DEFAULT_IMAGE = "evobench-openhands:latest"


def load_api_base(root: Path = ROOT, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    if os.getenv("OPENAI_API_BASE"):
        return os.environ["OPENAI_API_BASE"]
    env_path = root / ".env"
    if env_path.is_file():
        for raw in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "OPENAI_API_BASE":
                return value.strip().strip("'\"")
    return "https://aihub.arcsysu.cn/v1"


def output_prefix_for_context(context_mode: str, root: Path = ROOT) -> Path:
    suffix = "pipeline" if context_mode == "pipeline" else "per-task"
    return root / "eval" / f"container-runs-summary-{suffix}"
