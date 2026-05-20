#!/usr/bin/env python3
"""Generate Fig4: E2E-PRS vs GCPS comparison + Tab2 LaTeX for sec4."""
import json, sys
from pathlib import Path
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

D = "/root/proj/Paper/EXPERIMENT/RAMP"
OUT = Path(D) / "RAMP-Paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

with open(f"{D}/eval_prog/engineer-500-all.json") as f:
    raw = json.load(f)
df_all = pd.DataFrame(raw)
df_all = df_all[(df_all["has_report"]==True) & (df_all["context_mode"]=="pipeline") & (df_all["backend"]=="openhands")]
df = df_all.loc[df_all.groupby("model")["pipeline_score"].idxmax()].copy()
df = df.sort_values("pipeline_score", ascending=False).reset_index(drop=True)
print(f"Loaded {len(df)} models")

# Save CSV
df.to_csv(str(OUT / "main_table.csv"), index=False)

# ── E2E-PRS ─────────────────────────────────────────────────────
def e2e_prs(row):
    tasks=["task0","task1","task2","task3","task4","task5"]
    ok=True; sc=[]
    for i,t in enumerate(tasks):
        v=row[t]
        if i<4 and v<99.9: ok=False
        sc.append(v if ok else 0)
    return sum(sc)/6.0

df["e2e"]=df.apply(e2e_prs,axis=1)
df["gcps"]=df["pipeline_score"]

# ── Fig4 ────────────────────────────────────────────────────────
fig,ax=plt.subplots(figsize=(14,7))
x=np.arange(len(df)); w=0.35
ax.bar(x-w/2,df["gcps"],w,label="GCPS (Relaxed)",color="#2ca02c",alpha=0.8,edgecolor="black",lw=0.5)
ax.bar(x+w/2,df["e2e"],w,label="E2E-PRS (Strict)",color="#d62728",alpha=0.8,edgecolor="black",lw=0.5)
ax.set_xticks(x); ax.set_xticklabels([m[:18] for m in df["model"]],rotation=45,ha="right",fontsize=7)
ax.set_ylabel("Pipeline Score",fontsize=12)
ax.set_title("E2E-PRS vs GCPS Scoring Comparison (Semi-Guided Progressive)",fontsize=13,fontweight="bold")
ax.legend(fontsize=10); ax.grid(True,alpha=0.15,axis="y")
plt.tight_layout(); plt.savefig(str(OUT/"fig_score_comparison.png"),dpi=200,bbox_inches="tight")
plt.close()
print("✅ Fig4 saved")

# ── Tab2 LaTeX ──────────────────────────────────────────────────
lines=[r"\begin{table*}[!t]",r"\centering",
       r"\caption{E2E-PRS vs GCPS pipeline scores (Semi-Guided Progressive).}",r"\small",
       r"\begin{tabular}{lrrrr}",r"\toprule",
       r"\textbf{Model} & \textbf{GCPS (Relaxed)} & \textbf{E2E-PRS (Strict)} & \textbf{Drop} \\",r"\midrule"]
for _,row in df.iterrows():
    lines.append(f"{row['model']} & {row['gcps']:.2f} & {row['e2e']:.2f} & {row['gcps']-row['e2e']:.2f} \\\\")
lines.extend([r"\bottomrule",r"\end{tabular}",r"\label{tab:scoring_comparison}",r"\end{table*}"])
(OUT/"scoring_comparison.tex").write_text("\n".join(lines)+"\n")
print(f"✅ Tab2 saved: {OUT/'scoring_comparison.tex'}")
print("\nDone!")