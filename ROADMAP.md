# EvoBench 开发路线图 (ROADMAP)

## 项目概述

将中山大学 YatCC 编译原理课程实验改造为名为 "EvoBench" 的串行 Agent 评测基准。

## 设计决策记录

### 2026-05-10: Evo-CLI 架构重构

**决策 1: Harbor-like 后端抽象**
- 选择: 定义统一的 `AgentBackend` 接口，支持多个 Agent 框架
- 原因: 用户只需 `evo run --backend X --model Y` 即可切换框架
- 支持后端: openai、claude-code、openhands、codex、kimi-cli

**决策 2: CLI 入口使用 click**
- 选择: click 而非 argparse
- 原因: 更好的子命令支持和帮助信息格式化

**决策 3: score 解析兼容性修复**
- 问题: task0 的 score.py 没有写 leaderboard，导致总分解析为 0
- 修复: 当 leaderboard 无总分时，从 tests 列表计算平均分

### 2026-05-09: 初始架构设计

- 同时支持 Docker 和本地沙盒
- 复活机制通过修改 config.cmake REVIVE 标志实现
- OpenAI-compatible Tool Calling API
- 静态截断策略的上下文管理

## 跑分结果

### glm-5 (mimo-v2.5-pro) — Task 0-3

| Task | 得分 | 归一化 | 通过 | 测例 | 轮次 | Token |
|------|------|--------|------|------|------|-------|
| Task 0 | 100.0/100 | 100.0% | ✅ | 1/1 | 10 | 22654 |
| Task 1 | 17.6/100 | 17.6% | ❌ | 0/73 | 15 | 156756 |
| Task 2 | 0.0/100 | 0.0% | ❌ | 0/73 | 15 | 90219 |
| Task 3 | 1.4/100 | 1.4% | ❌ | 1/73 | 15 | 97638 |

- 流水线总分: 29.8/100
- 复活次数: 2
- 总 Token: 463290
- 总耗时: 436.1s

### deepseek-v4-pro — Task 0-3

| Task | 得分 | 归一化 | 通过 | 测例 | 轮次 | Token |
|------|------|--------|------|------|------|-------|
| Task 0 | 100.0/100 | 100.0% | ✅ | 1/1 | 11 | 23673 |
| Task 1 | 17.6/100 | 17.6% | ❌ | 0/73 | 15 | 103365 |
| Task 2 | 19.8/100 | 19.8% | ❌ | 13/73 | 15 | 100395 |
| Task 3 | 1.4/100 | 1.4% | ❌ | 1/73 | 15 | 133297 |

- 流水线总分: 34.7/100
- 复活次数: 2
- 总 Token: 614781
- 总耗时: 835.0s

## 使用方式

```bash
# 一条命令跑分
evo run --backend openai --model mimo-v2.5-pro --tasks 0-3
evo run --backend openai --model deepseek-v4-pro --tasks 0-3
evo run --backend claude-code --tasks 0-5

# 列出可用后端
evo list-backends

# 检查环境
evo check
```

## 文件结构

```
EvoBench/
├── evo_cli/                          # Evo-CLI 核心包
│   ├── __init__.py
│   ├── cli.py                        # click CLI 入口
│   ├── config.py                     # 配置管理
│   ├── orchestrator.py               # 评测编排器
│   ├── backends/
│   │   ├── __init__.py               # 后端注册表
│   │   ├── base.py                   # AgentBackend ABC
│   │   ├── openai_backend.py         # OpenAI API
│   │   ├── claude_code.py            # Claude Code CLI
│   │   ├── openhands_backend.py      # OpenHands SDK
│   │   ├── codex_backend.py          # Codex CLI
│   │   └── kimi_backend.py           # Kimi CLI
│   ├── evaluator/
│   │   └── __init__.py               # CMake 构建 + score 解析
│   ├── context/
│   │   └── __init__.py               # 上下文管理
│   └── metrics/
│       └── __init__.py               # 指标 + 报告
├── evobench_runner/                  # 原始 Runner（保留）
├── evobench_output/                  # 跑分报告
├── pyproject.toml                    # 包配置
├── .env                              # 环境变量
├── Dockerfile.evo                    # 评测沙盒镜像
├── ROADMAP.md                        # 本文件
├── idea.md                           # 项目愿景
└── YatCC/                            # 原始 YatCC 项目
```

## 已知问题 & 待办

- [ ] Agent 在 Task 1-3 表现较差，需要优化 System Prompt 或增加 max_turns
- [ ] Task 4-5 需要修复 RISC-V 工具链兼容性（clang-15 vs clang-18）
- [ ] 需要增加 Agent 行为回放（replay）功能用于调试
- [ ] openhands/codex 后端需要实际安装后测试
- [ ] 进化增益率需要对照实验验证
