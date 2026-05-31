"""Time/Cost vs Performance scatter plots with token-sized bubbles and vendor logos."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Annotation
from PIL import Image, ImageDraw

DATA_PATH = Path(__file__).parent / "engineer-500-score.json"
LOGO_DIR = Path(__file__).parent / "model_logo"
OUTPUT_PATH = Path(__file__).parent / "fig_scatter.pdf"
FIGURES_PATH = Path(__file__).resolve().parents[2] / "figures" / "fig_cost_performance.pdf"

# Table 3 (tab:main) / tab:model_groups abbreviations.
MODEL_DISPLAY_NAMES: dict[str, str] = {
    "claude-opus-4-7": "Opus-4.7",
    "deepseek-v4-pro": "DS-v4-Pro",
    "gpt-5.5": "GPT-5.5",
    "deepseek-v4-flash": "DS-v4-Flash",
    "qwen3.6-max-preview": "Qwen-3.6-Max",
    "kimi-k2.5": "Kimi-2.5",
    "kimi-k2.6": "Kimi-2.6",
    "glm-4.6": "GLM-4.6",
    "deepseek-chat": "DS-Chat",
    "qwen3.5-plus": "Qwen-3.5-Plus",
    "glm-4.7": "GLM-4.7",
    "glm-5.1": "GLM-5.1",
    "qwen3-coder-flash": "Qwen3-Coder",
    "minimax-m2.5": "MiniMax-2.5",
    "deepseek-reasoner": "DS-Reasoner",
}

# Same pixel canvas for every vendor logo before display scaling.
LOGO_PX = 128
SAVE_DPI = 300
# Per-model label ray (deg) so vendor siblings do not share the same direction.
_LABEL_ANGLES_DEG = (35, 95, 155, 215, 275, 50, 130, 210, 290, 20, 110, 200, 260, 70, 170)
MODEL_LABEL_ANGLE_DEG: dict[str, float] = {
    model: _LABEL_ANGLES_DEG[i % len(_LABEL_ANGLES_DEG)]
    for i, model in enumerate(sorted(MODEL_DISPLAY_NAMES))
}
_LABEL_PAD_PT = 12.0
_AXIS_LABEL_MARGIN_PX = 8.0
_NUDGE_MAX_ITERS = 48
_REPEL_OVERLAP_ITERS = 80
_REPEL_OVERLAP_PUSH_PT = 3.5
_REPEL_OVERLAP_PAD_PX = 5.0
_REPEL_ANCHOR_WEIGHT = 0.1
# Font sizes tuned for print/PDF legibility at single-column width.
FONT_MODEL_LABEL = 14
FONT_AXIS_LABEL = 14
FONT_AXIS_TICK = 12
FONT_SUBPLOT_TITLE = 15
FONT_LEGEND = 14
_LOGO_CACHE: dict[Path, np.ndarray] = {}

PERF_KEY = "mean_reward"
TIME_KEY = "elapsed_seconds"
COST_KEY = "run_llm_cost_usd"
TOKEN_KEY = "run_llm_total_tokens"


def load_data(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    return raw["models"] if isinstance(raw, dict) else raw


def model_display_name(model: str) -> str:
    """Map JSON model id to Table~3 display name."""
    return MODEL_DISPLAY_NAMES.get(model, model)


def vendor_logo_path(model: str) -> Path:
    # return LOGO_DIR / "3.jpg"
    m = model.lower()
    if m.startswith("deepseek"):
        return LOGO_DIR / "deepseek.webp"
    if m.startswith("glm"):
        return LOGO_DIR / "glm.webp"
    if m.startswith("kimi"):
        return LOGO_DIR / "kimi.webp"
    if m.startswith("gpt"):
        return LOGO_DIR / "openai.png"
    if m.startswith("qwen"):
        return LOGO_DIR / "qwen.png"
    if m.startswith("minimax"):
        return LOGO_DIR / "minimax.webp"
    if m.startswith("claude"):
        return LOGO_DIR / "claude.jfif"
    raise ValueError(f"No logo mapping for model: {model}")


def pareto_mask(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Non-dominated points when minimizing x and maximizing y."""
    n = len(x)
    mask = np.ones(n, dtype=bool)
    for i in range(n):
        if not mask[i]:
            continue
        dominated = (x <= x[i]) & (y >= y[i]) & ((x < x[i]) | (y > y[i]))
        dominated[i] = False
        if np.any(dominated):
            mask[i] = False
    return mask


