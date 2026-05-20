#!/usr/bin/env python3
"""Generate paper tables and figure data from RAMP leaderboard + process metrics.

Outputs:
  - LaTeX table for main leaderboard
  - JSON data for matplotlib figures
  - CSV for supplementary analysis
"""

import json
from pathlib import Path

LEADERBOARD_PATH = Path("site/assets/data/leaderboard.json")
PROCESS_PATH = Path("RAMP-paper/results/process_metrics.json")
OUTPUT_DIR = Path("RAMP-paper/results")

def generate_main_table_latex(leaderboard: list, process: dict) -> str:
    """Generate LaTeX table for main leaderboard."""
    lines = []
    lines.append("\\begin{table*}[t]")
    lines.append("\\centering")
    lines.append("\\small")
    lines.append("\\resizebox{\\textwidth}{!}{")
    lines.append("\\begin{tabular}{llrrrrrrrrrrr}")
    lines.append("\\toprule")
    lines.append("\\textbf{Model} & \\textbf{Backend} & \\textbf{T0} & \\textbf{T1} & \\textbf{T2} & \\textbf{T3} & \\textbf{T4} & \\textbf{T5} & \\textbf{MR} & \\textbf{PS} & \\textbf{PL} & \\textbf{Res} & \\textbf{Elapsed(s)} \\")
    lines.append("\\midrule")
    
    for entry in leaderboard:
        model = entry["model"]
        backend = entry["backend"]
        key = f"{model}/{backend}"
        
        # Get process metrics
        pm = process.get(key, {}).get("process_metrics", {})
        elapsed = pm.get("total_elapsed_seconds", 0)
        
        # Format scores
        scores = [entry.get(f"task{i}", 0) for i in range(6)]
        score_strs = []
        for s in scores:
            if s >= 60:
                score_strs.append(f"\\textbf{{{s:.0f}}}")
            elif s > 0:
                score_strs.append(f"{s:.0f}")
            else:
                score_strs.append("0")
        
        # Resurrection count
        res = entry.get("resurrections", 0)
        res_str = str(res) if res > 0 else "0"
        
        # Mean reward, pass score, pipeline score
        mr = entry.get("mean_reward", 0)
        ps = entry.get("pass_score", 0)
        pl = entry.get("pipeline_score", 0)
        
        # Zero-shot pass indicator
        zsp = entry.get("zero_shot_pass", False)
        model_str = model if not zsp else f"\\underline{{{model}}}"
        
        line = f"{model_str} & {backend} & {score_strs[0]} & {score_strs[1]} & {score_strs[2]} & {score_strs[3]} & {score_strs[4]} & {score_strs[5]} & {mr:.1f} & {ps:.1f} & {pl:.1f} & {res_str} & {elapsed:.0f}"
        lines.append(line)
    
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}}")
    lines.append("\\caption{\\ramp{} leaderboard across 18 model configurations. \\underline{Underlined} models achieved zero-shot pipeline success (no resurrection). \\textbf{Bold} scores indicate task passing ($\\geq 60\\%$). MR = Mean Reward, PS = Pass Score, PL = Pipeline Score, Res = Resurrection count, Elapsed = total wall-clock seconds.}")
    lines.append("\\label{tab:main}")
    lines.append("\\end{table*}")
    
    return "\n".join(lines)


