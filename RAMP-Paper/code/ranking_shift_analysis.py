#!/usr/bin/env python3
"""Compute ranking shift analysis for RAMP paper.

Compares serial ranking (no-resurrection pipeline depth) vs 
independent-task ranking (average per-task score with resurrection).
"""

import json
import numpy as np
from pathlib import Path
from scipy import stats

LEADERBOARD_PATH = Path("site/assets/data/leaderboard.json")
OUTPUT_DIR = Path("RAMP-paper/results")

def main():
    leaderboard = json.loads(LEADERBOARD_PATH.read_text())
    
    # Compute two rankings:
    # 1. Serial strict: no-resurrection pipeline depth (how far agent goes without help)
    # 2. Independent-task proxy: average per-task score (with resurrection = golden prerequisites)
    
    serial_scores = []  # no-resurrection pipeline depth
    independent_scores = []  # average per-task score (resurrection provides golden prerequisites)
    models = []
    
    for entry in leaderboard:
        model = entry["model"]
        models.append(model)
        
        # Per-task scores (with resurrection, these represent independent-task capability)
        task_scores = [entry.get(f"task{i}", 0) for i in range(6)]
        avg_score = np.mean(task_scores)
        independent_scores.append(avg_score)
        
        # No-resurrection pipeline depth: how far can agent go without resurrection
        depth = 0
        for s in task_scores:
            if s >= 60:
                depth += 1
            else:
                break
        # Convert depth to a score: depth/6 * 100
        serial_score = depth / 6 * 100
        serial_scores.append(serial_score)
    
    # Compute rankings
    serial_rank = stats.rankdata([-s for s in serial_scores])  # rank by descending score
    independent_rank = stats.rankdata([-s for s in independent_scores])
    
    # Compute correlation
    kendall_tau, kendall_p = stats.kendalltau(serial_rank, independent_rank)
    spearman_rho, spearman_p = stats.spearmanr(serial_scores, independent_scores)
    
    # Find models with significant rank shifts
    rank_shifts = []
    for i, model in enumerate(models):
        shift = independent_rank[i] - serial_rank[i]
        if abs(shift) >= 3:
            rank_shifts.append({
                "model": model,
                "serial_rank": int(serial_rank[i]),
                "independent_rank": int(independent_rank[i]),
                "shift": int(shift),
                "serial_score": serial_scores[i],
                "independent_score": independent_scores[i],
            })
    
    # Print results
    print("=== Ranking Shift Analysis ===")
    print(f"Kendall tau: {kendall_tau:.3f} (p={kendall_p:.4f})")
    print(f"Spearman rho: {spearman_rho:.3f} (p={spearman_p:.4f})")
    print(f"\nModels with rank shift >= 3:")
    for rs in rank_shifts:
        direction = "↑" if rs["shift"] > 0 else "↓"
        print(f"  {rs['model']}: serial_rank={rs['serial_rank']}, independent_rank={rs['independent_rank']}, shift={direction}{abs(rs['shift'])}")
        print(f"    serial_score={rs['serial_score']:.1f}, independent_score={rs['independent_score']:.1f}")
    
    print(f"\n=== Full Ranking Comparison ===")
    print(f"{'Model':<25} {'SerialRank':>10} {'IndepRank':>10} {'Shift':>8} {'SerialScore':>12} {'IndepScore':>12}")
    for i, model in enumerate(models):
        shift = int(independent_rank[i] - serial_rank[i])
        direction = "↑" if shift > 0 else "↓" if shift < 0 else "="
        print(f"{model:<25} {int(serial_rank[i]):>10} {int(independent_rank[i]):>10} {direction}{abs(shift):>7} {serial_scores[i]:>12.1f} {independent_scores[i]:>12.1f}")
    
    # Save results
    output = {
        "kendall_tau": kendall_tau,
        "kendall_p": kendall_p,
        "spearman_rho": spearman_rho,
        "spearman_p": spearman_p,
        "models": models,
        "serial_scores": serial_scores,
        "independent_scores": independent_scores,
        "serial_rank": [int(r) for r in serial_rank],
        "independent_rank": [int(r) for r in independent_rank],
        "rank_shifts": rank_shifts,
    }
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_DIR / "ranking_shift_analysis.json").write_text(json.dumps(output, indent=2))
    print(f"\nSaved ranking_shift_analysis.json")


if __name__ == "__main__":
    main()