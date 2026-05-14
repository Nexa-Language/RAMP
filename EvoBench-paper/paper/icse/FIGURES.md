# EVA 论文配图需求描述

## 图 1：系统架构总览图
- **类型**：分层架构示意图
- **位置**：第 2 节（Framework Design），跨双栏全宽
- **内容**：从上到下五层架构
  1. **最顶层：Observation & Leaderboard Layer**（观测与排行榜层）。包含四个子模块：Metrics Dashboard（指标仪表盘）、Leaderboard Web（网页排行榜）、Failure Taxonomy（失败分类）、Process Logs（过程日志，记录 tokens、turns 等）。用浅蓝色背景。
  2. **第二层：Task Orchestrator**（任务编排器）。包含四个子模块：Scheduling（T0→T5 调度）、Dependency Resolution（依赖解析）、Resurrection Trigger（复活触发器）、Pipeline Management（流水线管理）。用浅紫色背景。
  3. **第三层：Agent Runtime Layer**（Agent 运行时层）。四个并排的 Agent 框架：OpenHands SDK、Claude Code、Codex CLI、Kimi CLI。每个用不同的小图标区分。用浅绿色背景。
  4. **第四层：Model Access Layer / AIhub**（模型接入层）。一个横跨全宽的 API Gateway 盒子，标注 "Unified API Gateway (aihub.arcsysu.cn)"，下面列出 "21 Models: GPT, Claude, DeepSeek, Qwen, GLM, ..."。用浅橙色背景。
  5. **最底层：Execution Environment**（执行环境）。左右两个并排的盒子：左边是 "YatCC Workspace (CMake + LLVM 14)"，右边是 "YatCC-Hard Container (Isolated, Ephemeral)"。用浅灰色背景。
- **风格**：干净、简约、白底。每层之间用浅色水平线分隔。各模块用圆角矩形，带轻微阴影。颜色柔和，不要过于鲜艳。字体使用无衬线体，层级标题加粗。

## 图 2：串行依赖链与复活机制流程图
- **类型**：水平流程图
- **位置**：第 2.3 节（Workloads），单栏宽度
- **内容**：从左到右六个任务节点（T0→T1→T2→T3→T4→T5），用实线箭头连接，箭头上标注传递的中间产物名称（Token Stream、AST/ASG、LLVM IR、Optimized IR、RV64 Assembly）。每个任务节点下方有一个虚线边框的"Golden Artifact"盒子（金色/绿色），当任务失败时，红色虚线箭头从失败任务指向对应的 Golden Artifact，表示复活注入。底部有一个汇总箭头标注"Resurrection Injection (when score < 60%)"。
- **风格**：任务节点用蓝色圆角矩形，Golden Artifact 用绿色虚线边框矩形，复活箭头用红色虚线。整体紧凑，适合单栏宽度。

## 图 3：复活收益分布图
- **类型**：柱状图（matplotlib 生成）
- **位置**：第 4.2 节（Resurrection），单栏宽度
- **内容**：X 轴为模型名称（按复活收益降序排列），Y 轴为 Pipeline Score。每个模型两根柱子：蓝色为无复活分数，绿色为有复活分数。两根柱子之间的差值用数字标注。GPT-5.5 等零复活模型两根柱子等高。
- **风格**：标准学术柱状图，颜色柔和，有网格线辅助读数。图例简洁。

## 图 4：成本-性能前沿图
- **类型**：散点图（matplotlib 生成）
- **位置**：第 4.4 节（Process Diagnostics），单栏宽度
- **内容**：X 轴为总耗时（秒），Y 轴为 Pipeline Score。每个模型一个散点，标注模型名称。用不同颜色区分 Backend（OpenHands、Kimi CLI、Claude Code、Codex CLI）。画一条 Pareto 前沿线连接最优点。标注几个极端案例：qwen3.6-flash（高分低耗时）和 deepseek-reasoner（中分高耗时）。
- **风格**：标准学术散点图，颜色柔和，Pareto 线用虚线。

## 图 5：失败分类构成图
- **类型**：堆叠柱状图（matplotlib 生成）
- **位置**：第 4.4 节（Process Diagnostics），单栏宽度
- **内容**：X 轴为模型名称，Y 轴为失败次数。五种失败类型用不同颜色堆叠：predecessor failure（红）、task-local reasoning failure（橙）、execution failure（黄）、process collapse（蓝）、cost overrun（灰）。左右两个子图分别展示"无复活"和"有复活"两种设置下的失败分布。
- **风格**：标准学术堆叠柱状图，颜色区分明显但不过于鲜艳，有图例。

## 图 6：YatCC vs YatCC-Hard 难度差距图
- **类型**：分组柱状图（matplotlib 生成）
- **位置**：第 4.5 节（Scaffolding Gap），单栏宽度
- **内容**：X 轴为同时在两个 workload 上评测的模型名称（按 YatCC-Hard 分数降序排列），Y 轴为 Pipeline Score。每个模型两根柱子：蓝色为 YatCC 分数，橙色为 YatCC-Hard 分数。两根柱子之间的差值用数字标注在柱子上方。重点标注 kimi-k2.6（差距最大，从 99.3 跌到 64.9）和 mimo-v2.5-pro（从 98.9 跌到 0）。
- **风格**：标准学术分组柱状图，颜色柔和，差值标注清晰。

---

## 通用配色规范（IEEEtran 兼容）
- 主蓝色：#3b82f6
- 成功绿：#22c55e
- 警告橙：#f59e0b
- 危险红：#ef4444
- 中性灰：#6b7280
- 背景：白色
- 文字：#1a1a2e

## 通用尺寸规范
- 单栏图：宽度 = 3.5 英寸（IEEEtran 单栏宽）
- 跨双栏全宽图：宽度 = 7.16 英寸（IEEEtran 文本宽）
- 分辨率：≥ 300 DPI
- 字体大小：≥ 8pt
- 所有图片白底，不要深色背景
- LaTeX 中使用 `\includegraphics[width=\linewidth]`（单栏）或 `\includegraphics[width=\textwidth]`（全宽）