import os
from pathlib import Path

from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle, Patch
import matplotlib as mpl
import textwrap

OUTPUT_DIR = Path(__file__).resolve().parent


def save_figure(fig, stem: str) -> None:
    """Save figure as PDF/SVG (vector) and PNG (raster). Atomic replace so viewers pick up changes."""
    base = OUTPUT_DIR / stem
    outputs = [
        (".pdf", {}),
        (".svg", {}),
        (".png", {"dpi": 300}),
    ]
    for ext, extra in outputs:
        final = base.with_suffix(ext)
        tmp = final.with_name(f"{final.stem}.tmp{ext}")
        try:
            fig.savefig(tmp, bbox_inches="tight", **extra)
            os.replace(tmp, final)
        except OSError as exc:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            raise OSError(
                f"Could not write {final}. Close it in your PDF/image viewer and retry."
            ) from exc
        print(final.resolve())
# ============================================================
# 1. Data
# ============================================================

models = [
    "DS-Chat", "DS-Reasoner", "DS-v4-Flash", "DS-v4-Pro",
    "GLM-4.7", "GLM-5.1", "GLM-4.6", "Kimi-2.6",
    "Kimi-2.5", "GPT-5.5", "Qwen-3.6-Max", "Qwen-3.5-Plus",
    "Qwen3-Coder", "MiniMax-2.5", "Opus-4.7"
]

tasks = [f"task{i}" for i in range(6)]

grid = {m: {t: "no_failure" for t in tasks} for m in models}

def fill(model, start, end, failure):
    for i in range(start, end + 1):
        grid[model][f"task{i}"] = failure


def mark_unattempted_tasks():
    """Stages after the first failure that were never run must not show as pass."""
    for model in models:
        hit_failure = False
        for task in tasks:
            status = grid[model][task]
            if hit_failure and status == "no_failure":
                grid[model][task] = "not_attempted"
            elif status != "no_failure":
                hit_failure = True

fill("DS-Chat", 2, 2, "strategic_task_skipping")
fill("DS-Chat", 3, 3, "context_window_exhaustion")

fill("DS-Reasoner", 1, 1, "execution_failure")
fill("DS-Reasoner", 2, 2, "strategic_task_skipping")
fill("DS-Reasoner", 3, 3, "context_window_exhaustion")

fill("DS-v4-Flash", 2, 4, "strategic_task_skipping")
fill("DS-v4-Pro", 3, 4, "strategic_task_skipping")

fill("GLM-4.7", 1, 1, "execution_failure")
fill("GLM-4.7", 2, 2, "context_window_exhaustion")

fill("GLM-5.1", 1, 1, "execution_failure")
fill("GLM-5.1", 2, 2, "context_window_exhaustion")

fill("GLM-4.6", 2, 2, "process_collapse")
fill("GLM-4.6", 3, 3, "context_window_exhaustion")

fill("Kimi-2.6", 2, 4, "strategic_task_skipping")
fill("Kimi-2.6", 5, 5, "context_window_exhaustion")

fill("Kimi-2.5", 2, 4, "strategic_task_skipping")
fill("Kimi-2.5", 5, 5, "context_window_exhaustion")

fill("Qwen-3.6-Max", 3, 3, "context_window_exhaustion")

fill("Qwen-3.5-Plus", 2, 2, "execution_failure")
fill("Qwen-3.5-Plus", 3, 5, "strategic_task_skipping")

fill("Qwen3-Coder", 1, 3, "process_collapse")

fill("MiniMax-2.5", 1, 2, "execution_failure")
fill("MiniMax-2.5", 3, 3, "context_window_exhaustion")

# GPT-5.5: only model with stage-4 failure attributed to framework defect.
grid["GPT-5.5"]["task4"] = "framework_defect_error"

fill("Opus-4.7", 4, 4, "strategic_task_skipping")

mark_unattempted_tasks()

# Stage 5 completed despite earlier failures/skips (not "not attempted").
grid["DS-v4-Flash"]["task5"] = "no_failure"
grid["DS-v4-Pro"]["task5"] = "no_failure"
grid["Opus-4.7"]["task5"] = "no_failure"


# ============================================================
# 2. Academic visual style
# ============================================================

colors = {
    "no_failure": "#DDF4E4",
    "not_attempted": "#ECEFF3",
    "strategic_task_skipping": "#5B9BD5",
    "context_window_exhaustion": "#8E7CC3",
    "process_collapse": "#E9A23B",
    "execution_failure": "#D95F5F",
    "framework_defect_error": "#6C757D",
}

labels = {
    "no_failure": "Pass",
    "not_attempted": "Not Attempted",
    "strategic_task_skipping": "Planning Failure",
    "context_window_exhaustion": "Context Failure",
    "process_collapse": "Reasoning Failure",
    "execution_failure": "Tooling & Integration  Failure",
    "framework_defect_error": "Infrastructure  Failure",
}


abbr = {
    "no_failure": "✓",
    "not_attempted": "—",
    "strategic_task_skipping": "PF",
    "context_window_exhaustion": "CF",
    "process_collapse": "RF",
    "execution_failure": "TF",
    "framework_defect_error": "IF",
}

legend_order = [
    "execution_failure",
    "framework_defect_error",
    "process_collapse",
    "strategic_task_skipping",
    "context_window_exhaustion",
    "no_failure",
    "not_attempted",
]

mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.8,
})


# ============================================================
# 3. Figure 1a: Categorical Heatmap
# ============================================================

fig, ax = plt.subplots(figsize=(18.8, 7.3))
ax.set_facecolor("#FFFFFF")

cell_margin = 0.04

