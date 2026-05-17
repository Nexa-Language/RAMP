from __future__ import annotations

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
DEFAULT_API_KEYS_FILE = ROOT / "_api_keys.local.md"
DEFAULT_IMAGE = "evobench-openhands:latest"


def output_prefix_for_context(context_mode: str, root: Path = ROOT) -> Path:
    suffix = "pipeline" if context_mode == "pipeline" else "per-task"
    return root / "eval" / f"container-runs-summary-{suffix}"
