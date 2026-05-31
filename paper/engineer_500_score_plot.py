"""Plot per-model task scores as segmented horizontal bars."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

DATA_PATH = Path(__file__).parent / "engineer-500-score.json"
OUTPUT_PATH = Path(__file__).parent / "fig_score.png"

TASK_KEYS = [f"task{i}" for i in range(6)]
# Segment widths on the x-axis (must sum to 1.0).
TASK_WEIGHTS = [0.05, 0.20, 0.20, 0.15, 0.30, 0.10]
TASK_LEFTS = [sum(TASK_WEIGHTS[:i]) for i in range(len(TASK_KEYS))]
TASK_COLORS = [
    "#4C72B0",
    "#55A868",
    "#C44E52",
    "#8172B3",
    "#CCB974",
    "#64B5CD",
]
BG_COLOR = "#ECECEC"

MODEL_SHORT_NAMES = {
    "claude-opus-4-7": "Opus-4.7",
    "kimi-k2.6": "Kimi-2.6",
    "kimi-k2.5": "Kimi-2.5",
    "gpt-5.5": "GPT-5.5",
    "deepseek-v4-flash": "DS-v4-Flash",
    "glm-4.6": "GLM-4.6",
    "deepseek-v4-pro": "DS-v4-Pro",
    "deepseek-reasoner": "DS-Reasoner",
    "deepseek-chat": "DS-Chat",
    "qwen3.6-max-preview": "Qwen-3.6-Max",
    "qwen3.5-plus": "Qwen-3.5-Plus",
    "qwen3-coder-flash": "Qwen3-Coder",
    "glm-5.1": "GLM-5.1",
    "glm-4.7": "GLM-4.7",
    "minimax-m2.5": "MiniMax-2.5",
}


def load_data(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        return raw["models"]
    return raw


def plot_scores(records: list[dict], output_path: Path) -> None:
    records = sorted(records, key=lambda r: r["mean_reward"], reverse=True)
    models = [r["model"] for r in records]
    n_models = len(models)
    n_tasks = len(TASK_KEYS)

    fig_h = max(3.6, 0.26 * n_models + 0.6)
    fig, ax = plt.subplots(figsize=(11, fig_h))

    bar_height = 0.48
    y_positions = list(range(n_models))
    task_average_scores = {
        task_key: sum(record[task_key] for record in records) / n_models / 100.0
        for task_key in TASK_KEYS
    }

    for y, record in zip(y_positions, records):
        for task_idx, task_key in enumerate(TASK_KEYS):
            score = record[task_key] / 100.0
            x_left = TASK_LEFTS[task_idx]
            segment_width = TASK_WEIGHTS[task_idx]
            x_width = score * segment_width

            ax.barh(
                y,
                x_width,
                left=x_left,
                height=bar_height,
                color=TASK_COLORS[task_idx],
                edgecolor="white",
                linewidth=0.4,
                zorder=3,
            )

            if score < 1.0:
                ax.barh(
                    y,
                    (1.0 - score) * segment_width,
                    left=x_left + x_width,
                    height=bar_height,
                    color=BG_COLOR,
                    edgecolor="white",
                    linewidth=0.4,
                    zorder=2,
                )

    for task_idx in range(1, n_tasks):
        ax.axvline(
            TASK_LEFTS[task_idx],
            color="#222222",
            linewidth=1.1,
            linestyle="solid",  # 实线
            zorder=5,
        )
   
    label_y = -0.48
    for task_idx, task_key in enumerate(TASK_KEYS):
        x_left = TASK_LEFTS[task_idx]
        segment_width = TASK_WEIGHTS[task_idx]
        avg_x = x_left + task_average_scores[task_key] * segment_width
        avg_pct = task_average_scores[task_key] * 100.0
        ax.axvline(
            avg_x,
            color="gray",
            linewidth=0.9,
            linestyle=(0, (4, 3)),
            zorder=4,
        )
        ax.text(
            avg_x,
            label_y,
            f"{avg_pct:.1f}",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#555555",
            zorder=6,
        )

    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.6, n_models - 0.4)
    ax.invert_yaxis()

    ax.set_xticks(
        [left + width / 2 for left, width in zip(TASK_LEFTS, TASK_WEIGHTS)]
    )
    ax.set_xticklabels([f"Task {i}" for i in range(n_tasks)], fontsize=10)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(
        [MODEL_SHORT_NAMES.get(m, m) for m in models],
        fontsize=10,
    )

    ax.set_xlabel("Task Stage", fontsize=11, labelpad=6)
    ax.set_ylabel("Model", fontsize=11, labelpad=6)
    # ax.set_title(
    #     "Engineer-500 Pipeline Scores by Model and Task",
    #     fontsize=12,
    #     fontweight="bold",
    #     pad=8,
    # )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    # ax.grid(axis="x", color="#DDDDDD", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)

    legend_handles = [
        Line2D(
            [0],
            [0],
            color="#222222",
            linewidth=1.1,
            linestyle=(0, (4, 3)),
            label="Task average",
        ),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.25, 0.04),
        ncol=1,
        frameon=False,
        fontsize=9,
        columnspacing=1.2,
    )

    fig.subplots_adjust(left=0.22, right=0.98, top=0.92, bottom=0.18)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    print(output_path)


if __name__ == "__main__":
    plot_scores(load_data(DATA_PATH), OUTPUT_PATH)