def generate_figure_data(leaderboard: list, process: dict) -> dict:
    """Generate JSON data for matplotlib figures."""
    figure_data = {
        "leaderboard": [],
        "resurrection_analysis": [],
        "process_analysis": [],
        "failure_analysis": [],
    }
    
    for entry in leaderboard:
        model = entry["model"]
        backend = entry["backend"]
        key = f"{model}/{backend}"
        pm = process.get(key, {}).get("process_metrics", {})
        
        scores = [entry.get(f"task{i}", 0) for i in range(6)]
        resurrected = entry.get("resurrected", [False]*6)
        
        # Leaderboard data
        figure_data["leaderboard"].append({
            "model": model,
            "backend": backend,
            "scores": scores,
            "mean_reward": entry.get("mean_reward", 0),
            "pass_score": entry.get("pass_score", 0),
            "pipeline_score": entry.get("pipeline_score", 0),
            "resurrections": entry.get("resurrections", 0),
            "zero_shot_pass": entry.get("zero_shot_pass", False),
            "rank": entry.get("rank", 0),
            "elapsed_seconds": pm.get("total_elapsed_seconds", 0),
            "build_count": pm.get("build_count", 0),
            "score_count": pm.get("score_count", 0),
        })
        
        # Resurrection analysis: per-task resurrection effect
        # For each resurrected task, the score after resurrection
        res_tasks = []
        for i in range(6):
            if resurrected[i]:
                res_tasks.append({
                    "task": i,
                    "score": scores[i],
                    "resurrected": True,
                })
        
        figure_data["resurrection_analysis"].append({
            "model": model,
            "backend": backend,
            "resurrection_count": entry.get("resurrections", 0),
            "resurrected_tasks": res_tasks,
            "pipeline_score": entry.get("pipeline_score", 0),
            # Without resurrection, pipeline would stop at first failure
            "estimated_no_res_pipeline_depth": _estimate_pipeline_depth(scores),
        })
        
        # Process analysis
        figure_data["process_analysis"].append({
            "model": model,
            "backend": backend,
            "pipeline_score": entry.get("pipeline_score", 0),
            "mean_reward": entry.get("mean_reward", 0),
            "elapsed_seconds": pm.get("total_elapsed_seconds", 0),
            "build_count": pm.get("build_count", 0),
            "score_count": pm.get("score_count", 0),
            "build_errors": pm.get("build_errors", 0),
            "timeout_errors": pm.get("timeout_errors", 0),
        })
    
    return figure_data


def _estimate_pipeline_depth(scores: list) -> int:
    """Estimate how far an agent can progress without resurrection."""
    for i, s in enumerate(scores):
        if s < 60:
            return i
    return 6


def main():
    leaderboard = json.loads(LEADERBOARD_PATH.read_text())
    process = json.loads(PROCESS_PATH.read_text())
    
    # Generate LaTeX table
    latex_table = generate_main_table_latex(leaderboard, process)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_DIR / "main_table.tex").write_text(latex_table)
    print(f"Generated main_table.tex")
    
    # Generate figure data
    figure_data = generate_figure_data(leaderboard, process)
    Path(OUTPUT_DIR / "figure_data.json").write_text(json.dumps(figure_data, indent=2))
    print(f"Generated figure_data.json")
    
    # Generate CSV for supplementary analysis
    csv_lines = ["model,backend,t0,t1,t2,t3,t4,t5,mr,ps,pl,res,elapsed,builds,scores"]
    for entry in leaderboard:
        model = entry["model"]
        backend = entry["backend"]
        key = f"{model}/{backend}"
        pm = process.get(key, {}).get("process_metrics", {})
        
        scores = [entry.get(f"task{i}", 0) for i in range(6)]
        csv_lines.append(f"{model},{backend},{scores[0]},{scores[1]},{scores[2]},{scores[3]},{scores[4]},{scores[5]},{entry.get('mean_reward',0)},{entry.get('pass_score',0)},{entry.get('pipeline_score',0)},{entry.get('resurrections',0)},{pm.get('total_elapsed_seconds',0)},{pm.get('build_count',0)},{pm.get('score_count',0)}")
    
    Path(OUTPUT_DIR / "leaderboard_with_process.csv").write_text("\n".join(csv_lines))
    print(f"Generated leaderboard_with_process.csv")
    
    # Print resurrection analysis summary
    print("\n=== Resurrection Analysis ===")
    print(f"{'Model':<25} {'Res#':>4} {'PipelineDepth(no-res)':>20} {'PipelineScore':>12}")
    for item in figure_data["resurrection_analysis"]:
        print(f"{item['model']:<25} {item['resurrection_count']:>4} {item['estimated_no_res_pipeline_depth']:>20} {item['pipeline_score']:>12.1f}")
    
    # Print process analysis summary
    print("\n=== Process Analysis (Elapsed vs Score) ===")
    print(f"{'Model':<25} {'Elapsed(s)':>10} {'Builds':>8} {'PL':>8}")
    for item in figure_data["process_analysis"]:
        if item["elapsed_seconds"] > 0:
            print(f"{item['model']:<25} {item['elapsed_seconds']:>10.0f} {item['build_count']:>8} {item['pipeline_score']:>8.1f}")


if __name__ == "__main__":
    main()