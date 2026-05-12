#!/usr/bin/env python3
"""EvoBench 指标计算与 Leaderboard 生成。

指标公式:
1. Mean Reward (加权平均分):
   mean_reward = Σ(score[i] × weight[i] × bonus[i]) / Σ(weight[i])
   - weight[i] = [1.0, 2.0, 2.0, 3.0, 3.0, 4.0]  # Task 0-5 递增
   - bonus[i] = 1.2 if not resurrected else 1.0

2. Pass Score (加权通过分):
   pass_score = Σ(pass[i] × bonus_pass[i]) / (6 × 1.5) × 100
   - pass[i] = 1 if score >= 60% else 0
   - bonus_pass[i] = 1.5 if not resurrected else 1.0

用法:
    python metrics.py                     # 从 eval/results/ 收集所有结果
    python metrics.py --output site/assets/data/leaderboard.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Task 权重（递增，Task 5 最重要）
TASK_WEIGHTS = [1.0, 2.0, 2.0, 3.0, 3.0, 4.0]

# Bonus 系数
NO_RESURRECTION_BONUS = 1.2   # 直接通过 +20%
RESURRECTION_BONUS = 1.0      # 复活通过无 bonus

# Pass bonus
NO_RESURRECTION_PASS_BONUS = 1.5  # 直接通过 +50%
RESURRECTION_PASS_BONUS = 1.0     # 复活通过无 bonus

TASK_KEYS = ["task0", "task1", "task2", "task3", "task4", "task5"]


def compute_mean_reward(scores: list[float], resurrected: list[bool]) -> float:
    """计算 Mean Reward（加权平均分，含复活 bonus）。

    公式: Σ(score[i] × weight[i] × bonus[i]) / Σ(weight[i])
    """
    numerator = 0.0
    denominator = 0.0
    for i in range(6):
        weight = TASK_WEIGHTS[i]
        bonus = RESURRECTION_BONUS if resurrected[i] else NO_RESURRECTION_BONUS
        numerator += scores[i] * weight * bonus
        denominator += weight * bonus
    return numerator / denominator if denominator > 0 else 0.0


def compute_pass_score(scores: list[float], resurrected: list[bool]) -> float:
    """计算 Pass Score（加权通过分）。

    公式: Σ(pass[i] × bonus_pass[i]) / (6 × NO_RESURRECTION_PASS_BONUS) × 100
    """
    total = 0.0
    for i in range(6):
        passed = 1 if scores[i] >= 60.0 else 0
        bonus = RESURRECTION_PASS_BONUS if resurrected[i] else NO_RESURRECTION_PASS_BONUS
        total += passed * bonus
    max_possible = 6 * NO_RESURRECTION_PASS_BONUS
    return (total / max_possible) * 100.0


def parse_log_file(log_path: Path, backend: str, model: str) -> dict:
    """从日志文件解析评测结果。

    取每个 Task 的最高分（而非最后匹配），避免复活后的 0 分覆盖原始分数。
    """
    content = log_path.read_text(encoding="utf-8", errors="replace")

    # 收集每个 Task 的所有分数记录
    task_records: dict[int, list[float]] = {}
    for m in re.finditer(r"Task (\d): [✅❌] ([\d.]+)/100", content):
        task_id = int(m.group(1))
        score = float(m.group(2))
        task_records.setdefault(task_id, []).append(score)

    # 取每个 Task 的最高分
    task_scores: dict[int, float] = {}
    for task_id, records in task_records.items():
        task_scores[task_id] = max(records)

    # 修正：Task 0 是环境准备，如果其他 Task 有分数但 T0=0，设为 100
    has_other_scores = any(task_scores.get(i, 0) > 0 for i in range(1, 6))
    if has_other_scores and task_scores.get(0, 0) == 0:
        task_scores[0] = 100.0

    # 解析复活次数
    resurrection_count = len(re.findall(r"触发复活", content))

    resurrected = [False] * 6
    for task_id, records in task_records.items():
        if len(records) > 1 and task_id < 6:
            resurrected[task_id] = True

    # 填充缺失的 Task 为 0
    scores = [task_scores.get(i, 0.0) for i in range(6)]

    # 计算指标
    mean_reward = compute_mean_reward(scores, resurrected)
    pass_score = compute_pass_score(scores, resurrected)
    zero_shot_pass = all(s >= 60.0 for s in scores) and resurrection_count == 0

    return {
        "model": model,
        "backend": backend,
        "task0": scores[0],
        "task1": scores[1],
        "task2": scores[2],
        "task3": scores[3],
        "task4": scores[4],
        "task5": scores[5],
        "mean_reward": round(mean_reward, 2),
        "pass_score": round(pass_score, 2),
        "pipeline_score": round(sum(scores) / 6, 2),
        "resurrections": resurrection_count,
        "zero_shot_pass": zero_shot_pass,
        "resurrected": resurrected,
    }


def collect_results(results_dir: Path) -> list[dict]:
    """从结果目录收集所有评测结果。

    合并同一模型的多次运行（如 t4t5 重跑），取每个 Task 的最高分。
    过滤无效条目（全 0 分、太小的日志文件）。
    """
    # 模型名规范化映射
    MODEL_MAP = {
        "deepseek.v4.pro": "deepseek-v4-pro",
        "deepseek.v4.flash": "deepseek-v4-flash",
        "deepseek.chat": "deepseek-chat",
        "deepseek.reasoner": "deepseek-reasoner",
        "qwen3.6.max.preview": "qwen3.6-max-preview",
        "qwen3.6.flash": "qwen3.6-flash",
        "qwen3.6.plus": "qwen3.6-plus",
        "qwen3.coder.flash": "qwen3-coder-flash",
        "qwen3.5.plus.2026.02.15": "qwen3.5-plus-2026-02-15",
        "qwen.omni.turbo": "qwen-omni-turbo",
        "glm.5": "glm-5",
        "glm.5.1": "glm-5.1",
        "glm.4.7": "glm-4.7",
        "minimax.m2.5": "minimax-m2.5",
        "minimax.m2.7": "minimax-m2.7",
        "mimo.v2.5.pro": "mimo-v2.5-pro",
        "kimi.k2.thinking": "kimi-k2-thinking",
        "kimi.k2.6": "kimi-k2.6",
    }
    # t4t5 重跑日志名后缀，用于合并
    T4T5_SUFFIXES = ["-t4t5", ".t4t5"]

    # ── 第一步：收集所有日志条目，按模型分组 ──
    model_entries: dict[str, list[dict]] = {}  # model_name -> [entries]

    logs_dir = results_dir.parent / "logs"
    if logs_dir.exists():
        for log_file in sorted(logs_dir.glob("openhands-*.log")):
            # 跳过太小的日志（< 2KB，通常是失败的初始化）
            if log_file.stat().st_size < 2000:
                continue

            raw_name = log_file.stem.replace("openhands-", "").replace("-", ".")

            # 判断是否是 t4t5 重跑日志
            is_t4t5 = False
            for suffix in T4T5_SUFFIXES:
                if suffix in raw_name:
                    is_t4t5 = True
                    # 去掉后缀得到原始模型名
                    raw_name = raw_name.replace(suffix, "").replace(suffix.replace("-", "."), "").rstrip(".")
                    break

            model = MODEL_MAP.get(raw_name, raw_name.replace(".", "-") if raw_name not in MODEL_MAP else raw_name)
            # 额外规范化：如果映射后还有点号，转连字符
            if model not in MODEL_MAP.values():
                model = raw_name.replace(".", "-")

            entry = parse_log_file(log_file, "openhands", model)
            model_entries.setdefault(model, []).append(entry)

    # ── 第二步：合并同模型的多次运行，取每个 Task 最高分 ──
    entries = []
    for model, group in model_entries.items():
        if len(group) == 1:
            merged = group[0]
        else:
            # 合并多个条目
            best_scores = [0.0] * 6
            any_resurrected = [False] * 6
            total_resurrections = 0
            for e in group:
                for i in range(6):
                    v = e.get(f"task{i}", 0) or 0
                    if v > best_scores[i]:
                        best_scores[i] = v
                    if e.get("resurrected", [False] * 6)[i]:
                        any_resurrected[i] = True
                total_resurrections = max(total_resurrections, e.get("resurrections", 0))

            merged = {
                "model": model,
                "backend": "openhands",
                "task0": best_scores[0], "task1": best_scores[1],
                "task2": best_scores[2], "task3": best_scores[3],
                "task4": best_scores[4], "task5": best_scores[5],
                "resurrected": any_resurrected,
                "resurrections": total_resurrections,
            }
            merged["mean_reward"] = round(compute_mean_reward(best_scores, any_resurrected), 2)
            merged["pass_score"] = round(compute_pass_score(best_scores, any_resurrected), 2)
            merged["pipeline_score"] = round(sum(best_scores) / 6, 2)
            merged["zero_shot_pass"] = all(s >= 60.0 for s in best_scores) and not any(any_resurrected)

        # 过滤全 0 分的条目
        scores = [merged.get(f"task{i}", 0) for i in range(6)]
        if all(s == 0 for s in scores):
            continue
        entries.append(merged)

    # ── 第三步：从 CLI 报告解析（取最高分条目） ──
    cli_model_best: dict[str, dict] = {}  # model_name -> best entry
    for report_file in sorted(results_dir.glob("cli_*_report.json")):
        try:
            data = json.loads(report_file.read_text())
            backend = data.get("agent_backend", "unknown")
            model_name = data.get("model", f"mimo-v2.5-pro ({backend})")

            task_scores = [0.0] * 6
            resurrected = [False] * 6
            for t in data.get("tasks", []):
                tid = t["task_id"]
                if tid < 6:
                    score = t.get("score", 0)
                    if score > task_scores[tid]:
                        task_scores[tid] = score
                    if t.get("resurrected"):
                        resurrected[tid] = True

            # 跳过全 0 分
            if all(s == 0 for s in task_scores):
                continue

            entry = {
                "model": model_name,
                "backend": backend,
                "task0": task_scores[0], "task1": task_scores[1],
                "task2": task_scores[2], "task3": task_scores[3],
                "task4": task_scores[4], "task5": task_scores[5],
                "mean_reward": round(compute_mean_reward(task_scores, resurrected), 2),
                "pass_score": round(compute_pass_score(task_scores, resurrected), 2),
                "pipeline_score": round(sum(task_scores) / 6, 2),
                "resurrections": sum(1 for r in resurrected if r),
                "zero_shot_pass": all(s >= 60.0 for s in task_scores) and not any(resurrected),
                "resurrected": resurrected,
            }

            # 对于同一模型+backend，保留最高 mean_reward 的
            key = f"{model_name}@{backend}"
            if key not in cli_model_best or entry["mean_reward"] > cli_model_best[key]["mean_reward"]:
                cli_model_best[key] = entry
        except Exception as e:
            print(f"Warning: Failed to parse {report_file}: {e}")

    entries.extend(cli_model_best.values())

    # ── 第四步：手动注入特殊条目（Codex gpt-5.5 等） ──
    # Codex gpt-5.5 数据来自手动评测日志
    MANUALLY_INJECTED = {
        "gpt-5.5@codex": {
            "model": "gpt-5.5", "backend": "codex",
            "task0": 100.0, "task1": 100.0, "task2": 100.0,
            "task3": 100.0, "task4": 95.0, "task5": 100.0,
        },
    }
    existing_keys = {f"{e['model']}@{e.get('backend', 'openhands')}" for e in entries}
    for key, data in MANUALLY_INJECTED.items():
        if key not in existing_keys:
            scores = [data.get(f"task{i}", 0) for i in range(6)]
            res = [False] * 6
            entry = {
                **data,
                "mean_reward": round(compute_mean_reward(scores, res), 2),
                "pass_score": round(compute_pass_score(scores, res), 2),
                "pipeline_score": round(sum(scores) / 6, 2),
                "resurrections": 0,
                "zero_shot_pass": all(s >= 60 for s in scores),
                "resurrected": res,
            }
            entries.append(entry)

    return entries


def generate_leaderboard(entries: list[dict], output_path: Path) -> None:
    """生成 Leaderboard JSON。"""
    # 按 mean_reward 降序排序
    entries.sort(key=lambda e: e.get("mean_reward", 0), reverse=True)

    # 添加排名
    for i, entry in enumerate(entries):
        entry["rank"] = i + 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2))
    print(f"Leaderboard 已生成: {output_path} ({len(entries)} 条记录)")


def main():
    parser = argparse.ArgumentParser(description="EvoBench 指标计算")
    parser.add_argument("--results-dir", default="eval/results",
                        help="评测结果目录")
    parser.add_argument("--output", default="site/assets/data/leaderboard.json",
                        help="Leaderboard 输出路径")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"结果目录不存在: {results_dir}")
        sys.exit(1)

    entries = collect_results(results_dir)

    if not entries:
        print("没有找到评测结果")
        sys.exit(1)

    # 打印摘要
    print(f"\n{'='*80}")
    print(f"  EvoBench Leaderboard ({len(entries)} models)")
    print(f"{'='*80}")
    print(f"{'Rank':<5} {'Model':<30} {'Mean Reward':<12} {'Pass Score':<11} {'Pipeline':<9} {'🔄':<4}")
    print(f"{'-'*5} {'-'*30} {'-'*12} {'-'*11} {'-'*9} {'-'*4}")

    entries.sort(key=lambda e: e.get("mean_reward", 0), reverse=True)
    for i, e in enumerate(entries):
        print(f"{i+1:<5} {e['model']:<30} {e.get('mean_reward',0):<12.2f} "
              f"{e.get('pass_score',0):<11.2f} {e.get('pipeline_score',0):<9.2f} "
              f"{e.get('resurrections',0):<4}")

    print(f"{'='*80}\n")

    generate_leaderboard(entries, Path(args.output))


if __name__ == "__main__":
    main()
