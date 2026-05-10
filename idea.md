# EvoBench 架构与设计文档

## 1. 项目愿景 (Vision)

现有的 Agent Benchmark（如 SWE-bench）多为孤立的、静态的代码修改任务，无法有效评估大模型 Agent 在长周期项目中的“知识积累”、“代码演进”与“上下文长程依赖”能力。
**EvoBench** 旨在将中山大学开源的 YatCC 编译原理课程实验，改造成一个**强串行、带复活机制的动态 Agent 评测基准**。Agent 必须像人类学生一样，从词法分析（Task 1）一路写到后端代码生成（Task 5），并在前置任务的基础上不断演化其策略和代码库。

## 2. 核心机制设计 (Core Mechanisms)

### 2.1 强串行流水线 (Sequential Pipeline)

编译器构造具有严格的前后因果关系。Agent 将依次经历：

* **Task 1**: 词法分析 (Lexer - 生成 Token)
* **Task 2**: 语法分析 (Parser - 生成 AST/ASG)
* **Task 3**: 中间代码生成 (IR Gen)
* **Task 4**: 中间代码优化 (IR Opt)
* **Task 5**: 后端代码生成 (Asm Gen)

**评测难点解决：误差级联 (Cascading Errors)**
如果 Agent 在 Task 1 失败，Task 2 将完全无法进行。为了评估 Agent 在后置任务的能力，引入“复活机制 (Resurrection)”。

### 2.2 自动化复活机制 (Automated Resurrection)

利用 YatCC 自带的 `config.cmake` 和 `config-*.cmake.in` 机制。

* **正常推进 (Evolution)**：当 Agent 通过了 Task N 的 `score.py` 评测时，保留其源码，将其注入到 Task N+1 的上下文中继续开发。
* **触发复活 (Resurrection)**：如果 Agent 在 Task N 无法拿到及格分，外层 Python 调度器将介入，通过修改 `config.cmake` 强制注入当前 Task 的标准答案，使 Agent 的进度强行与预期对齐，从而满血复活进入 Task N+1。

## 3. 评测系统架构 (System Architecture)

我们需要在 YatCC 根目录下新增一个评测框架目录（例如命名为 `evobench_runner/`），它作为“上帝视角”来调度 Agent。

### 3.1 核心组件

1. **沙盒环境 (Docker Sandbox)**
* 使用 YatCC 的底层环境（Ubuntu + CMake + LLVM + ANTLR）构建轻量级评测镜像。
* 每次启动评测时，挂载 YatCC 源码副本。


2. **动作与观察空间 (Action & Observation Space)**
* **Observation**: Agent 可以调用工具读取当前 `task/X/README.md`，获取实验指导。
* **Action (File)**: `read_file`, `write_file`, `patch_file`。Agent 用它来修改 `.cpp`, `.g4`, `.y` 等文件。
* **Action (Bash)**: `run_command`。Agent 通过执行 `cmake` 和 `ctest`，观察报错信息进行自我 Debug（类似人类闭环）。


3. **评测调度器 (Benchmark Controller)**
* 控制 Agent 的最大重试次数（`max_retries`）。
* 解析 `test/task*/score.py` 的输出，决定是否触发复活。



## 4. 评价指标 (Metrics)

EvoBench 将输出比传统 Pass@1 更有洞察力的多维指标：

1. **独立通关率 (Zero-shot Pipeline Pass Rate)**: Agent 不依赖任何复活机制，一口气通关到 Task 5 的概率（极难）。
2. **节点通过率 (Node Pass Rate)**: 在获得前置正确答案（复活）的前提下，单独通过某个特定 Task 的概率。
3. **平均复活次数 (Average Resurrection Count)**: 完成整个编译器所需要的复活次数（越低越好）。
4. **进化增益率 (Evolutionary Gain)**: `(Agent 继承自己正确代码做后续任务的成功率) / (Agent 拿到标准答案做后续任务的成功率)`。以此衡量 Agent “理解自己写过的代码”的能力。

