"""Per-model 5-axis radar charts + external AEI from engineer-500 aggregate metrics."""

import argparse
import json
import math
from pathlib import Path


AEI_KEY = "agent_efficiency_index"
AEI_LABEL = "AEI"


def _setup_cjk_font() -> None:
    """Prefer a CJK font on Windows so embedded captions render."""
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    candidates = (
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "Arial Unicode MS",
    )
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            return


DATA_PATH = Path(__file__).parent / "engineer-500-score.json"
OUTPUT_PATH = Path(__file__).parent / "fig_radar.pdf"

# (json_key, axis_label)
METRICS = [
    ("pipeline_stage", "Pipeline Stage"),
    ("mean_reward", "Mean\nReward"),
    ("elapsed_seconds", "Time(eff.)"),
    ("run_llm_cost_usd", "Cost(eff.)"),
    ("run_llm_total_tokens", "Tokens\n(eff.)"),
]

COLS_PER_ROW = 4
CAPTION_PATH = Path(__file__).parent / "fig_radar_caption.md"
MODEL_ORDER = [
    "claude-opus-4-7",
    "gpt-5.5",
    "deepseek-v4-pro",
    "deepseek-v4-flash",
    "qwen3.6-max-preview",
    "qwen3.5-plus",
    "deepseek-chat",
    "deepseek-reasoner",
    "qwen3-coder-flash",
    "glm-4.6",
    "glm-5.1",
    "glm-4.7",
    "kimi-k2.5",
    "kimi-k2.6",
    "minimax-m2.5",
]

