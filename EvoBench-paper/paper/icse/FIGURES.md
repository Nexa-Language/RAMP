# EVA 论文配图需求描述

## 示意图（需手绘/TikZ/draw.io，共 2 张）

### 示意图 1：系统架构总览图
- **位置**：第 2 节（Framework Design），跨双栏全宽
- **内容**：从上到下五层架构，每层用圆角矩形表示，层与层之间用浅色水平线分隔。
  1. **Observation & Leaderboard Layer**（观测与排行榜层）：包含 Metrics Dashboard、Leaderboard Web、Failure Taxonomy、Process Logs 四个子模块。
  2. **Task Orchestrator**（任务编排器）：包含 Scheduling（T0→T5）、Dependency Resolution、Resurrection Trigger、Pipeline Management 四个子模块。
  3. **Agent Runtime Layer**（Agent 运行时层）：四个并排的 Agent 框架——OpenHands SDK、Claude Code、Codex CLI、Kimi CLI。
  4. **Model Access Layer / AIhub**（模型接入层）：一个横跨全宽的 API Gateway 盒子，标注 "Unified API Gateway (aihub.arcsysu.cn)"，下方列出支持的模型系列。
  5. **Execution Environment**（执行环境）：左右两个并排盒子——"YatCC Workspace (CMake + LLVM 14)" 和 "YatCC-Hard Container (Isolated, Ephemeral)"。
- **风格**：白底，干净简约。各层用不同浅色背景区分（蓝/紫/绿/橙/灰）。模块用圆角矩形，带轻微阴影。字体无衬线，层级标题加粗。

### 示意图 2：串行依赖链与复活机制
- **位置**：第 2.3 节（Workloads），单栏宽度
- **内容**：从左到右六个任务节点（T0→T1→T2→T3→T4→T5），实线箭头连接，箭头上标注传递的中间产物（Token Stream、AST/ASG、LLVM IR、Optimized IR、RV64 Assembly）。每个任务节点下方有一个虚线边框的 "Golden Artifact" 盒子。当任务失败时，红色虚线箭头从失败任务指向对应的 Golden Artifact，表示复活注入。底部汇总标注 "Resurrection triggers when score < 60%"。
- **风格**：任务节点蓝色圆角矩形，Golden Artifact 绿色虚线边框，复活箭头红色虚线。紧凑，适合单栏。

---

## 统计图表（matplotlib 生成，共 4 张，已有 PNG）

### 图表 1：Per-Task Score Heatmap（已有：`fig_score_heatmap.png`）
- 横轴 22 模型，纵轴 6 任务，颜色从红（0 分）到绿（100 分），每格标注分数。

### 图表 2：Resurrection Gain（已有：`fig_resurrection_gain.png`）
- 柱状图，每个模型两根柱子（无复活 vs 有复活的 Pipeline Score），差值标注。

### 图表 3：Cost-Performance Frontier（已有：`fig_cost_performance.png`）
- 散点图，X 轴耗时，Y 轴 Pipeline Score，Pareto 前沿线，按 Backend 着色。

### 图表 4：Failure Taxonomy（已有：`fig_failure_taxonomy.png`）
- 堆叠柱状图，五种失败类型，有/无复活两个子图对比。

---

## 通用规范
- **配色**：蓝 #3b82f6 / 绿 #22c55e / 橙 #f59e0b / 红 #ef4444 / 灰 #6b7280，白底
- **尺寸**：单栏宽 3.5in，全宽 7.16in，≥300 DPI，字体 ≥8pt
- **LaTeX**：单栏 `\includegraphics[width=\linewidth]`，全宽 `\includegraphics[width=\textwidth]`（需 `figure*` 环境）