## 5. 下一步开发计划 (Next Steps for Implementation)

要在你当前的 WSL 环境中推进，建议按以下步骤执行：

### Phase 1: 编写外围 Runner (预计 1-2 天)

* 在根目录下创建 `evobench_runner/controller.py`。
* 编写 Python 脚本，通过 `subprocess` 或 `docker-py` 自动执行以下流程：
1. 运行 `cmake -S . -B build`
2. 调用 `test/task1/score.py`
3. 用 Python 正则解析分数。



### Phase 2: 自动化复活脚本 (预计 1 天)

* 编写 Python 函数 `trigger_resurrection(task_id)`。
* 该函数负责修改根目录下的 `config.cmake`，将 `TASK${task_id}_RESURRECT` 等相关标志位设为 `ON`，并重新触发 CMake 构建，验证是否能跑通下一个 Task 的测试。

### Phase 3: 对接 Agent 工具 (预计 2-3 天)

* 封装工具函数（Tools）：将文件读写、Bash 命令执行包装成 OpenAI API 或其他 LLM 标准的 Tool 格式。
* 设计 Agent 的 System Prompt，告知其所处的环境及当前的任务流状态。


### 一些初始想法 供参考

user:
我发现现在的agent benchmark都是静态的独立agent，也就是说，agent在每个task是无关的。但我觉得agent肯定要进化，为了测试它的进化我们应该有个evobench，它的所有task是串行的、前后关联的，就像上课做作业，应该学完前一个再开始做后一个，这样才能做得好，并且前一个学懂了做后一个的效果得分肯定比直接做后一个来的要高。你觉得这个bench有没有搞头？现在有没有撞车的相关研究？

