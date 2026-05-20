#!/usr/bin/env python3
"""Re-generate all sec4 figures with ONLY 14 valid models (eval_prog subdirs)."""
import json, sys
from pathlib import Path
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

VALID_MODELS = {
    'deepseek-chat','deepseek-reasoner','deepseek-v4-flash','deepseek-v4-pro',
    'glm-4.7','glm-5.1','kimi-k2.5','kimi-k2.6','minimax-m2.5',
    'glm-4.6','gpt-5.5','qwen3.5-plus','qwen3.6-max-preview','qwen3-coder-flash'
}

D = Path("/root/proj/Paper/EXPERIMENT/RAMP")
OUT = D / "RAMP-Paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
DATA = D / "eval_prog" / "engineer-500-all.json"

BASELINE = [100.0, 17.64, 20.55, 1.37, 35.1, 0.0]

with open(DATA) as f:
    raw = json.load(f)

# Filter to only 14 valid models + openhands + has_report + pipeline
df = pd.DataFrame(raw)
df = df[(df['model'].isin(VALID_MODELS)) & (df['has_report']==True) & 
        (df['context_mode']=='pipeline') & (df['backend']=='openhands')]
df = df.loc[df.groupby('model')['pipeline_score'].idxmax()].copy()
df = df.sort_values('pipeline_score', ascending=False).reset_index(drop=True)
print(f"14 models:\n{df[['model','pipeline_score','mean_reward']].to_string()}")

# Save CSV
df.to_csv(str(OUT / "main_table_14.csv"), index=False)

# ── Fig: Per-task trajectory ──────────────────────────────────
tasks = ['task0','task1','task2','task3','task4','task5']
tlabs = ['T0\nSetup','T1\nLexer','T2\nParser','T3\nIR Gen','T4\nIR Opt','T5\nCodeGen']

matplotlib.rcParams.update({'font.size': 14, 'axes.titlesize': 16, 'axes.labelsize': 14, 'xtick.labelsize': 12, 'ytick.labelsize': 12, 'legend.fontsize': 12})

fig,ax=plt.subplots(figsize=(12,7))
hi = {'deepseek-v4-pro':'#1f77b4','gpt-5.5':'#ff7f0e','deepseek-v4-flash':'#2ca02c','qwen3.6-max-preview':'#d62728'}
for _,r in df.iterrows():
    sc=[r[t] for t in tasks]
    c=hi.get(r['model'],'gray'); a=0.8 if r['model'] in hi else 0.25
    lw=2.5 if r['model'] in hi else 0.8; ms=7 if r['model'] in hi else 4
    ax.plot(range(6),sc,'o-',color=c,alpha=a,lw=lw,ms=ms,label=r['model'] if r['model'] in hi else '')
ax.plot(range(6),BASELINE,'s--',color='darkred',alpha=0.6,lw=2,ms=6,label='Baseline (no agent)')
ax.axhline(y=60,color='green',ls=':',alpha=0.5,lw=1.5,label='Pass (60%)')
ax.set_xticks(range(6)); ax.set_xticklabels(tlabs)
ax.set_ylabel('Score'); ax.set_ylim(-5,105)
ax.set_title('RAMP: Per-Task Score Trajectory (14 models, Progressive)',fontsize=16,fontweight='bold')
ax.legend(loc='lower left',fontsize=11,ncol=2); ax.grid(alpha=0.2)
plt.tight_layout(); plt.savefig(str(OUT/"fig_per_task_trajectory.png"),dpi=200,bbox_inches='tight'); plt.close()
print("✅ trajectory saved")

# ── Fig: E2E-PRS vs GCPS ──────────────────────────────────────
def e2e_prs(row):
    ok=True; sc=[]
    for i,t in enumerate(tasks):
        v=row[t]; 
        if i<4 and v<99.9: ok=False
        sc.append(v if ok else 0)
    return sum(sc)/6

df['e2e']=df.apply(e2e_prs,axis=1)
df['gcps']=df['pipeline_score']

fig,ax=plt.subplots(figsize=(14,7))
x=np.arange(len(df)); w=0.35
ax.bar(x-w/2,df['gcps'],w,label='GCPS (Relaxed)',color='#2ca02c',alpha=0.8,ec='black',lw=0.5)
ax.bar(x+w/2,df['e2e'],w,label='E2E-PRS (Strict)',color='#d62728',alpha=0.8,ec='black',lw=0.5)
ax.set_xticks(x); ax.set_xticklabels([m[:18] for m in df['model']],rotation=45,ha='right',fontsize=11)
ax.set_ylabel('Pipeline Score')
ax.set_title('E2E-PRS vs GCPS (14 models, Progressive)',fontsize=16,fontweight='bold')
ax.legend(fontsize=14); ax.grid(alpha=0.15,axis='y')
plt.tight_layout(); plt.savefig(str(OUT/"fig_score_comparison.png"),dpi=200,bbox_inches='tight'); plt.close()
print("✅ scoring comparison saved")