def pareto_curve_xy(
    x: np.ndarray, y: np.ndarray, mask: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    pts = sorted(zip(x[mask], y[mask]), key=lambda t: t[0])
    if not pts:
        return np.array([]), np.array([])
    frontier_x, frontier_y = [pts[0][0]], [pts[0][1]]
    best_y = pts[0][1]
    for xi, yi in pts[1:]:
        if yi > best_y:
            frontier_x.append(xi)
            frontier_y.append(yi)
            best_y = yi
    return np.asarray(frontier_x), np.asarray(frontier_y)


def _token_norm(tokens: np.ndarray) -> np.ndarray:
    t_min, t_max = tokens.min(), tokens.max()
    if t_max <= t_min:
        return np.full_like(tokens, 0.5, dtype=float)
    return (tokens - t_min) / (t_max - t_min)


def scale_bubble_sizes(tokens: np.ndarray, min_pt: float = 80.0, max_pt: float = 1100.0) -> np.ndarray:
    return min_pt + _token_norm(tokens) * (max_pt - min_pt)


def logo_zoom_from_scatter(ax: plt.Axes, scatter) -> np.ndarray:
    """Match OffsetImage diameter to scatter marker diameter (display pixels)."""
    fig = ax.figure
    fig.set_dpi(SAVE_DPI)
    fig.canvas.draw()
    dpi = fig.dpi

    edge_pt = scatter.get_linewidths()
    edge_pt = 0.0 if edge_pt is None else float(np.atleast_1d(edge_pt)[0])
    edge_px = edge_pt * dpi / 72.0

    zooms = np.empty(len(scatter.get_offsets()), dtype=float)
    for i, trans in enumerate(scatter.get_transforms()):
        radius_px = float(np.hypot(trans[0, 0], trans[0, 1]))
        diam_px = 2.0 * radius_px + 2.0 * edge_px
        zooms[i] = diam_px * 72.0 / (LOGO_PX * dpi)
    return zooms


def logo_radius_pt(zoom: float, dpi: float) -> float:
    """On-plot logo radius in points (matches OffsetImage sizing)."""
    return LOGO_PX * zoom * 72.0 / dpi / 2.0


def label_offset_pt(model: str, zoom: float, dpi: float) -> tuple[float, float]:
    """Place label outside the logo along a per-model compass ray."""
    dist = logo_radius_pt(zoom, dpi) + _LABEL_PAD_PT
    deg = MODEL_LABEL_ANGLE_DEG.get(model, 40.0)
    rad = np.deg2rad(deg)
    return dist * np.cos(rad), dist * np.sin(rad)


def _px_to_offset_pt(px: float, dpi: float) -> float:
    return px * 72.0 / dpi


def _bbox_center(bb) -> tuple[float, float]:
    return (bb.x0 + bb.x1) / 2.0, (bb.y0 + bb.y1) / 2.0


def _bboxes_overlap(b1, b2, pad_px: float) -> bool:
    return not (
        b1.x1 <= b2.x0 - pad_px
        or b1.x0 >= b2.x1 + pad_px
        or b1.y1 <= b2.y0 - pad_px
        or b1.y0 >= b2.y1 + pad_px
    )


def _label_inside_axes(bb, ax_bb, margin_px: float) -> bool:
    return (
        bb.x0 >= ax_bb.x0 + margin_px
        and bb.x1 <= ax_bb.x1 - margin_px
        and bb.y0 >= ax_bb.y0 + margin_px
        and bb.y1 <= ax_bb.y1 - margin_px
    )


def _set_ann_offset(ann: Annotation, offset: np.ndarray) -> None:
    """Write offset-points position (matplotlib 3.8+ uses ``xyann``)."""
    ann.xyann = (float(offset[0]), float(offset[1]))


def nudge_annotations_inside_axes(
    ax: plt.Axes,
    annotations: list[Annotation],
    offsets: list[np.ndarray],
) -> None:
    """Shift labels inward when they spill past the plotting area."""
    if not annotations:
        return
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    ax_bb = ax.get_window_extent(renderer)
    margin = _AXIS_LABEL_MARGIN_PX
    dpi = fig.dpi

    for ann, offset in zip(annotations, offsets):
        for _ in range(_NUDGE_MAX_ITERS):
            _set_ann_offset(ann, offset)
            fig.canvas.draw()
            bb = ann.get_window_extent(renderer)
            if _label_inside_axes(bb, ax_bb, margin):
                break
            if bb.x0 < ax_bb.x0 + margin:
                offset[0] += _px_to_offset_pt(ax_bb.x0 + margin - bb.x0, dpi)
            if bb.x1 > ax_bb.x1 - margin:
                offset[0] -= _px_to_offset_pt(bb.x1 - (ax_bb.x1 - margin), dpi)
            if bb.y0 < ax_bb.y0 + margin:
                offset[1] += _px_to_offset_pt(ax_bb.y0 + margin - bb.y0, dpi)
            if bb.y1 > ax_bb.y1 - margin:
                offset[1] -= _px_to_offset_pt(bb.y1 - (ax_bb.y1 - margin), dpi)
            # Pull slightly toward the marker so labels do not hug the border.
            offset *= 0.9
        _set_ann_offset(ann, offset)


def repel_overlapping_labels(
    ax: plt.Axes,
    annotations: list[Annotation],
    offsets: list[np.ndarray],
    initial_offsets: list[np.ndarray],
) -> None:
    """Slightly separate overlapping model-name boxes."""
    if len(annotations) < 2:
        return
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    anchors = [np.array(o, dtype=float) for o in initial_offsets]

    for _ in range(_REPEL_OVERLAP_ITERS):
        for ann, offset in zip(annotations, offsets):
            _set_ann_offset(ann, offset)
        fig.canvas.draw()
        boxes = [ann.get_window_extent(renderer) for ann in annotations]
        moved = False

        for i in range(len(annotations)):
            for j in range(i + 1, len(annotations)):
                if not _bboxes_overlap(boxes[i], boxes[j], _REPEL_OVERLAP_PAD_PX):
                    continue
                ci = _bbox_center(boxes[i])
                cj = _bbox_center(boxes[j])
                vx = ci[0] - cj[0]
                vy = ci[1] - cj[1]
                norm = float(np.hypot(vx, vy))
                if norm < 1e-6:
                    vx, vy, norm = 1.0, 0.0, 1.0
                push = _REPEL_OVERLAP_PUSH_PT
                offsets[i][0] += push * vx / norm
                offsets[i][1] += push * vy / norm
                offsets[j][0] -= push * vx / norm
                offsets[j][1] -= push * vy / norm
                moved = True

        for offset, anchor in zip(offsets, anchors):
            offset += _REPEL_ANCHOR_WEIGHT * (anchor - offset)
        if not moved:
            break

    for ann, offset in zip(annotations, offsets):
        _set_ann_offset(ann, offset)


def circular_logo_array(logo_path: Path, size: int = LOGO_PX) -> np.ndarray:
    """Center-crop source image to a square, resize, then apply a circular mask."""
    if logo_path in _LOGO_CACHE:
        return _LOGO_CACHE[logo_path]

    img = Image.open(logo_path).convert("RGBA")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((size, size), Image.Resampling.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    alpha = np.asarray(mask, dtype=np.float32) / 255.0
    arr = np.asarray(img, dtype=np.float32)
    arr[:, :, 3] *= alpha
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    _LOGO_CACHE[logo_path] = arr
    return arr


def regression_line(
    ax: plt.Axes, x: np.ndarray, y: np.ndarray, log_x: bool, color: str
) -> None:
    if log_x:
        x_fit = np.log10(np.maximum(x, np.finfo(float).tiny))
        x_line = np.logspace(np.log10(x.min()), np.log10(x.max()), 100)
    else:
        x_fit = x
        x_line = np.linspace(x.min(), x.max(), 100)
    coef = np.polyfit(x_fit, y, 1)
    y_line = np.polyval(coef, np.log10(x_line) if log_x else x_line)
    ax.plot(x_line, y_line, color=color, linewidth=1.6, linestyle="--", alpha=0.85, zorder=2)


def add_logo(
    ax: plt.Axes,
    x: float,
    y: float,
    logo_path: Path,
    zoom: float,
    zorder: int = 6,
) -> None:
    img = circular_logo_array(logo_path)
    imagebox = OffsetImage(img, zoom=zoom)
    ab = AnnotationBbox(
        imagebox,
        (x, y),
        frameon=False,
        pad=0.0,
        zorder=zorder,
    )
    ax.add_artist(ab)


def plot_average_lines(ax: plt.Axes, x: np.ndarray, y: np.ndarray) -> None:
    x_mean = float(np.mean(x))
    y_mean = float(np.mean(y))
    ax.axhline(
        y_mean,
        color="#888888",
        linewidth=1.2,
        linestyle=(0, (4, 3)),
        zorder=2,
    )
    ax.axvline(
        x_mean,
        color="#888888",
        linewidth=1.2,
        linestyle=(0, (4, 3)),
        zorder=2,
    )


def plot_panel(
    ax: plt.Axes,
    records: list[dict],
    x_key: str,
    x_label: str,
    title: str,
    log_x: bool,
) -> None:
    x = np.array([r[x_key] for r in records], dtype=float)
    y = np.array([r[PERF_KEY] for r in records], dtype=float)
    tokens = np.array([r[TOKEN_KEY] for r in records], dtype=float)
    sizes = scale_bubble_sizes(tokens)

    if log_x:
        ax.set_xscale("log")

    plot_average_lines(ax, x, y)
    regression_line(ax, x, y, log_x=log_x, color="#555555")

    scatter = ax.scatter(
        x,
        y,
        s=sizes,
        c="#B8C9E0",
        alpha=0.55,
        edgecolors="#6B7F99",
        linewidths=0.8,
        zorder=3,
    )
    zooms = logo_zoom_from_scatter(ax, scatter)

    # pmask = pareto_mask(x, y)
    # px, py = pareto_curve_xy(x, y, pmask)
    # if len(px) > 0:
    #     ax.plot(
    #         px,
    #         py,
    #         color="#C44E52",
    #         linewidth=2.0,
    #         linestyle="-",
    #         zorder=4,
    #         label="Pareto frontier",
    #     )

    for rec, xi, yi, zoom in zip(records, x, y, zooms):
        add_logo(
            ax,
            float(xi),
            float(yi),
            vendor_logo_path(rec["model"]),
            zoom=float(zoom),
        )

    label_bbox = dict(
        boxstyle="round,pad=0.2",
        facecolor="white",
        edgecolor="none",
        alpha=0.88,
    )
    dpi = ax.figure.dpi
    annotations: list[Annotation] = []
    label_offsets: list[np.ndarray] = []
    initial_offsets: list[np.ndarray] = []
    for rec, xi, yi, zoom in zip(records, x, y, zooms):
        dx, dy = label_offset_pt(rec["model"], float(zoom), dpi)
        ha = "left" if dx >= 0 else "right"
        va = "bottom" if dy >= 0 else "top"
        offset = np.array([dx, dy], dtype=float)
        label_offsets.append(offset)
        initial_offsets.append(offset.copy())
        ann = ax.annotate(
            model_display_name(rec["model"]),
            (float(xi), float(yi)),
            xytext=(float(offset[0]), float(offset[1])),
            textcoords="offset points",
            fontsize=FONT_MODEL_LABEL,
            color="#1A1A1A",
            ha=ha,
            va=va,
            bbox=label_bbox,
            clip_on=False,
            zorder=10,
        )
        annotations.append(ann)
    nudge_annotations_inside_axes(ax, annotations, label_offsets)
    repel_overlapping_labels(ax, annotations, label_offsets, initial_offsets)
    nudge_annotations_inside_axes(ax, annotations, label_offsets)

    ax.set_xlabel(x_label, fontsize=FONT_AXIS_LABEL)
    ax.set_ylabel("MR", fontsize=FONT_AXIS_LABEL)
    ax.set_title(title, fontsize=FONT_SUBPLOT_TITLE, fontweight="bold", pad=10)
    ax.tick_params(axis="both", labelsize=FONT_AXIS_TICK)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, which="both", color="#DDDDDD", linewidth=0.5, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)


def plot_scatter(records: list[dict], output_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.2))

    plot_panel(
        axes[0],
        records,
        TIME_KEY,
        "Elapsed Time (s)",
        "Time vs Performance",
        log_x=True,
    )
    plot_panel(
        axes[1],
        records,
        COST_KEY,
        "Cost ($)",
        "Cost vs Performance",
        log_x=True,
    )

    legend_handles = [
        # Line2D([0], [0], color="#C44E52", linewidth=2.0, label="Pareto frontier"),
        Line2D([0], [0], color="#555555", linewidth=1.6, linestyle="--", label="Regression line"),
        Line2D(
            [0],
            [0],
            color="#888888",
            linewidth=1.2,
            linestyle=(0, (4, 3)),
            label="Mean (horizontal & vertical)",
        ),
        Patch(facecolor="#B8C9E0", edgecolor="#6B7F99", alpha=0.55, label="Bubble & logo size ∝ tokens"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=3,
        frameon=False,
        fontsize=FONT_LEGEND,
        handlelength=2.4,
        handletextpad=0.8,
        columnspacing=1.6,
        bbox_to_anchor=(0.5, 0.02),
    )

    fig.set_dpi(SAVE_DPI)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.90, bottom=0.17, wspace=0.28)
    fig.savefig(
        output_path,
        format=output_path.suffix.lstrip(".") or "pdf",
        dpi=SAVE_DPI,
        bbox_inches="tight",
    )
    print(output_path)


if __name__ == "__main__":
    records = load_data(DATA_PATH)
    plot_scatter(records, OUTPUT_PATH)
    plot_scatter(records, FIGURES_PATH)