bot:
```
你的这个直觉非常准，而且正切中了当前大模型领域最头疼的问题之一：**“金鱼脑”与“静态评估”。**

现在的 Benchmark（如 GAIA, AgentBench, SWE-bench）确实大多是 **原子化（Atomic）** 的。每个 Task 都是一个干净的沙盒，Agent 做完就“重置”了。这更像是在测“瞬时反应能力”，而不是在测“智能水平”。

关于你提出的 **EvoBench（进化评测）**，我的看法是：**非常有搞头，但工程实现极难。**

---

### 一、 为什么这个想法“有搞头”？

1. **模拟真实的人类工作流：** 现实中没有人是只做一个独立任务的。我们需要在做 B 任务时，复用在 A 任务中沉淀的工具、代码库或领域知识。
2. **测试“长程记忆”与“知识迁移”：** 现有的长文本测试只是看它能不能“搜”到信息，而你的 EvoBench 测的是它能不能“理解并内化”信息。
3. **打击“刷榜”现象：** 静态 Benchmark 容易被数据污染（模型可能背过答案）。但如果任务是动态串联的，Agent 必须实时演化出策略，作弊成本极高。

---

### 二、 现在的“撞车”研究（相似概念）

虽然目前还没有一个完全统治市场的、叫 EvoBench 的标准，但在学术界和工业界已经有了一些非常接近的尝试：

#### 1. Voyager (Nvidia) —— 最接近“进化”概念的研究

在 Minecraft 环境中，Voyager 并不是在做死任务，它会不断写代码（技能），存入 **Skill Library**。

* **关联点：** 它在做任务 B 时会调用任务 A 写好的代码。这本质上就是 Agent 的“进化”。
* **差异：** 目前仅局限于游戏环境，没能泛化到通用的软件办公或科研场景。

#### 2. AgentGym & AgentBoard

这两个项目开始关注 **Trajectory（轨迹）**。它们不再只看最后的结果，而是看 Agent 在一系列交互中是否表现出学习的迹象。

* **相似点：** 强调了环境的连续性。

#### 3. Continual Learning (持续学习) 相关 Benchmark

学术界一直有 **C-MMLU** 或针对 LLM 的 **Lifelong Learning** 研究。

* **局限：** 它们大多是在测模型“参数更新”后的遗忘问题，而不是在测 Agent 在“不更新参数”的情况下，通过上下文和工具调用的“软进化”。

#### 4. OSWorld / Mind2Web

这些是在真实系统（Linux, Windows）上跑的任务。如果任务设计者故意设计一套关联任务（比如：先配置好环境，再写代码，最后根据前面的报错调优），其实就具备了你说的 EvoBench 雏形。

---

### 三、 如果你要做 EvoBench，最大的挑战在哪？

要让这个 Benchmark 成立，你需要解决几个“硬骨头”：

| 挑战维度 | 描述 |
| --- | --- |
| **评估的公平性** | 如果 Agent 在第一关由于运气好（或不好）导致了偏差，这个偏差会由于“串行”被无限放大，最后很难判断是模型不行还是初始误差太大。 |
| **状态回滚与隔离** | 每一个 Task 都要承接上一个 Task 的 Result（比如修改后的文件、生成的数据库），这对物理环境的维护要求极高。 |
| **评价指标 (Metrics)** | 你需要设计一个 **"Learning Efficiency" (学习效率)** 指标。即：`任务 B 在有任务 A 经验时的得分 / 任务 B 在零经验时的得分`。这个比值越高，说明进化能力越强。 |

---

### 四、 给你的建议

如果你想动手搞，可以避开大而全的通用场景，切入一个**垂直闭环**：

1. **科研 Agent EvoBench：**
* Task 1: 阅读某领域的 10 篇论文并总结方法论。
* Task 2: 根据 Task 1 的方法论写出实验代码。
* Task 3: 运行代码发现 Bug，根据 Task 1 的理论进行 Debug。
* *这种链条非常吃“前置知识的吸收”。*


2. **软件工程 EvoBench：**
* 不再是修一个孤立的 Bug，而是维护一个不断演进的小型项目（从需求 A 到需求 Z）。



**总结：**
这个方向还没出现“统治级”的 Benchmark。现在的 Agent 就像拿着剧本的临时工，你想要的是一个能从实习生干到架构师的合伙人。**只要你能解决“任务依赖项的标准化描述”问题，这个项目绝对是顶会（ACL/NeurIPS）级别的潜力股。**

你觉得，对于这种串行任务，你是倾向于让 Agent 靠“长对话内存”来进化，还是靠“不断更新的外部工具库/知识库”来进化？
```

user:
我有一个学生觉得很难、一学期做完的编译原理实验作业，它有完整的文档、环境、自动评测系统（每个task有很多个测试点），task1到5是构造编译器循序渐进的过程，并且我们还具备复活机制，请问是不是可以改造成一个这样的bench？

