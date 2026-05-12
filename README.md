# EvoBench

**串行 Agent 评测基准 — 基于编译原理实验的进化能力测评**

EvoBench 将中山大学 YatCC 编译原理课程实验改造为一个**强串行、带复活机制的动态 Agent 评测基准**。Agent 必须像人类学生一样，从词法分析（Task 1）一路写到后端代码生成（Task 5），并在前置任务的基础上不断演化其策略和代码库。

## 核心特性

- **强串行流水线**: Task 0→1→2→3→4→5，前后因果依赖
- **自动复活机制**: 前置任务失败时自动注入标准答案，继续评测后续任务
- **多后端支持**: OpenHands SDK、Claude Code、Codex CLI、Kimi CLI、Gemini CLI、OpenAI API
- **一条命令跑分**: `evo run --backend openhands --model mimo-v2.5-pro --tasks 0-5`
- **完整评测报告**: JSON/CSV/Markdown 多格式输出

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/Nexa-Language/EvoBench.git
cd EvoBench

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 安装 Python 依赖
pip install -e .

# 准备 YatCC 依赖（ANTLR + LLVM + pybind11）
cd data/YatCC && bash antlr/setup.sh && bash llvm/setup.sh && bash pybind11/setup.sh && cd ../..
```

### 2. 运行评测

```bash
# 使用 OpenAI-compatible API
evo run --backend openai --model mimo-v2.5-pro --tasks 0-5

# 使用 OpenHands SDK（真正的 Agent 框架）
# 需要 Python 3.12+
uv venv .venv-openhands --python 3.12
. .venv-openhands/bin/activate
uv pip install openhands-sdk openhands-tools

python src/run_openhands.py --model mimo-v2.5-pro --tasks 0-5

# 使用 Claude Code
evo run --backend claude-code --tasks 0-5

# 使用 Codex CLI
evo run --backend codex --tasks 0-5

# 使用 Kimi CLI
evo run --backend kimi --tasks 0-5

# 检查环境
evo check
```

### 3. 查看报告

```bash
cat evobench_output/evobench_report.md
```

## 评测任务

| Task | 名称 | 内容 | 输入 |
|------|------|------|------|
| 0 | 环境准备 | 确认开发环境 | - |
| 1 | 词法分析 | 实现 Lexer | 预处理后的 C 源码 |
| 2 | 语法分析 | 实现 Parser | Token 流 |
| 3 | 中间代码生成 | 生成 LLVM IR | AST/JSON |
| 4 | 中间代码优化 | 实现 LLVM Pass | LLVM IR |
| 5 | 后端代码生成 | 生成 RV64 汇编 | 优化后的 IR |

## 评测指标

| 指标 | 说明 |
|------|------|
| **独立通关率** | 不依赖复活，一口气通关到 Task 5 |
| **节点通过率** | 单个 Task 的通过率 |
| **平均复活次数** | 完成全部 Task 所需复活次数（越低越好） |
| **进化增益率** | Agent 理解自己代码的能力 |

## 跑分结果

### OpenHands SDK + 各模型（2026-05-11）

| 排名 | 模型 | Pipeline | T0 | T1 | T2 | T3 | T4 | T5 | 复活 |
|------|------|----------|-----|-----|-----|-----|-----|-----|------|
| 1 | qwen3.6-plus | 88.0 | 100 | 100 | 74.0 | 72.6 | 81.1 | 100 | 2 |
| 2 | glm-5 | 77.1 | 100 | 100 | 100 | 100 | 62.5 | 100 | 1 |
| 3 | minimax-m2.5 | 75.5 | 100 | 100 | 0 | 72.6 | 80.2 | 100 | 2 |
| 4 | qwen3.5-plus | 73.3 | 100 | 100 | 0 | 53.4 | 86.6 | 100 | 2 |
| 5 | deepseek-v4-pro | 66.7 | 100 | 100 | 100 | 100 | 0 | 0 | 2 |
| 6 | qwen3-coder-flash | 65.3 | 100 | 100 | 0 | 34.2 | 57.8 | 100 | 3 |
| 7 | kimi-k2-thinking | 63.5 | 100 | 0 | 100 | 100 | 60.0 | 100 | 2 |
| 8 | deepseek-reasoner | 63.5 | 100 | 0 | 21.1 | 100 | 60.0 | 100 | 2 |
| 9 | deepseek-chat | 63.5 | 100 | 0 | 21.1 | 100 | 60.0 | 100 | 2 |
| 10 | qwen3.6-max-preview | 59.6 | 100 | 60.5 | 100 | 97.3 | 0 | 0 | 3 |

> 完整 22 个模型数据请访问 [Leaderboard](https://evobench.nexa-lang.com/leaderboard.html)

## 项目结构

```
EvoBench/
├── src/                    # 源代码
│   ├── evo_cli/            # Evo-CLI（多后端框架）
│   ├── run_openhands.py    # OpenHands SDK runner
│   ├── run_cli_agent.py    # CLI agent runner（claude/codex/gemini/kimi）
│   └── metrics.py          # 指标计算 & leaderboard 生成
├── data/                   # 基准数据
│   ├── YatCC/              # YatCC 编译器项目（submodule）
│   ├── YatCC-docs/         # YatCC 文档
│   └── task_guides.md      # 精简版任务指南（注入 Agent 上下文）
├── eval/                   # 评测
│   ├── results/            # 评测结果（JSON）
│   ├── logs/               # 执行日志（gitignored）
│   └── workspaces/         # Agent 工作区（gitignored）
├── site/                   # 网站（GitHub Pages）
│   ├── index.html          # 主页（粒子效果）
│   ├── leaderboard.html    # 交互式 Leaderboard
│   └── blog.html           # Blog（可展开文章）
└── .github/workflows/      # GitHub Actions（自动部署）
```

## Agent 后端

| 后端 | 类型 | 特性 | 安装 |
|------|------|------|------|
| `openhands` | 真正 Agent | 无限自循环、Skill、MCP | `pip install openhands-sdk` |
| `claude-code` | CLI Agent | 文件读写、命令执行 | 安装 Claude Code |
| `codex` | CLI Agent | 自动编码 | 安装 Codex CLI |
| `kimi-cli` | CLI Agent | 对话式编码 | 安装 Kimi CLI |
| `openai` | API 调用 | Tool Calling | `pip install openai` |

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 检查环境
evo check
```

## 引用

```bibtex
@misc{evobench2026,
  title={EvoBench: A Serial Agent Benchmark with Resurrection Mechanism},
  author={EvoBench Team},
  year={2026},
  url={https://github.com/Nexa-Language/EvoBench}
}
```

## 致谢

- [YatCC](https://github.com/arcsysu/YatCC) — 中山大学编译原理课程实验
- [OpenHands](https://github.com/All-Hands-AI/OpenHands) — Agent 框架

## License

MIT
