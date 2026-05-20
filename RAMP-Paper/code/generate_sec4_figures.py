#!/usr/bin/env python3
"""生成 sec4 缺失图表: Fig4 (E2E-PRS vs GCPS 对比) + Tab2 (计分对比表)。

数据源: eval_prog/analyze_main.py 的输出 (RAMP-paper/results/main_table.csv)
"""

from pathlib import Path
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

RESULT_DIR = Path(__file__).parent.parent.parent / "RAMP-paper" / "results"
CSV_PATH = RESULT_DIR / "main_table.csv"

# Baseline scores
BASELINE = [100.0, 17.64, 20.55, 1.37, 35.1, 0.0]

matplotlib.rcParams.update({"font.size": 10, "figure.dpi": 150})

df = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df)} models from {CSV_PATH}")


# ── Fig 4: E2E-PRS vs GCPS 对比 ─────────────────────────────────

def compute_e2e_prs(row):
    """T0-T3 必须满分, 否则后续全0。T4 需要 task4>=60 才有分。"""
    tasks = ["task0", "task1", "task2", "task3", "task4", "task5"]
    all_passed = True
    scores = []
    for i, t in enumerate(tasks):
        v = row[t]
        if i < 4 and v < 99.9:  # <100
            all_passed = False
        scores.append(v if all_passed else 0)
    # T4: 需要 passed
    if all_passed and scores[4] < 60:
        scores[4] = 0
    return sum(scores) / 6.0

df["e2e_prs"] = df.apply(compute_e2e_prs, axis=1)
df["gcps"] = df["pipeline_score"]  # GCPS = 当前的 pipeline_score

# 只取 top 15 + bottom 3 来让柱子不太多
df_display = df.sort_values("gcps", ascending=False)

fig, ax = plt.subplots(figsize=(14, 7))
x = np.arange(len(df_display))
width = 0.35

bars1 = ax.bar(x - width/2, df_display["gcps"], width, label="GCPS (Granular, relaxed)",
               color="#2ca02c", alpha=0.8, edgecolor="black", linewidth=0.5)
bars2 = ax.bar(x + width/2, df_display["e2e_prs"], width, label="E2E-PRS (Production Readiness, strict)",
               color="#d62728", alpha=0.8, edgecolor="black", linewidth=0.5)

ax.set_ylabel("Pipeline Score", fontsize=12)
ax.set_title("RAMP: E2E-PRS vs GCPS — Two Scoring Paradigms (Semi-Guided Progressive)", fontsize=13, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels([m[:20] for m in df_display["model"]], rotation=45, ha="right", fontsize=7)
ax.legend(fontsize=10)
ax.axhline(y=100, color="gray", linestyle=":", alpha=0.4)
ax.grid(True, alpha=0.15, axis="y")

# 在 E2E-PRS 柱子上标注数值 (只标注 >20 的)
for bar in bars2:
    h = bar.get_height()
    if h > 20:
        ax.text(bar.get_x() + bar.get_width()/2., h + 1, f"{h:.0f}",
                ha="center", va="bottom", fontsize=6, color="#d62728")

plt.tight_layout()
fig_path = RESULT_DIR / "fig_score_comparison.png"
plt.savefig(fig_path, dpi=200, bbox_inches="tight")
plt.close()
print(f"✅ Fig4 保存: {fig_path}")


# ── Tab 2: LaTeX 计分对比表 ─────────────────────────────────────

df_tab = df.sort_values("gcps", ascending=False).head(15)
lines = [
    r"\begin{table*}[!t]",
    r"\centering",
    r"\caption{E2E-PRS vs GCPS pipeline scores for top 15 models (Semi-Guided Progressive).}",
    r"\small",
    r"\begin{tabular}{lrrrr}",
    r"\toprule",
    r"\textbf{Model} & \textbf{GCPS (Relaxed)} & \textbf{E2E-PRS (Strict)} & \textbf{Drop} & \textbf{Zero-Shot?} \\",
    r"\midrule",
]
for _, row in df_tab.iterrows():
    drop = row["gcps"] - row["e2e_prs"]
    lines.append(
        f"{row['model']} & {row['gcps']:.2f} & {row['e2e_prs']:.2f} & {drop:.2f} & "
        f"{'Yes' if row['e2e_prs'] > 80 else 'No'} \\\\"
    )
lines.extend([
    r"\bottomrule",
    r"\end{tabular}",
    r"\label{tab:scoring_comparison}",
    r"\end{table*}",
])

tex_path = RESULT_DIR / "scoring_comparison.tex"
tex_path.write_text("\n".join(lines) + "\n")
print(f"✅ Tab2 LaTeX 保存: {tex_path}")


# ── Fig 4 alt: 双面板 (E2E-PRS 柱 + Drop 柱) ────────────────────

fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

df_t10 = df.sort_values("gcps", ascending=False).head(12)

# Left: E2E-PRS vs GCPS top 12
x2 = np.arange(len(df_t10))
bars_g = ax1.bar(x2 - width/2, df_t10["gcps"], width, label="GCPS", color="#2ca02c", alpha=0.8)
bars_e = ax1.bar(x2 + width/2, df_t10["e2e_prs"], width, label="E2E-PRS", color="#d62728", alpha=0.8)
ax1.set_xticks(x2)
ax1.set_xticklabels([m[:18] for m in df_t10["model"]], rotation=45, ha="right", fontsize=7)
ax1.set_title("E2E-PRS vs GCPS (Top 12)", fontsize=12, fontweight="bold")
ax1.set_ylabel("Pipeline Score")
ax1.legend(fontsize=8)
ax1.grid(True, alpha=0.15, axis="y")

# Right: Drop (GCPS - E2E-PRS)
df_t10 = df_t10.copy()
df_t10["drop"] = df_t10["gcps"] - df_t10["e2e_prs"]
df_t10 = df_t10.sort_values("drop", ascending=True)
bars_d = ax2.barh(df_t10["model"], df_t10["drop"], color="#ff7f0e", alpha=0.8, edgecolor="black", linewidth=0.5)
ax2.set_title("Score Drop from GCPS → E2E-PRS", fontsize=12, fontweight="bold")
ax2.set_xlabel("Pipeline Score Drop")
ax2.grid(True, alpha=0.15, axis="x")

plt.tight_layout()
fig2_path = RESULT_DIR / "fig_score_comparison_v2.png"
plt.savefig(fig2_path, dpi=200, bbox_inches="tight")
plt.close()
print(f"✅ Fig4 alt 保存: {fig2_path}")

print("\n✅ 全部图表生成完成!")