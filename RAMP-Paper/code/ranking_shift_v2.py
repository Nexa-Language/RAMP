#!/usr/bin/env python3
"""Compute refined ranking shift analysis using no-resurrection pipeline score.

Instead of coarse pipeline depth, compute a "no-resurrection pipeline score" 
that uses actual task scores but stops accumulating after the first failure < 60.
"""

import json
import numpy as np
from pathlib import Path
from scipy import stats

LEADERBOARD_PATH = Path("site/assets/data/leaderboard.json")
OUTPUT_DIR = Path("RAMP-paper/results")

# Task weights (same as in evaluation protocol)
WEIGHTS = [0.05, 0.20, 0.20, 0.15, 0.30, 0.10]

def main():
    leaderboard = json.loads(LEADERBOARD_PATH.read_text())
    
    # Compute three rankings:
    # 1. No-resurrection pipeline score: weighted sum of scores, stops at first failure
    # 2. With-resurrection pipeline score: weighted sum of all scores (current leaderboard)
    # 3. Independent-task average: simple average of per-task scores
    
    no_res_scores = []
    with_res_scores = []
    independent_scores = []
    models = []
    
    for entry in leaderboard:
        model = entry["model"]
        models.append(model)
        
        task_scores = [entry.get(f"task{i}", 0) for i in range(6)]
        
        # With-resurrection: current pipeline score
        with_res = entry.get("pipeline_score", 0)
        with_res_scores.append(with_res)
        
        # Independent-task: simple average
        independent = np.mean(task_scores)
        independent_scores.append(independent)
        
        # No-resurrection: weighted sum that stops at first failure
        # After first task < 60, all subsequent tasks get 0
        no_res_weighted = 0
        for i, s in enumerate(task_scores):
            if s < 60:
                # First failure: this task gets its actual score, rest get 0
                no_res_weighted += s * WEIGHTS[i]
                break
            else:
                no_res_weighted += s * WEIGHTS[i]
        # Normalize to 0-100
        no_res_pipeline = no_res_weighted / sum(WEIGHTS) * 100
        no_res_scores.append(no_res_pipeline)
    
    # Compute rankings
    no_res_rank = stats.rankdata([-s for s in no_res_scores])
    with_res_rank = stats.rankdata([-s for s in with_res_scores])
    independent_rank = stats.rankdata([-s for s in independent_scores])
    
    # Compute correlations
    tau_no_vs_indep, p_no_vs_indep = stats.kendalltau(no_res_rank, independent_rank)
    rho_no_vs_indep, p_rho_no = stats.spearmanr(no_res_scores, independent_scores)
    tau_no_vs_with, p_no_vs_with = stats.kendalltau(no_res_rank, with_res_rank)
    
    # Find models with significant rank shifts (no-res vs independent)
    rank_shifts = []
    for i, model in enumerate(models):
        shift = int(independent_rank[i] - no_res_rank[i])
        if abs(shift) >= 2:
            rank_shifts.append({
                "model": model,
                "no_res_rank": int(no_res_rank[i]),
                "independent_rank": int(independent_rank[i]),
                "shift": shift,
                "no_res_score": no_res_scores[i],
                "independent_score": independent_scores[i],
                "with_res_score": with_res_scores[i],
            })
    
    # Print results
    print("=== Refined Ranking Shift Analysis ===")
    print(f"No-res vs Independent: Kendall tau={tau_no_vs_indep:.3f} (p={p_no_vs_indep:.4f}), Spearman rho={rho_no_vs_indep:.3f}")
    print(f"No-res vs With-res: Kendall tau={tau_no_vs_with:.3f} (p={p_no_vs_with:.4f})")
    
    print(f"\nModels with rank shift >= 2 (no-res vs independent):")
    for rs in sorted(rank_shifts, key=lambda x: abs(x["shift"]), reverse=True):
        direction = "↑" if rs["shift"] > 0 else "↓"
        print(f"  {rs['model']}: no_res_rank={rs['no_res_rank']}, indep_rank={rs['independent_rank']}, shift={direction}{abs(rs['shift'])}")
        print(f"    no_res_score={rs['no_res_score']:.1f}, indep_score={rs['independent_score']:.1f}, with_res_score={rs['with_res_score']:.1f}")
    
    print(f"\n=== Full Ranking Comparison ===")
    print(f"{'Model':<25} {'NoResRank':>10} {'IndepRank':>10} {'Shift':>8} {'NoResScore':>12} {'IndepScore':>12} {'WithRes':>10}")
    for i, model in enumerate(models):
        shift = int(independent_rank[i] - no_res_rank[i])
        direction = "↑" if shift > 0 else "↓" if shift < 0 else "="
        print(f"{model:<25} {int(no_res_rank[i]):>10} {int(independent_rank[i]):>10} {direction}{abs(shift):>7} {no_res_scores[i]:>12.1f} {independent_scores[i]:>12.1f} {with_res_scores[i]:>10.1f}")
    
    # Save results
    output = {
        "kendall_tau_no_vs_indep": tau_no_vs_indep,
        "kendall_p_no_vs_indep": p_no_vs_indep,
        "spearman_rho_no_vs_indep": rho_no_vs_indep,
        "kendall_tau_no_vs_with": tau_no_vs_with,
        "kendall_p_no_vs_with": p_no_vs_with,
        "models": models,
        "no_res_scores": no_res_scores,
        "independent_scores": independent_scores,
        "with_res_scores": with_res_scores,
        "no_res_rank": [int(r) for r in no_res_rank],
        "independent_rank": [int(r) for r in independent_rank],
        "with_res_rank": [int(r) for r in with_res_rank],
        "rank_shifts": rank_shifts,
    }
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_DIR / "ranking_shift_v2.json").write_text(json.dumps(output, indent=2))
    print(f"\nSaved ranking_shift_v2.json")


if __name__ == "__main__":
    main()