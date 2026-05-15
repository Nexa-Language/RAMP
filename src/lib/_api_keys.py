from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ApiKeyEntry:
    name: str
    model: str
    key: str


def load_api_keys(path: Path) -> list[ApiKeyEntry]:
    if not path.is_file():
        raise FileNotFoundError(f"找不到 API key 文件: {path}")
    entries: list[ApiKeyEntry] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line.startswith("|") or "---" in line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 5:
            continue
        name, model, key = parts[1], parts[2], parts[3]
        if name and model and key.startswith("sk-"):
            entries.append(ApiKeyEntry(name=name, model=model, key=key))
    if not entries:
        raise ValueError(f"API key 文件中没有可用 key: {path}")
    return entries


def select_api_key(entries: list[ApiKeyEntry], model: str) -> ApiKeyEntry:
    for entry in entries:
        if entry.model == model:
            return entry
    for entry in entries:
        if entry.name.startswith(f"{model}-") or entry.model.startswith(f"{model}-"):
            return entry
    for entry in entries:
        if entry.model == "all":
            return entry
    raise KeyError(f"模型 {model} 找不到匹配 key，也没有 all fallback")