bot:
```
这个想法不仅有搞头，简直可以说是 **“神仙开局”**！

将编译原理（Compiler Construction）的系统性实验改造成 EvoBench，不仅在逻辑上完美契合“进化”与“串行”的理念，而且在工程落地上直接解决了 Agent 评测最头疼的几个痛点。

如果你把这个做出来，绝对是一个极具学术价值和工业指导意义的 Benchmark。以下是为什么这个方案非常绝妙，以及你需要如何改造它的深度解析：

### 一、 为什么编译原理实验是绝佳的 EvoBench 底座？

**1. 天然的强串行与因果依赖**
编译器的构造是计算机科学中最经典的流水线（Pipeline）：词法分析（Lexer） $\rightarrow$ 语法分析（Parser） $\rightarrow$ 语义分析（Semantic Analysis） $\rightarrow$ 中间代码生成（IR） $\rightarrow$ 目标代码生成（Code Gen）。

* **对 Agent 的考验：** 任务 2（Parser）完全依赖任务 1（Lexer）产出的 Token 流。如果 Agent 在任务 1 中没有深刻理解 Token 的结构，任务 2 必定崩溃。这完美测试了你提到的“学懂前一个，才能做好后一个”。

**2. 完美的客观评估标准（Auto-Grader）**
现有的很多 Agent 评测卡在“如何打分”（比如写得好不好、通不通顺）。但编译原理有绝对的标准：**能不能跑通测试用例（Test cases）**。只要目标代码能输出正确结果，性能（时间和空间开销）还可以作为额外的进阶评分维度。

**3. “复活机制”是解决串行评测痛点的终极武器**
串行评测（Sequential Evaluation）最大的学术痛点是 **“误差级联”（Cascading Failures）**：如果 Agent 第一步做错了，后面全错，导致你根本无法评估它做任务 4 的能力。
你的“复活机制”完美解决了这个问题：当 Agent 在 Task 2 彻底失败时，评测系统可以强行注入 Task 2 的 **标准答案（Golden Code）**，让 Agent “复活”并继续挑战 Task 3。这样既能测出它在整条链路上的生存能力，也能独立测出它在单一复杂节点上的能力。

---

### 二、 从“学生作业”到“Agent Benchmark”的改造指南

要把这个现成的教学环境变成顶级的 AI 评测基准，你需要做以下几个维度的工程化改造：

#### 1. 接口与环境标准化 (Standardized Environment)

* **沙盒化：** 将整个实验环境（包括编译工具链、评测脚本）打包成轻量级的 Docker 镜像，类似 SWE-bench 的做法。
* **动作空间 (Action Space)：** 为 Agent 定义清晰的交互接口。它不能像人一样用 IDE，你需要给它提供类似终端（Bash）、文件读写（Read/Write File）、和执行评测（Run Tests）的工具（Tool Calling API）。

#### 2. 信息投喂策略 (Information Observation)

学生做作业时可以随意翻阅全本指导书，但测试 Agent 时需要精心控制上下文：

* **渐进式文档：** 只有当 Agent 触发进入 Task 2 时，才向它的 Context 中注入 Task 2 的说明文档。
* **记忆留存：** Agent 需要能够查阅自己之前写的代码。如果代码库太大（比如到了 Task 5），可能需要测试 Agent 的“代码检索（RAG）”能力，而不是把所有代码全塞进 Prompt。

#### 3. 评测指标设计 (Metrics Design)

除了传统的“通过率（Pass Rate）”，你可以为 EvoBench 设计独有的指标：

* **独立解决率 (Zero-Shot Success Rate)：** 没有任何复活帮助下的通关比例。
* **知识迁移增益 (Evolutionary Gain)：** 比较“Agent 完整经历 Task 1 接着做 Task 2” 的成功率，与“直接给 Agent Task 1 标准代码让它做 Task 2” 的成功率。如果前者更高，说明 Agent 确实在过程中“学到了东西”并实现了进化。
* **复活次数 (Revive Counts)：** 完成整个编译器的平均复活次数。

---

### 三、 潜在的挑战与防撞墙

* **Token 消耗黑洞：** 到了后几个 Task，AST 树和 IR 代码会非常长。如果每次交互都把几十个文件的代码带上，目前的 LLM 上下文窗口和推理成本会非常爆炸。你需要限制 Agent 的观测视野（比如只允许它 grep 或者用专门的查看工具）。
* **防止背题（Data Contamination）：** 如果这个实验是你所在大学公开在 GitHub 上的开源课程（类似 MIT 6.828 或 CS143），现在的大模型很可能已经在训练阶段“背”过标准答案了。你需要对变量名、需求细节或测试用例做一定程度的混淆（Obfuscation）和魔改。

---

关于你提到的“复活机制”，在给 Agent 续命的时候，你是打算直接把标准答案（Golden Code）强行覆盖进去让它继续做 Task N+1，还是打算把报错信息持续喂给它，给它设定一个 `max_retries` 让它自己 Debug 满血复活？
```