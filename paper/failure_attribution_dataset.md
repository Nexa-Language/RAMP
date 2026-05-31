# Failure Attribution Dataset (14 Models)

以下数据根据运行日志、人工标注和论文中的失败分类整理而成。

## Failure Categories

- `execution_failure`: 构建错误、依赖问题、工具调用错误、文件损坏等
- `process_collapse`: 重复搜索/调试但长期无有效进展
- `cost_overrun`: 时间或 API 预算耗尽
- `strategic_task_skipping`: 模型主动决定跳过任务
- `context_window_exhaustion`: 因上下文长度超过模型限制而终止

## Data Format

```json
{
  "model": "...",
  "attribution": [
    {"tasks": "task1-task2", "failure": "strategic_task_skipping"},
    {"tasks": "task3", "failure": "context_window_exhaustion"}
  ],
  "notes": "..."
}
```

---

```json
[
  {
    "model": "deepseek-chat",
    "attribution": [
      {"tasks": "task2-task3", "failure": "strategic_task_skipping"},
      {"tasks": "task3", "failure": "context_window_exhaustion"}
    ],
    "notes": "在 Task 2 评估任务工作量后倾向于停止深入实现，最终在进入 Task 3 前后因上下文过长终止。"
  },
  {
    "model": "deepseek-reasoner",
    "attribution": [
      {"tasks": "task1", "failure": "execution_failure"},
      {"tasks": "task1-task2", "failure": "strategic_task_skipping"},
      {"tasks": "task3", "failure": "context_window_exhaustion"}
    ],
    "notes": "Task 1 文件被破坏导致无法编译，随后明确声明跳过 Task 1 和 Task 2，最终因上下文过长终止。"
  },
  {
    "model": "deepseek-v4-flash",
    "attribution": [
      {"tasks": "task2-task4", "failure": "strategic_task_skipping"}
    ],
    "notes": "多次根据时间限制主动结束当前任务并转向后续任务。"
  },
  {
    "model": "deepseek-v4-pro",
    "attribution": [
      {"tasks": "task3-task4", "failure": "strategic_task_skipping"}
    ],
    "notes": "明确放弃 Task 4，优先完成范围更清晰的 Task 5。"
  },
  {
    "model": "glm-4.7",
    "attribution": [
      {"tasks": "task1-task2", "failure": "execution_failure"},
      {"tasks": "task2", "failure": "context_window_exhaustion"}
    ],
    "notes": "多次出现 str_replace 缺少 new_str 参数的工具调用错误，最终因上下文过长终止。"
  },
  {
    "model": "glm-5.1",
    "attribution": [
      {"tasks": "task1", "failure": "execution_failure"},
      {"tasks": "task2", "failure": "context_window_exhaustion"}
    ],
    "notes": "Task 1 存在环境或读分异常，随后在中期任务阶段触发上下文长度限制。"
  },
  {
    "model": "glm-4.6",
    "attribution": [
      {"tasks": "task2-task3", "failure": "process_collapse"},
      {"tasks": "task3", "failure": "context_window_exhaustion"}
    ],
    "notes": "缺乏显式规划，持续编辑与调试但进展有限，最终上下文耗尽。"
  },
  {
    "model": "kimi-k2.6",
    "attribution": [
      {"tasks": "task2-task4", "failure": "strategic_task_skipping"},
      {"tasks": "task5", "failure": "context_window_exhaustion"}
    ],
    "notes": "多个任务以“由于时间和资源限制，建议继续下一任务”结束，最终因上下文过长终止。"
  },
  {
    "model": "kimi-k2.5",
    "attribution": [
      {"tasks": "task2-task4", "failure": "strategic_task_skipping"}
    ],
    "notes": "与 kimi-k2.6 相同，倾向于在任务尚未完成时转向后续任务。"
  },
  {
    "model": "gpt-5.5",
    "attribution": [],
    "notes": "未观察到显著的失败模式；任务在 Task 4 后自然结束，Task 5 未完成但无明确异常行为。"
  },
  {
    "model": "claude-opus-4-7",
    "attribution": [],
    "notes": "未观察到显著的失败模式。"
  },
  {
    "model": "qwen3.6-max-preview",
    "attribution": [
      {"tasks": "task3", "failure": "context_window_exhaustion"}
    ],
    "notes": "在完成前期任务后，于 Task 3 附近触发上下文长度限制。"
  },
  {
    "model": "qwen3.5-plus",
    "attribution": [
      {"tasks": "task2", "failure": "execution_failure"},
      {"tasks": "task3-task5", "failure": "strategic_task_skipping"}
    ],
    "notes": "Task 3 文件编辑导致语法错误和重复定义，随后认为后续任务依赖受阻而主动放弃。"
  },
  {
    "model": "qwen3-coder-flash",
    "attribution": [
      {"tasks": "task1-task3", "failure": "process_collapse"}
    ],
    "notes": "思考轮次极少，在早期任务中持续尝试但未形成有效推进。"
  },
  {
    "model": "minimax-m2.5",
    "attribution": [
      {"tasks": "task1-task2", "failure": "execution_failure"},
      {"tasks": "task3", "failure": "context_window_exhaustion"}
    ],
    "notes": "工具使用能力较弱，经历大量终端操作和长时间搜索后最终触发上下文长度限制。"
  }
]
```

---

# Summary Statistics (Primary Signals)

> 一个模型可同时具有多个失败归因，因此总数超过 14。

| Failure Type | Models | Ratio |
|-----------|------:|------:|
| context_window_exhaustion | 9 | 64.3% |
| strategic_task_skipping | 7 | 50.0% |
| execution_failure | 6 | 42.9% |
| process_collapse | 4 | 28.6% |
| cost_overrun | 0 (通常作为 strategic_task_skipping 的显式理由出现) | 0.0% |

## Interpretation

- **Context-window exhaustion** 是最普遍的终止机制，也是最客观、最容易自动识别的系统瓶颈。
- **Strategic task skipping** 是第二常见行为，说明大量模型在面对高工作量任务时倾向于主动放弃，而非持续求解。
- **Execution failure** 广泛存在于工具调用、文件编辑和编译阶段。
- **Process collapse** 主要表现为高轮数搜索与重复调试，但没有形成有效状态变化。
- **Cost overrun** 更多表现为模型的主观担忧，而非系统强制终止，因此在论文中更适合作为 strategic task skipping 的动机解释，而不是独立的主要标签。

