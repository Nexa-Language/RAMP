#!/usr/bin/env python3
"""Generate matplotlib figures for RAMP paper.

Outputs PNG figures to RAMP-paper/paper/mypaper/figures/
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

FIGURE_DIR = Path("RAMP-paper/paper/mypaper/figures")
DATA_DIR = Path("RAMP-paper/results")

# Style settings
plt.rcParams.update({
    'font.size': 10,
    'font.family': 'serif',
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})


def load_data():
    figure_data = json.loads((DATA_DIR / "figure_data.json").read_text())
    return figure_data


def fig_resurrection_gain(data):
    """Figure 4: Resurrection gain — pipeline depth without vs with resurrection."""
    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    
    models = [item["model"] for item in data["resurrection_analysis"]]
    no_res_depth = [item["estimated_no_res_pipeline_depth"] for item in data["resurrection_analysis"]]
    with_res_depth = [6 for _ in data["resurrection_analysis"]]  # With resurrection, all 6 tasks are reachable
    pipeline_scores = [item["pipeline_score"] for item in data["resurrection_analysis"]]
    
    # Sort by no-res depth
    sorted_indices = sorted(range(len(models)), key=lambda i: no_res_depth[i], reverse=True)
    models_sorted = [models[i] for i in sorted_indices]
    no_res_sorted = [no_res_depth[i] for i in sorted_indices]
    with_res_sorted = [with_res_depth[i] for i in sorted_indices]
    scores_sorted = [pipeline_scores[i] for i in sorted_indices]
    
    x = np.arange(len(models_sorted))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, no_res_sorted, width, label='No Resurrection', color='#e74c3c', alpha=0.8)
    bars2 = ax.bar(x + width/2, with_res_sorted, width, label='With Resurrection', color='#2ecc71', alpha=0.8)
    
    # Add pipeline score annotations
    for i, (depth, score) in enumerate(zip(no_res_sorted, scores_sorted)):
        if depth < 6:
            ax.annotate(f'{score:.0f}', xy=(i - width/2, depth), 
                       xytext=(0, 3), textcoords='offset points',
                       ha='center', va='bottom', fontsize=7, color='#e74c3c')
    
    ax.set_xlabel('Model')
    ax.set_ylabel('Pipeline Depth (tasks reachable)')
    ax.set_title('Resurrection Recovers Downstream Evaluation Signal')
    ax.set_xticks(x)
    ax.set_xticklabels(models_sorted, rotation=45, ha='right', fontsize=7)
    ax.legend(loc='upper right')
    ax.set_ylim(0, 7)
    ax.axhline(y=6, color='gray', linestyle='--', alpha=0.3, label='Full pipeline')
    
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "fig_resurrection_gain.png")
    print(f"Saved fig_resurrection_gain.png")
    plt.close(fig)


def fig_cost_performance(data):
    """Figure 5: Cost-performance frontier — elapsed time vs pipeline score."""
    fig, ax = plt.subplots(1, 1, figsize=(6, 4))
    
    models = []
    elapsed = []
    scores = []
    backends = []
    
    for item in data["process_analysis"]:
        if item["elapsed_seconds"] > 0:
            models.append(item["model"])
            elapsed.append(item["elapsed_seconds"] / 3600)  # Convert to hours
            scores.append(item["pipeline_score"])
            backends.append(item["backend"])
    
    # Color by backend
    backend_colors = {
        "openhands": "#3498db",
        "codex": "#e67e22",
        "claude": "#9b59b6",
        "kimi": "#1abc9c",
    }
    
    for i, (m, e, s, b) in enumerate(zip(models, elapsed, scores, backends)):
        color = backend_colors.get(b, "#95a5a6")
        ax.scatter(e, s, c=color, s=80, zorder=5, edgecolors='white', linewidth=0.5)
        # Label
        short_name = m.split("-")[0] if len(m) > 10 else m
        ax.annotate(short_name, (e, s), fontsize=6, 
                   xytext=(5, 5), textcoords='offset points', alpha=0.7)
    
    # Pareto frontier
    sorted_by_score = sorted(zip(scores, elapsed, models), key=lambda x: (-x[0], x[1]))
    pareto = []
    min_elapsed_so_far = float('inf')
    for s, e, m in sorted_by_score:
        if e < min_elapsed_so_far:
            pareto.append((e, s))
            min_elapsed_so_far = e
    
    if len(pareto) > 1:
        pareto.sort(key=lambda x: x[0])
        ax.plot([p[0] for p in pareto], [p[1] for p in pareto], 
               'k--', alpha=0.4, linewidth=1, label='Pareto frontier')
    
    # Legend for backends
    patches = [mpatches.Patch(color=c, label=b.capitalize()) for b, c in backend_colors.items() if c != "#95a5a6"]
    ax.legend(handles=patches, loc='lower right', title='Backend')
    
    ax.set_xlabel('Total Elapsed Time (hours)')
    ax.set_ylabel('Pipeline Score')
    ax.set_title('Cost-Performance Frontier: Time vs Score')
    ax.set_xlim(0, max(elapsed) * 1.1 if elapsed else 5)
    ax.set_ylim(40, 105)
    ax.grid(True, alpha=0.2)
    
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "fig_cost_performance.png")
    print(f"Saved fig_cost_performance.png")
    plt.close(fig)


def fig_score_heatmap(data):
    """Figure 3: Per-task score heatmap across models."""
    fig, ax = plt.subplots(1, 1, figsize=(8, 5))
    
    models = [item["model"] for item in data["leaderboard"]]
    scores_matrix = np.array([item["scores"] for item in data["leaderboard"]])
    
    # Sort by pipeline score
    sorted_idx = sorted(range(len(models)), key=lambda i: data["leaderboard"][i]["pipeline_score"], reverse=True)
    models_sorted = [models[i] for i in sorted_idx]
    scores_sorted = scores_matrix[sorted_idx]
    
    im = ax.imshow(scores_sorted, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
    
    # Add score text
    for i in range(len(models_sorted)):
        for j in range(6):
            s = scores_sorted[i, j]
            text_color = 'white' if s < 30 else 'black'
            ax.text(j, i, f'{s:.0f}', ha='center', va='center', fontsize=7, color=text_color)
    
    ax.set_xticks(range(6))
    ax.set_xticklabels(['T0\nSetup', 'T1\nLexer', 'T2\nParser', 'T3\nIR Gen', 'T4\nIR Opt', 'T5\nCodegen'])
    ax.set_yticks(range(len(models_sorted)))
    ax.set_yticklabels(models_sorted, fontsize=7)
    ax.set_title('RAMP Per-Task Score Matrix')
    
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Score (0-100)')
    
    # Add passing threshold line
    ax.axhline(y=-0.5, color='gray', linewidth=0.5)
    
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "fig_score_heatmap.png")
    print(f"Saved fig_score_heatmap.png")
    plt.close(fig)


def fig_failure_taxonomy(data):
    """Figure 7: Failure taxonomy — composition of failure types."""
    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    
    models = [item["model"] for item in data["leaderboard"]]
    scores = [item["scores"] for item in data["leaderboard"]]
    
    # Categorize failures
    predecessor_fail = []  # Tasks unreachable due to predecessor
    task_local_fail = []   # Task failed despite correct prerequisites
    execution_fail = []    # Build/execution errors
    
    for i, (model, task_scores) in enumerate(zip(models, scores)):
        res = data["leaderboard"][i].get("resurrected", [False]*6)
        res_count = data["leaderboard"][i].get("resurrections", 0)
        
        pred = 0
        local = 0
        exec_f = 0
        
        # Find first failure point
        first_fail = -1
        for j, s in enumerate(task_scores):
            if s < 60:
                first_fail = j
                break
        
        if first_fail >= 0:
            # First failure is task-local
            local += 1
            # All subsequent failures without resurrection are predecessor
            for j in range(first_fail + 1, 6):
                if not res[j]:
                    pred += 1
                else:
                    # After resurrection, if still fails, it's task-local
                    if task_scores[j] < 60:
                        local += 1
                    # If score > 0 but < 60, could be execution
                    if 0 < task_scores[j] < 60:
                        exec_f += 1
        
        predecessor_fail.append(pred)
        task_local_fail.append(local)
        execution_fail.append(exec_f)
    
    # Sort by total failures
    total_fail = [p + l + e for p, l, e in zip(predecessor_fail, task_local_fail, execution_fail)]
    sorted_idx = sorted(range(len(models)), key=lambda i: total_fail[i], reverse=True)
    
    models_sorted = [models[i] for i in sorted_idx]
    pred_sorted = [predecessor_fail[i] for i in sorted_idx]
    local_sorted = [task_local_fail[i] for i in sorted_idx]
    exec_sorted = [execution_fail[i] for i in sorted_idx]
    
    x = np.arange(len(models_sorted))
    
    ax.bar(x, pred_sorted, label='Predecessor Failure', color='#e74c3c', alpha=0.8)
    ax.bar(x, local_sorted, bottom=pred_sorted, label='Task-Local Failure', color='#f39c12', alpha=0.8)
    ax.bar(x, exec_sorted, bottom=[p+l for p,l in zip(pred_sorted, local_sorted)], 
           label='Execution Failure', color='#3498db', alpha=0.8)
    
    ax.set_xlabel('Model')
    ax.set_ylabel('Number of Failed Tasks')
    ax.set_title('Failure Taxonomy: Predecessor vs Task-Local vs Execution')
    ax.set_xticks(x)
    ax.set_xticklabels(models_sorted, rotation=45, ha='right', fontsize=7)
    ax.legend(loc='upper right')
    
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "fig_failure_taxonomy.png")
    print(f"Saved fig_failure_taxonomy.png")
    plt.close(fig)


def main():
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    data = load_data()
    
    fig_resurrection_gain(data)
    fig_cost_performance(data)
    fig_score_heatmap(data)
    fig_failure_taxonomy(data)
    
    print(f"\nAll figures saved to {FIGURE_DIR}")


if __name__ == "__main__":
    main()