# json model key -> subplot title (abbreviated)
MODEL_DISPLAY_NAMES = {
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


def model_display_name(model_key: str) -> str:
    return MODEL_DISPLAY_NAMES.get(model_key, model_key)

def build_figure_captions(maxima: dict[str, float]) -> tuple[str, str, str]:
    s_max = maxima["pipeline_stage"]
    r_max = maxima["mean_reward"]
    t_max = maxima["elapsed_seconds"]
    c_max = maxima["run_llm_cost_usd"]
    k_max = maxima["run_llm_total_tokens"]
    k_m = k_max / 1_000_000

    zh = (
        "各模型在 Engineer-500 上的多维效能画像。"
        f"五轴按当前 15 个模型的观测最大值映射至 [0,100]："
        f"Pipeline Stage 按 $0$--${s_max:.0f}$；Mean Reward 按 $0$--${r_max:.2f}$；"
        f"耗时、成本与 token 分别为 $({t_max:,.0f}-T)/{t_max:,.0f}$、"
        f"$({c_max:.2f}-C)/{c_max:.2f}$、"
        f"$({k_m:.2f}\\mathrm{{M}}-K)/{k_m:.2f}\\mathrm{{M}}$ 再乘 $100$ 并截断，"
        "半径越大表示相对该 cohort 越优。"
        "Agent Efficiency Index（AEI）为上述五维归一化得分的等权算术平均（$0$--$100$），"
        "标注于子图标题右下角；各模型子图按 AEI 从高到低排列。"
        "最后一个子图为各轴得分的平均轮廓。"
    )
    en = (
        "Multi-dimensional efficiency profiles on Engineer-500. "
        "Five radar axes map to [0,100] using cohort maxima: "
        f"pipeline stage over [0,{s_max:.0f}], mean reward over [0,{r_max:.2f}], "
        f"and inverted time/cost/token as "
        f"$({t_max:,.0f}-T)/{t_max:,.0f}$, "
        f"$({c_max:.2f}-C)/{c_max:.2f}$, and "
        f"$({k_m:.2f}\\mathrm{{M}}-K)/{k_m:.2f}\\mathrm{{M}}$ times 100 (clipped). "
        "Agent Efficiency Index (AEI) is the equal-weight mean of those five scores (0--100), "
        "shown at the bottom-right of each panel title; model panels are ordered by AEI (high to low). "
        "The final panel averages per-axis scores across models."
    )
    latex = (
        r"\caption{Multi-dimensional efficiency profiles on \textsc{Engineer-500}. "
        rf"Radar scores use cohort maxima: stage$/{s_max:.0f}$, reward$/{r_max:.2f}$, "
        rf"$(\num{{{t_max:.0f}}}-T)/\num{{{t_max:.0f}}}$, "
        rf"$(\num{{{c_max:.2f}}}-C)/\num{{{c_max:.2f}}}$, "
        rf"$(\num{{{k_m:.2f}}}\mathrm{{M}}-K)/\num{{{k_m:.2f}}}\mathrm{{M}}$ "
        r"(clipped to $[0,100]$). "
        r"AEI is the equal-weight mean of the five axis scores, shown at the bottom-right of each title; "
        r"model panels are sorted by AEI (descending). "
        r"The final panel shows mean per-axis scores across models.}"
        r"\label{fig:engineer500-radar}"
    )
    return zh, en, latex

FILL_COLOR = "#4C72B0"
FILL_ALPHA = 0.25
LINE_COLOR = "#4C72B0"
LINE_WIDTH = 1.8


def _to_float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def write_caption_files(maxima: dict[str, float], path: Path = CAPTION_PATH) -> None:
    zh, en, latex = build_figure_captions(maxima)
    body = (
        "# Figure caption: `fig_radar.pdf`\n\n"
        "## 中文（论文图注）\n\n"
        f"**图 X.** {zh}\n\n"
        "## English\n\n"
        f"**Figure X.** {en}\n\n"
        "## LaTeX\n\n"
        "```latex\n"
        f"{latex}\n"
        "```\n"
    )
    path.write_text(body, encoding="utf-8")
    print(path)


def load_data(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        return raw["models"]
    return raw


def _clip100(value: float) -> float:
    return max(0.0, min(100.0, value))


def compute_scale_maxima(records: list[dict]) -> dict[str, float]:
    """Cohort-wide maxima per metric (used as normalization denominators)."""
    maxima: dict[str, float] = {}
    for key, _ in METRICS:
        values = [_to_float(record.get(key)) for record in records]
        finite = [v for v in values if v is not None]
        if not finite:
            raise ValueError(f"No finite values for metric {key!r}")
        maxima[key] = max(finite)
        if maxima[key] <= 0:
            raise ValueError(f"Non-positive cohort maximum for {key!r}: {maxima[key]}")
    return maxima


def _score_from_raw(key: str, raw: float, maxima: dict[str, float]) -> float:
    """Map raw metric to cohort-max radar score in [0, 100]."""
    denom = maxima[key]
    if key in ("pipeline_stage", "mean_reward"):
        return _clip100(raw / denom * 100.0)
    if key in ("elapsed_seconds", "run_llm_cost_usd", "run_llm_total_tokens"):
        return _clip100((denom - raw) / denom * 100.0)
    raise KeyError(key)


def cohort_scale_scores(
    records: list[dict], key: str, maxima: dict[str, float]
) -> list[float]:
    """Per-model radar scores normalized by cohort maxima."""
    scores: list[float] = []
    for record in records:
        raw = _to_float(record.get(key))
        if raw is None:
            scores.append(0.0)
            continue
        scores.append(_score_from_raw(key, raw, maxima))
    return scores


def normalized_axis_scores(record: dict, maxima: dict[str, float]) -> list[float]:
    """Per-axis scores in [0, 100] for one model (same mapping as the radar axes)."""
    scores: list[float] = []
    for key, _ in METRICS:
        raw = _to_float(record.get(key))
        if raw is None:
            scores.append(0.0)
        else:
            scores.append(_score_from_raw(key, raw, maxima))
    return scores


def compute_aei(record: dict, maxima: dict[str, float]) -> float:
    """AEI = equal-weight mean of the five cohort-normalized axis scores."""
    axis = normalized_axis_scores(record, maxima)
    return sum(axis) / len(axis)


def sync_aei_in_records(records: list[dict], maxima: dict[str, float]) -> None:
    """Write computed AEI into each record's agent_efficiency_index field."""
    for record in records:
        record[AEI_KEY] = round(compute_aei(record, maxima), 4)


def order_records(records: list[dict], maxima: dict[str, float]) -> list[dict]:
    """Validate expected models and return records sorted by AEI (descending)."""
    by_model = {r.get("model"): r for r in records}
    missing = [model for model in MODEL_ORDER if model not in by_model]
    if missing:
        raise ValueError(f"Missing models in input data: {', '.join(missing)}")
    ordered = [by_model[model] for model in MODEL_ORDER]
    ordered.sort(key=lambda r: (-compute_aei(r, maxima), r.get("model", "")))
    return ordered


def compute_all_normalized(
    records: list[dict], maxima: dict[str, float]
) -> dict[str, list[float]]:
    return {key: cohort_scale_scores(records, key, maxima) for key, _ in METRICS}


def _draw_aei_label(ax, raw_aei: float | None) -> None:
    """AEI text at the bottom-right of the panel title (model name)."""
    label = f"{AEI_LABEL}: {raw_aei:.2f}" if raw_aei is not None else f"{AEI_LABEL}: —"
    ax.text(
        1.1,
        1.25,
        label,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color="black",
        clip_on=False,
    )


def plot_radars(
    records: list[dict],
    output_path: Path,
    metric_normed: dict[str, list[float]],
    maxima: dict[str, float],
    cols: int = COLS_PER_ROW,
) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    _setup_cjk_font()
    records = order_records(records, maxima)
    n_models = len(records)
    n_panels = n_models + 1
    n_axes = len(METRICS)
    angles = np.linspace(0, 2 * np.pi, n_axes, endpoint=False)
    angles_closed = np.concatenate([angles, angles[:1]])

    average_values = [
        float(np.mean([metric_normed[key][idx] for idx in range(n_models)]))
        for key, _ in METRICS
    ]

    rows = (n_panels + cols - 1) // cols
    fig_w = 2.2 * cols
    fig_h = 3.0 * rows
    fig, axes = plt.subplots(
        rows,
        cols,
        figsize=(fig_w, fig_h),
        subplot_kw=dict(projection="polar"),
    )
    axes_flat = np.atleast_1d(axes).ravel()

    dim_labels = [m[1] for m in METRICS]

    panels: list[tuple[str, list[float], int | None]] = [
        (
            model_display_name(record["model"]),
            [metric_normed[key][idx] for key, _ in METRICS],
            idx,
        )
        for idx, record in enumerate(records)
    ]
    panels.append(("Average", average_values, None))

    for idx, (title, values, rec_idx) in enumerate(panels):
        ax = axes_flat[idx]
        values_closed = np.concatenate([values, [values[0]]])

        ax.plot(
            angles_closed,
            values_closed,
            color=LINE_COLOR,
            linewidth=LINE_WIDTH,
            zorder=3,
        )
        ax.fill(angles_closed, values_closed, color=FILL_COLOR, alpha=FILL_ALPHA, zorder=2)

        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_thetagrids(np.degrees(angles), dim_labels, fontsize=7)
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(["25", "50", "75", "100"], fontsize=5, color="#888888")
        ax.grid(color="#CCCCCC", linewidth=0.6)
        ax.set_title(title, fontsize=9, fontweight="bold", pad=14)

        if rec_idx is not None:
            _draw_aei_label(ax, compute_aei(records[rec_idx], maxima))
        else:
            aeis = [compute_aei(r, maxima) for r in records]
            _draw_aei_label(ax, sum(aeis) / len(aeis))

    for j in range(n_panels, len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.08, wspace=0.5, hspace=0)
    save_kw: dict = {"bbox_inches": "tight"}
    if output_path.suffix.lower() != ".pdf":
        save_kw["dpi"] = 300
    fig.savefig(output_path, **save_kw)
    plt.close(fig)
    print(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cols",
        type=int,
        default=COLS_PER_ROW,
        choices=(4, 5),
        help="subplots per row (default: 4)",
    )
    parser.add_argument("-o", "--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument(
        "--write-caption",
        action="store_true",
        help="write fig_radar_caption.md",
    )
    parser.add_argument(
        "--sync-aei",
        action="store_true",
        help="recompute agent_efficiency_index in engineer-500-score.json and exit",
    )
    args = parser.parse_args()
    if args.sync_aei:
        with DATA_PATH.open(encoding="utf-8") as f:
            payload = json.load(f)
        records = payload["models"] if isinstance(payload, dict) else payload
        maxima = compute_scale_maxima(records)
        sync_aei_in_records(records, maxima)
        if isinstance(payload, dict):
            payload["normalization_maxima"] = maxima
            payload["agent_efficiency_index_formula"] = {
                "latex": (
                    r"\mathrm{AEI} = \frac{1}{5}\sum_{d \in \mathcal{D}} "
                    r"s_d,\quad \mathcal{D}=\{\mathrm{stage},\mathrm{reward},"
                    r"\mathrm{time},\mathrm{cost},\mathrm{tokens}\}"
                ),
                "description": (
                    "AEI = mean of five cohort-max scores in [0,100]: "
                    f"pipeline_stage/{maxima['pipeline_stage']}*100, "
                    f"mean_reward/{maxima['mean_reward']}*100, "
                    f"({maxima['elapsed_seconds']}-T)/{maxima['elapsed_seconds']}*100, "
                    f"({maxima['run_llm_cost_usd']}-C)/{maxima['run_llm_cost_usd']}*100, "
                    f"({maxima['run_llm_total_tokens']}-K)/{maxima['run_llm_total_tokens']}*100 "
                    "(each clipped to [0,100])"
                ),
            }
            payload["models"] = records
        DATA_PATH.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Updated AEI in {DATA_PATH}")
    else:
        records = load_data(DATA_PATH)
        maxima = compute_scale_maxima(records)
        records = order_records(records, maxima)
        metric_normed = compute_all_normalized(records, maxima)
        plot_radars(records, args.output, metric_normed, maxima, cols=args.cols)
        if args.write_caption:
            write_caption_files(maxima)
