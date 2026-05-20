#!/usr/bin/env python3
"""Extract process metrics from RAMP logs and leaderboard data.

Outputs a structured JSON file suitable for paper tables and figures.
"""

import json
import re
import os
from pathlib import Path
from collections import defaultdict

# Paths
LEADERBOARD_PATH = Path("site/assets/data/leaderboard.json")
LOGS_DIR = Path("eval/logs")
OUTPUT_PATH = Path("RAMP-paper/results/process_metrics.json")

# Mapping from log filename patterns to leaderboard model names
LOG_TO_MODEL = {
    "openhands-deepseek-chat": "deepseek-chat",
    "openhands-deepseek-reasoner": "deepseek-reasoner",
    "openhands-deepseek-v4-flash": "deepseek-v4-flash",
    "openhands-deepseek-v4-pro": "deepseek-v4-pro",
    "openhands-glm-4-7": "glm-4.7",
    "openhands-glm-5-1": "glm-5.1",
    "openhands-glm-5": "glm-5",
    "openhands-qwen-omni-turbo": "qwen-omni-turbo",
    "openhands-qwen3-5-plus-2026-02-15": "qwen3.5-plus-2026-02-15",
    "openhands-qwen3-6-flash": "qwen3.6-flash",
    "openhands-qwen3-6-max-preview": "qwen3.6-max-preview",
    "openhands-qwen3-6-plus": "qwen3.6-plus",
    "openhands-qwen3-coder-flash": "qwen3-coder-flash",
    "openhands-kimi-k2-thinking": "kimi-k2-thinking",
    "openhands-minimax-m2-5": "minimax-m2.5",
    "openhands-minimax-m2-7": "minimax-m2.7",
    "openhands-mimo-v2-5-pro": "mimo-v2.5-pro",
    "codex-gpt5.5": "gpt-5.5",
    "claude-sonnet-4.6": "claude-sonnet-4.6",
    "cli-kimi-k2.5": "kimi-k2.5",
    "cli-kimi-k2.6": "kimi-k2.6",
    "cli-mimo-v2.5-pro": "mimo-v2.5-pro",
}


def parse_log_for_metrics(log_path: Path) -> dict:
    """Parse a CLI agent log file for token/turn/retry metrics."""
    try:
        content = log_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}
    
    # Count build attempts
    build_count = len(re.findall(r"cmake --build", content))
    
    # Count test/score attempts
    score_count = len(re.findall(r"task\d+-score|task\d+-classic-score", content))
    
    # Count resurrection triggers
    resurrection_count = len(re.findall(r"触发复活|RESURRECT|resurrection", content))
    
    # Extract elapsed time mentions
    elapsed_matches = re.findall(r"耗时[:\s]*([\d.]+)\s*s|elapsed[:\s]*([\d.]+)\s*s", content)
    total_elapsed = 0
    for m in elapsed_matches:
        for g in m:
            if g:
                try:
                    total_elapsed += float(g)
                except ValueError:
                    pass
    
    # Count shell commands (rc= patterns from OpenAI backend)
    shell_count = len(re.findall(r"\[rc=\d+\]", content))
    
    # Count error patterns
    build_errors = len(re.findall(r"构建失败|build error|Build Error|ninja: build FAILED", content))
    timeout_errors = len(re.findall(r"超时|Timeout|timeout", content))
    max_turn_errors = len(re.findall(r"max turns|Reached max turns|max_iterations", content))
    
    # Extract token mentions
    token_matches = re.findall(r"tokens[:\s]*([\d,]+)", content)
    total_tokens = 0
    for t in token_matches:
        cleaned = t.replace(",", "").strip()
        if cleaned and cleaned.isdigit():
            total_tokens += int(cleaned)
    
    # Extract turn mentions
    turn_matches = re.findall(r"轮次[:\s]*([\d]+)|turns[:\s]*([\d]+)|iterations[:\s]*([\d]+)", content)
    total_turns = 0
    for m in turn_matches:
        for g in m:
            if g and g.isdigit():
                total_turns += int(g)
    
    # Extract per-task scores from log
    task_scores = {}
    score_patterns = re.findall(r"Task (\d+).*?([\d.]+)/100", content)
    for task_id, score in score_patterns:
        task_scores[int(task_id)] = float(score)
    
    # Also look for score.json patterns
    score_json_patterns = re.findall(r"Task (\d+).*?✅.*?([\d.]+)/100", content)
    for task_id, score in score_json_patterns:
        task_scores[int(task_id)] = float(score)
    
    return {
        "build_count": build_count,
        "score_count": score_count,
        "resurrection_count": resurrection_count,
        "total_elapsed_seconds": total_elapsed,
        "shell_count": shell_count,
        "build_errors": build_errors,
        "timeout_errors": timeout_errors,
        "max_turn_errors": max_turn_errors,
        "total_tokens": total_tokens,
        "total_turns": total_turns,
        "task_scores_from_log": task_scores,
    }


