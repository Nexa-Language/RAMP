# OpenHands + YatCC 并行评测容器使用指南

目标：

- 每个模型一个容器。
- 每个容器使用镜像内独立的 `/workspace/YatCC`，互不共享 YatCC 工作区。
- OpenHands 在容器内运行，不在 Windows 宿主机跑。
- 每个 run 有独立输出目录，包含控制台日志、评测报告、OpenHands event/message JSONL。

当前已具备的能力：

- `Dockerfile.evo` 已安装 `openhands-sdk` / `openhands-tools`。
- `src/run_openhands.py` 已支持 `--run-id`、`--output-dir`。
- `src/run_openhands.py` 会把 OpenHands events 写到 `openhands-events/*.jsonl`，SDK 状态写到 `openhands-state/`。

## 0. 项目部署

1. 将本项目拉取到服务器上。

2. 在 `data/YatCC/` 目录下，拉取 YatCC 项目:  `https://gitlab.arcsysu.cn/huangx385/yatcc-hard.git`。

3. 上下文：准备好 `YatCC/` 的文档。构建镜像时，会自动将 `YatCC/` 复制到镜像内。此外，在镜像之外， `data\task_guides.md` 也提供了上下文。具体逻辑见 `eval\launch_openhands_containers.sh` 。


## 1. 构建标准镜像

在 bash 执行：

```powershell
cd EvoBench-main/

docker build -f Dockerfile.evo -t evobench-openhands:latest --build-arg LLVM_BUILD_JOBS_MAX=48   --build-arg HTTP_PROXY="${HTTP_PROXY}"   --build-arg HTTPS_PROXY="${HTTPS_PROXY}"   --build-arg NO_PROXY="${NO_PROXY}"   --build-arg http_proxy="${http_proxy}"   --build-arg https_proxy="${https_proxy}"   --build-arg no_proxy="${no_proxy}"   .
```

含义：

- `docker build` 构建镜像。
- `-f Dockerfile.evo` 指定使用项目里的任务环境镜像文件。
- `-t evobench-openhands:latest` 给镜像起标准名字。
- `.` 表示构建上下文是当前目录。

如果这一步成功，以后在服务器上跑 OpenHands bench 就统一用镜像 `evobench-openhands:latest`。


## 3. 运行评测容器

在 bash 终端下运行如下命令启动多个评测容器：

```shell
cd EvoBench-main/

bash eval/launch_openhands_containers.sh \
  --models minimax-m2.7,minimax-m2.5 \
  --tasks 0-5 \
  --max-iterations 1000 \
  --context-mode pipeline \
  --parallel 4 \
  --run-prefix "run-pipeline-"
```

### 参数详解

- `--models minimax-m2.7,minimax-m2.5`  
  指定本次评测要测试的多个模型，多个模型用英文逗号分隔，可根据需要修改。例如也可使用 `--all-models` 评测所有 models.json 中的模型，或用 `--model xxx` 重复多次只评测部分模型。

- `--tasks 0-5`  
  指定评测任务的范围（第0到5号任务）。也可用如 `0,2,4` 评测特定任务。

- `--max-iterations 1000`  
  每个任务最多允许运行多少轮，防止陷入死循环。

- `--context-mode pipeline`  
  指定上下文模式：  
  - `per-task`（默认）：每个 Task 从空对话开始。  
  - `pipeline`：所有任务用同一对话进行，连续执行，有利于多轮推理。

- `--parallel 4`  
  最多同时启动 4 个任务容器并发评测，按需调整以适配硬件资源。

- `--run-prefix "run-pipeline-"`  
  所有本次运行结果输出目录、容器名称都会带上该前缀。

### 运行流程说明

`eval/launch_openhands_containers.sh` 脚本的主要工作包括：

1. 针对每个模型、每组 tasks，自动分配评测实验（Experiment），组合出 run_id。
2. 按需分配 API KEY（支持多模型/多 key 自动映射）。
3. 自动为每个 Experiment 单独创建输出目录（如 `eval/container-runs/run-pipeline-xxxx/`），输出包括控制台日志、events、评测报告等。
4. 为每个容器挂载独立的 `/workspace/YatCC`，各评测间互不影响，保证并发纯净。
5. 脚本自动将 `src/run_openhands.py` 参数正确传递给容器，包括模型名、tasks、context-mode、run-id、输出目录及复活（resurrect）等。
6. 支持传递 OpenHands LLM 缓存相关参数（如 `--cache-prompt`, `--no-cache-prompt`, `--prompt-cache-retention`）。
7. 容器在 wall-clock 超时后会被自动 kill，防止异常挂死。
8. 各容器的输出均可在对应 output 目录中查看详细日志、事件流及最终分数。
9. 脚本执行结束后，可手动或脚本自动进行结果收集与汇总。

> ⚠️ 若需批量自定义实验方案，可准备文本文件用 `--experiments-file FILE`，格式可参考脚本帮助说明。

**更多启动参数说明和自定义用法，请执行：**
```shell
bash eval/launch_openhands_containers.sh --help
```

**评测中产生的全部输出均位于 `eval/container-runs/` 下，不会和宿主机其他环境混用，便于追溯和复现。**