# ── Fig: Cost-Performance (time + cost) ────────────────────────
df['_cost']=pd.to_numeric(df.get('run_llm_cost_usd'),errors='coerce')

fig,(ax1,ax2)=plt.subplots(1,2,figsize=(16,7))

sc1=ax1.scatter(df['elapsed_seconds'],df['pipeline_score'],s=df['run_agent_llm_rounds'].fillna(0)/2+40,
                c=range(len(df)),cmap='viridis',alpha=0.8,ec='black',lw=0.5)
for _,r in df.iterrows():
    if r['pipeline_score']>=65 or r['elapsed_seconds']>5000:
        ax1.annotate(r['model'][:18],(r['elapsed_seconds'],r['pipeline_score']),fontsize=10,xytext=(5,5),textcoords='offset points')
ax1.set_xlabel('Elapsed Time (s)'); ax1.set_ylabel('Pipeline Score')
ax1.set_title('Time vs Performance',fontsize=16,fontweight='bold'); ax1.grid(alpha=0.2)

df_c = df[df['_cost'].notna() & (df['_cost']>0)]
sc2=ax2.scatter(df_c['_cost'],df_c['pipeline_score'],s=df_c['run_llm_total_tokens'].fillna(0)/5e5+40,
                c=range(len(df_c)),cmap='plasma',alpha=0.8,ec='black',lw=0.5)
for _,r in df_c.iterrows():
    if r['pipeline_score']>=65 or r['_cost']>5:
        ax2.annotate(r['model'][:18],(r['_cost'],r['pipeline_score']),fontsize=10,xytext=(5,5),textcoords='offset points')
ax2.set_xlabel('LLM Cost (USD)'); ax2.set_ylabel('Pipeline Score')
ax2.set_title('Cost vs Performance',fontsize=16,fontweight='bold'); ax2.grid(alpha=0.2)

plt.tight_layout(); plt.savefig(str(OUT/"fig_cost_performance.png"),dpi=200,bbox_inches='tight'); plt.close()
print("✅ cost-performance saved")

# ── LaTeX table ────────────────────────────────────────────────
lines=[r"\begin{table*}[!t]",r"\centering",
       r"\caption{\eva{} \Progressive{} leaderboard across 14 model configurations (GCPS). \textbf{Bold}=task passing ($\geq 60\%$). PL=Pipeline Score, MR=Mean Reward. \textsc{Baseline}=raw code framework without agent modification.}",r"\small",
       r"\begin{tabular}{lrrrrrrrrr}",r"\toprule",
       r"\textbf{Model} & \textbf{T0} & \textbf{T1} & \textbf{T2} & \textbf{T3} & \textbf{T4} & \textbf{T5} & \textbf{PL} & \textbf{MR} & \textbf{Cost\$} \\",r"\midrule"]
for _,r in df.iterrows():
    c=r.get('run_llm_cost_usd','')
    cs=f'{c:.2f}' if isinstance(c,(int,float)) and c>0 else '---'
    def b(v,t=60): return f"\\textbf{{{v:.0f}}}" if v>=t else f"{v:.0f}"
    def bf(v,t=60): return f"\\textbf{{{v:.1f}}}" if v>=t else f"{v:.1f}"
    lines.append(f"{r['model']} & {b(r['task0'])} & {bf(r['task1'])} & {bf(r['task2'])} & {bf(r['task3'])} & {bf(r['task4'])} & {bf(r['task5'])} & {r['pipeline_score']:.2f} & {r['mean_reward']:.2f} & {cs} \\\\")
lines.append(r"\midrule")
lines.append(r"\textsc{Baseline} & 100 & 17.6 & 20.6 & 1.4 & 35.1 & 0.0 & 29.2 & --- & --- \\")
lines.extend([r"\bottomrule",r"\end{tabular}",r"\label{tab:main}",r"\end{table*}"])
(OUT/"main_table_14.tex").write_text("\n".join(lines)+"\n")
print(f"✅ LaTeX saved: {OUT/'main_table_14.tex'}")

# Print key stats
print(f"\n=== Key Stats (14 models) ===")
print(f"Zero-shot pass: {df['zero_shot_pass'].sum()}/14")
print(f"Avg PL: {df['pipeline_score'].mean():.2f}")
print(f"Best PL: {df['pipeline_score'].max():.2f} ({df.loc[df['pipeline_score'].idxmax(),'model']})")
print(f"Best MR: {df['mean_reward'].max():.2f} ({df.loc[df['mean_reward'].idxmax(),'model']})")
print(f"Avg elapsed: {df['elapsed_seconds'].mean():.0f}s")
print(f"\nDone!")