def match_log_to_model(log_name: str) -> str:
    """Match a log filename to a leaderboard model name."""
    # Remove timestamp suffixes like -1778578605
    clean = re.sub(r"-[\d]{6,}", "", log_name)
    # Remove -v2, -v3 suffixes
    clean = re.sub(r"-v\d+$", "", clean)
    # Remove -t4t5 suffix
    clean = re.sub(r"-t4t5$", "", clean)
    # Remove task-specific suffixes
    clean = re.sub(r"-task\d+$", "", clean)
    # Remove -task0-5 suffix
    clean = re.sub(r"-task\d+-\d+$", "", clean)
    
    # Direct lookup
    if clean in LOG_TO_MODEL:
        return LOG_TO_MODEL[clean]
    
    # Try partial match
    for pattern, model in LOG_TO_MODEL.items():
        if clean.startswith(pattern) or pattern.startswith(clean):
            return model
    
    return None


def main():
    # Load leaderboard data
    leaderboard = json.loads(LEADERBOARD_PATH.read_text())
    
    # Build per-model result structure
    results = {}
    for entry in leaderboard:
        model = entry["model"]
        backend = entry["backend"]
        key = f"{model}/{backend}"
        results[key] = {
            "model": model,
            "backend": backend,
            "task0": entry.get("task0", 0),
            "task1": entry.get("task1", 0),
            "task2": entry.get("task2", 0),
            "task3": entry.get("task3", 0),
            "task4": entry.get("task4", 0),
            "task5": entry.get("task5", 0),
            "mean_reward": entry.get("mean_reward", 0),
            "pass_score": entry.get("pass_score", 0),
            "pipeline_score": entry.get("pipeline_score", 0),
            "resurrections": entry.get("resurrections", 0),
            "zero_shot_pass": entry.get("zero_shot_pass", False),
            "resurrected": entry.get("resurrected", [False]*6),
            "rank": entry.get("rank", 0),
            "process_metrics": {
                "total_tokens": 0,
                "total_turns": 0,
                "build_count": 0,
                "score_count": 0,
                "shell_count": 0,
                "total_elapsed_seconds": 0,
                "build_errors": 0,
                "timeout_errors": 0,
                "max_turn_errors": 0,
            }
        }
    
    # Parse log files for process metrics
    log_files = list(LOGS_DIR.glob("*.log"))
    print(f"Found {len(log_files)} log files")
    
    matched = 0
    unmatched = 0
    
    for log_path in log_files:
        log_name = log_path.stem
        model_name = match_log_to_model(log_name)
        
        if model_name is None:
            unmatched += 1
            continue
        
        # Find matching leaderboard entry
        matching_keys = [k for k in results if results[k]["model"] == model_name]
        if not matching_keys:
            unmatched += 1
            continue
        
        metrics = parse_log_for_metrics(log_path)
        if not metrics:
            continue
        
        matched += 1
        
        # Aggregate process metrics across all matching logs
        for key in matching_keys:
            pm = results[key]["process_metrics"]
            pm["build_count"] += metrics.get("build_count", 0)
            pm["score_count"] += metrics.get("score_count", 0)
            pm["shell_count"] += metrics.get("shell_count", 0)
            pm["build_errors"] += metrics.get("build_errors", 0)
            pm["timeout_errors"] += metrics.get("timeout_errors", 0)
            pm["max_turn_errors"] += metrics.get("max_turn_errors", 0)
            pm["total_tokens"] += metrics.get("total_tokens", 0)
            pm["total_turns"] += metrics.get("total_turns", 0)
            if metrics.get("total_elapsed_seconds", 0) > pm["total_elapsed_seconds"]:
                pm["total_elapsed_seconds"] = metrics.get("total_elapsed_seconds", 0)
    
    # Also load the OpenAI API run report which has detailed token/turn data
    api_report_path = Path("ramp_output/ramp_report.json")
    if api_report_path.exists():
        api_report = json.loads(api_report_path.read_text())
        model = api_report.get("agent_model", "unknown")
        backend = api_report.get("agent_backend", "unknown")
        key = f"{model}/{backend}"
        
        if key in results:
            agent_details = api_report.get("agent_details", [])
            total_tokens = sum(a.get("total_tokens", 0) for a in agent_details)
            total_turns = sum(a.get("turns", 0) for a in agent_details)
            total_elapsed = api_report.get("total_elapsed_seconds", 0)
            
            results[key]["process_metrics"]["total_tokens"] = total_tokens
            results[key]["process_metrics"]["total_turns"] = total_turns
            results[key]["process_metrics"]["total_elapsed_seconds"] = total_elapsed
    
    print(f"Matched {matched} logs, unmatched {unmatched}")
    
    # Save results
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Saved process metrics to {OUTPUT_PATH}")
    
    # Print summary table
    print("\n=== Process Metrics Summary ===")
    print(f"{'Model/Backend':<35} {'Tokens':>10} {'Turns':>8} {'Elapsed':>10} {'Builds':>8} {'Scores':>8} {'Shell':>8}")
    for key, data in sorted(results.items(), key=lambda x: x[1].get("rank", 99)):
        pm = data.get("process_metrics", {})
        print(f"{key:<35} {pm.get('total_tokens',0):>10} {pm.get('total_turns',0):>8} "
              f"{pm.get('total_elapsed_seconds',0):>10.1f} {pm.get('build_count',0):>8} "
              f"{pm.get('score_count',0):>8} {pm.get('shell_count',0):>8}")


if __name__ == "__main__":
    main()