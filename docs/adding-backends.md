# 添加新的 Agent 后端

RAMP 设计为可扩展的评测框架，支持任意 Agent 框架接入。

## 步骤

### 1. 创建后端文件

在 `ramp_cli/backends/` 下创建新文件，如 `my_backend.py`:

```python
from .base import AgentBackend, TaskContext, TaskResult

class MyBackend(AgentBackend):
    name = "my-backend"

    def __init__(self, model: str = "", **kwargs) -> None:
        super().__init__(model=model)

    def is_available(self) -> bool:
        """检查依赖是否安装"""
        try:
            import my_agent_lib
            return True
        except ImportError:
            return False

    def get_description(self) -> str:
        return f"My Backend ({self.model})"

    def solve_task(
        self,
        task_id: int,
        workspace: Path,
        context: TaskContext,
        max_turns: int = 20,
    ) -> TaskResult:
        result = TaskResult(task_id=task_id)
        t_start = time.time()

        # 组装提示词
        prompt = context.to_prompt()

        # 调用你的 Agent 框架
        # Agent 应该在 workspace 中自由操作
        # ...

        result.elapsed_seconds = time.time() - t_start
        return result
```

### 2. 注册后端

在 `ramp_cli/backends/__init__.py` 的 `_BACKEND_REGISTRY` 中添加:

```python
_BACKEND_REGISTRY = {
    ...
    "my-backend": "ramp_cli.backends.my_backend:MyBackend",
}
```

### 3. 测试

```bash
ramp list-backends  # 确认新后端出现
ramp check          # 确认后端可用
ramp run --backend my-backend --tasks 0  # 测试
```

## 关键要求

1. **Agent 必须在 workspace 中操作**: 读写文件、执行命令
2. **Agent 应该自主迭代**: 不限制轮次，直到任务完成
3. **Agent 应该有完整工具**: 文件读写、命令执行、任务追踪
4. **返回 TaskResult**: 包含 success、turns、elapsed_seconds