for x, model in enumerate(models):
    for y, task in enumerate(tasks):
        failure = grid[model][task]

        rect = Rectangle(
            (x + cell_margin, y + cell_margin),
            1 - 2 * cell_margin,
            1 - 2 * cell_margin,
            facecolor=colors[failure],
            edgecolor="#FFFFFF",
            linewidth=1.4,
            zorder=2
        )
        ax.add_patch(rect)

        if failure == "no_failure":
            text_color = "#4F8A60"
        elif failure == "not_attempted":
            text_color = "#9AA3AD"
        else:
            text_color = "white"

        ax.text(
            x + 0.5,
            y + 0.5,
            abbr[failure],
            ha="center",
            va="center",
            fontsize=10.5,
            fontweight="bold",
            color=text_color,
            zorder=3
        )

# subtle grid lines
for x in range(len(models) + 1):
    ax.axvline(x, color="#E4EAF0", linewidth=0.85, zorder=1)

for y in range(len(tasks) + 1):
    ax.axhline(y, color="#E4EAF0", linewidth=0.85, zorder=1)

ax.set_xlim(0, len(models))
ax.set_ylim(0, len(tasks))

ax.set_xticks([i + 0.5 for i in range(len(models))])
wrapped_models = [
    "\n".join(textwrap.wrap(m, width=13, break_long_words=False, break_on_hyphens=True))
    for m in models
]
ax.set_xticklabels(wrapped_models, rotation=0, ha="center", fontsize=10.5)

ax.set_yticks([i + 0.5 for i in range(len(tasks))])
ax.set_yticklabels([f"Stage {i}" for i in range(len(tasks))], fontsize=12)

ax.set_xlabel("Models", fontsize=14, labelpad=16)
ax.set_ylabel("Task Stage", fontsize=14, labelpad=10)

for spine in ax.spines.values():
    spine.set_visible(False)

ax.tick_params(axis="both", length=0)


handles = [
    Patch(
        facecolor=colors[k],
        edgecolor="#D7DEE8",
        label=f"{labels[k]} ({abbr[k]})"
    )
    for k in legend_order
]

fig.legend(
    handles=handles,
    loc="upper right",
    bbox_to_anchor=(0.985, 0.945),
    ncol=1,
    frameon=True,
    fancybox=True,
    framealpha=1,
    facecolor="#FFFFFF",
    edgecolor="#E3E8EF",
    fontsize=10.5,
    borderpad=0.8,
    labelspacing=0.7,
    handlelength=1.4,
)


fig.subplots_adjust(top=0.82, bottom=0.18, left=0.07, right=0.87)

save_figure(fig, "failure_taxonomy_heatmap")
plt.close(fig)


# ============================================================
# 4. Figure 1b: Per-stage horizontal bar (pass: ✓, fail: type abbr)
# ============================================================

# Lexicographic over pass/fail only (stage 0→5): both-fail stages tie and
# compare at the next stage, so later passes break ties (e.g. GLM-4.6 > Qwen-3.5-Plus).
def lex_sort_key(model):
    return tuple(
        0 if grid[model][t] == "no_failure" else 1
        for t in tasks
    )


models_sorted = sorted(models, key=lex_sort_key)

fig, ax = plt.subplots(figsize=(10.5, 7.8))
ax.set_facecolor("#FFFFFF")

y_positions = list(range(len(models_sorted)))
bar_height = 0.72

for yi, model in enumerate(models_sorted):
    for ti, task in enumerate(tasks):
        failure = grid[model][task]

        ax.barh(
            yi,
            1,
            left=ti,
            color=colors[failure],
            edgecolor="white",
            linewidth=0.8,
            height=bar_height,
        )

        if failure == "no_failure":
            text_color = "#4F8A60"
        elif failure == "not_attempted":
            text_color = "#9AA3AD"
        else:
            text_color = "white"

        ax.text(
            ti + 0.5,
            yi,
            abbr[failure],
            ha="center",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color=text_color,
        )

ax.set_yticks(y_positions)
ax.set_yticklabels(models_sorted, fontsize=10.5)
ax.invert_yaxis()

ax.set_xlim(0, len(tasks))
ax.set_xlabel("Task Stages", fontsize=13, labelpad=10)
ax.set_ylabel("Models", fontsize=13, labelpad=10)

ax.set_xticks(range(0, len(tasks) + 1))
ax.set_xticklabels([""] * (len(tasks) + 1))
for i in range(len(tasks)):
    ax.text(
        i + 0.5, -0.02, str(i),
        ha="center", va="top",
        transform=ax.get_xaxis_transform(),
        fontsize=mpl.rcParams["xtick.labelsize"],
        color="#4B5563",
    )
# Vertical guides only between stages (skip x=0 and x=len(tasks) to avoid side borders).
for x in range(1, len(tasks)):
    ax.axvline(x, color="#E4EAF0", linewidth=0.8, zorder=0)

for spine in ("top", "right", "left"):
    ax.spines[spine].set_visible(False)

ax.spines["bottom"].set_visible(True)
ax.spines["bottom"].set_color("#AAB2BD")
ax.spines["bottom"].set_bounds(0, len(tasks))
ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", colors="#4B5563")

bar_legend_handles = [
    Patch(
        facecolor=colors[k],
        edgecolor="white",
        label=f"{labels[k]} ({abbr[k]})",
    )
    for k in legend_order
]
ax.legend(
    handles=bar_legend_handles,
    loc="lower center",
    bbox_to_anchor=(0.5, -0.18),
    ncol=4,
    frameon=False,
    fontsize=10.5,
    columnspacing=1.6,
    handletextpad=0.45,
)

fig.subplots_adjust(top=0.96, bottom=0.20, left=0.26, right=0.98)

save_figure(fig, "fig_failure_taxonomy")
plt.close(fig)