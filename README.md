# EvoBench

**串行 Agent 评测基准 — 基于编译原理实验的进化能力测评**

EvoBench 将中山大学 YatCC 编译原理课程实验改造为一个**强串行、带复活机制的动态 Agent 评测基准**。Agent 必须像人类学生一样，从词法分析（Task 1）一路写到后端代码生成（Task 5），并在前置任务的基础上不断演化其策略和代码库。

## 核心特性

- **强串行流水线**: Task 0→1→2→3→4→5，前后因果依赖
- **自动复活机制**: 前置任务失败时自动注入标准答案，继续评测后续任务
- **多后端支持**: OpenAI API、Claude Code、OpenHands SDK、Codex CLI、Kimi CLI
- **一条命令跑分**: `evo run --backend openai --model mimo-v2.5-pro --tasks 0-5`
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
cd YatCC && bash antlr/setup.sh && bash llvm/setup.sh && bash pybind11/setup.sh && cd ..
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
python run_openhands.py --model mimo-v2.5-pro --tasks 0-5

# 使用 Claude Code
evo run --backend claude-code --tasks 0-3

# 指定任务范围
evo run --backend openai --tasks 0-3

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

### OpenHands SDK + mimo-v2.5-pro

| Task | 得分 | 通过 | 测例 |
|------|------|------|------|
| Task 0 | 100.0% | ✅ | 1/1 |
| Task 1 | 17.6% | ❌ | 0/73 |
| Task 2 | 19.8% | ❌ | 13/73 |
| Task 3 | 1.4% | ❌ | 1/73 |

## 项目结构

```
EvoBench/
├── evo_cli/                  # Evo-CLI 核心包
│   ├── cli.py                # evo 命令入口
│   ├── config.py             # 配置管理
│   ├── orchestrator.py       # 评测编排器
│   ├── backends/             # Agent 后端
│   │   ├── base.py           # AgentBackend ABC
│   │   ├── openai_backend.py # OpenAI API
│   │   ├── claude_code.py    # Claude Code CLI
│   │   ├── openhands_backend.py # OpenHands SDK
│   │   ├── codex_backend.py  # Codex CLI
│   │   └── kimi_backend.py   # Kimi CLI
│   ├── evaluator/            # CMake 构建 + 评分
│   ├── context/              # 上下文管理
│   └── metrics/              # 指标 + 报告
├── run_openhands.py          # OpenHands SDK 独立 runner
├── evobench_runner/          # 原始 Runner（保留）
├── pyproject.toml            # 包配置
├── .env.example              # 环境变量示例
├── YatCC/                    # 编译原理实验项目
└── docs/                     # 文档
```

## Agent 后端

| 后端 | 类型 | 特性 | 安装 |
|------|------|------|------|
| `openai` | API 调用 | Tool Calling | `pip install openai` |
| `openhands` | 真正 Agent | 无限自循环、Skill、MCP | `pip install openhands-sdk` |
| `claude-code` | CLI | 文件读写、命令执行 | 安装 Claude Code |
| `codex` | CLI | 自动编码 | 安装 Codex CLI |
| `kimi-cli` | CLI | 对话式编码 | 安装 Kimi CLI |

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
  howpublished={\url{https://github.com/Nexa-Language/EvoBench}}
}
```

## 致谢

- [YatCC](https://github.com/arcsysu/YatCC) — 中山大学编译原理课程实验
- [OpenHands](https://github.com/All-Hands-AI/OpenHands) — Agent 框架

## License

MIT
