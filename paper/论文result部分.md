4. 失败归因/分类，尽量量化：“为什么大部分模型止步于t3”（统计图）
5. 具体两个事例分析，识别 agent 工作行为、心理韧性、（各 task 时间开销收集）
6. Imc 对比：上下文影响：agent


**失败归因**
这里的失败是模型完成任务的失败，因素是场景的因素。
- 
- 

1. deepseek-chat 要求不高、被工作量吓退、对自己能力没有清晰认知。
out of context length limit

t0 127轮，实际上是干了 t0和t1
terminal  268  61.3%
file_editor  128  29.3%
task_tracker  18  4.1%
think  10  2.3%
finish  6  1.4%
user  6  1.4%
system  1  0.2%
─────────────────────────
合计  437  100.0%

Task 1 已经实现了功能完整的词法分析器，能够正确识别 C 语言子集的所有关键 token，输出格式与 clang 高度一致。72.93 分的成绩表明词法分析器在大多数测试用例上工作良好，为后续编译阶段奠定了坚实基础。

Task 2 的改进主要集中在修复程序崩溃问题，使语法分析器能够为更多测试用例产生输出。30.89 分的成绩反映了基础框架的工作情况，但语法分析器还需要大量扩展才能处理完整的 C 语言子集。
考虑到时间限制（约4.5小时）和 Task 2 的预计工作量（1000-2000行代码），当前成果是合理的。
当前实现为后续改进奠定了基础，但需要大量额外工作才能达到高分。

结束于上下文太长。没有截断机制？

2. "deepseek-reasoner 
file_editor  134  62.9%
terminal  70  32.9%
user  6  2.8%
assistant  2  0.9%
system  1  0.5%
─────────────────────────
合计  213  100.0%

把t1的代码搞崩了无法编译，哪怕之前拿了 57.14 分，但决定跳过。

#74 Given the constraints, we will skip further debugging of Task 1 and Task 2 and proceed to Task 3, 4, and 5.
 
结束于上下文太长。

3. "deepseek-v4-flash
真实的任务分配：7 60 166 60 53 37
terminal  481  63.1%
file_editor  236  31.0%
task_tracker  22  2.9%
think  9  1.2%
user  6  0.8%
assistant  5  0.7%
finish  2  0.3%
system  1  0.1%
─────────────────────────
合计  762  100.0%

#233 I could spend more time expanding the grammar, but given the time constraints, let me move on to Task 3 (IR generation) which builds on Tasks 1 and 2.

#293 Given the time constraints, let me take a practical approach. Task 3 already has a decent framework and the issues are subtle and debugging without a debugger is time-consuming. Let me focus on moving to Task 4 and 5 where the work is more clearly defined (4 functions to implement).

#346 However, given the time constraints, the score is competitive. Let me finish up with a summary.


4. "deepseek-v4-pro
真实的任务分配：7 69 57 122+45 3+18 28
terminal  458  65.1%
file_editor  204  29.0%
task_tracker  26  3.7%
user  6  0.9%
assistant  5  0.7%
finish  2  0.3%
think  2  0.3%
system  1  0.1%
─────────────────────────
合计  704  100.0%

做完了实验 0125，实验3才40分，实验4没做，居然刚好遇到要求完成实验三的 user prompt 。于是模型回去做实验三。

#286 The user wants me to continue working on Task 3 (IR Generation). Let me check the current state of the code and score, then work on improving the score from 42.47 to as high as possible.

跳过 t4 只因 t5 文件更简单
#257 Let me focus on Task 5 since it has a clear scope - just 4 functions to implement. Task 4 might require more complex IR transformations.


5. "glm-4.7 
out of context length limite

file_editor  270  49.4%
terminal  266  48.6%
user  6  1.1%
think  4  0.7%
system  1  0.2%
─────────────────────────
合计  547  100.0%

Tool Error
真实的任务分配：8 154

模型的工具调用能力不足：
28次出现："Parameter `new_str` is required for command: str_replace."

此外就是太笨了，连 t1 都做不好，根本没法继续往下走.


6. "glm-5.1
out of context length limite
terminal  302  64.3%
file_editor  125  26.6%
think  16  3.4%
task_tracker  14  3.0%
user  6  1.3%
finish  4  0.9%
assistant  1  0.2%
system  1  0.2%
tool  1  0.2%
─────────────────────────
合计  470  100.0%
挺稳定的，t1有 100 分，只是容器环境不稳定导致读分错误的问题。

7. "glm-4.6
out of context length limite
file_editor  273  72.6%
terminal  86  22.9%
finish  10  2.7%
user  6  1.6%
system  1  0.3%
─────────────────────────
合计  376  100.0%

太笨了，没有思考

8. "kimi-k2.6
out of context length limite
terminal  583  87.5%
file_editor  42  6.3%
think  32  4.8%
user  6  0.9%
finish  2  0.3%
system  1  0.2%
─────────────────────────
合计  666  100.0%

每个实验都以下面这种输出结束：
#239 由于时间和资源限制，当前实现仅支持基础功能。建议继续到 Task 4。

9. "kimi-k2.5
真实的任务分配：9 154
terminal  304  52.3%
file_editor  230  39.6%
task_tracker  22  3.8%
finish  12  2.1%
think  6  1.0%
user  6  1.0%
system  1  0.2%
─────────────────────────
合计  581  100.0%

#239 由于时间和资源限制，当前实现仅支持基础功能。建议继续到 Task 4。

10. "gpt-5.5
terminal  90  50.8%
file_editor  50  28.2%
task_tracker  26  14.7%
user  6  3.4%
assistant  4  2.3%
system  1  0.6%
─────────────────────────
合计  177  100.0%

11. "qwen3.6-max-preview
out of context length limite
terminal  184  46.3%
file_editor  170  42.8%
think  30  7.6%
finish  6  1.5%
user  6  1.5%
system  1  0.3%
─────────────────────────
合计  397  100.0%

12.  "qwen3.5-plus
不太会使用 tool
terminal  324  81.6%
file_editor  34  8.6%
finish  12  3.0%
task_tracker  10  2.5%
think  10  2.5%
user  6  1.5%
system  1  0.3%
─────────────────────────
合计  397  100.0%

担心时间限制
#136 Given the ~4 hours remaining and the complexity of this task (estimated 1000-2000 lines of code as noted in the README), I recommend focusing on getting the basic infrastructure working correctly first, then incrementally adding features.

让文件没法 build，害怕了就跑了
#184 Task 3 implementation encountered issues during incremental editing. The EmitIR.cpp file has syntax errors from multiple append operations that created duplicate function definitions and corrupted the file structure.

#198 **Task 4: IR Optimization** - Not started
- Depends on Task 3 working correctly
**Task 5: Backend (RV64)** - Not started
- Depends on Task 4 working correctly


13. "qwen3-coder-flash"
几乎没有思考
file_editor  68  48.6%
terminal  54  38.6%
user  6  4.3%
assistant  5  3.6%
think  4  2.9%
finish  2  1.4%
system  1  0.7%
─────────────────────────
合计  140  100.0%

14. "minimax-m2.5
不太会使用 tool
out of context length limit

terminal  607  71.8%
file_editor  214  25.3%
finish  8  0.9%
task_tracker  6  0.7%
user  6  0.7%
think  3  0.4%
system  1  0.1%
─────────────────────────
合计  845  100.0%



失败分类
├── Tool Error
├── out of context length limite
├── Search Error
├── Build Error
├── Test Failure
├── Timeout
├── Cost Limit
├── Environment Error
├── Submission Error
└── No Progress

不太会使用 tool（70%以上）: minimax-m2.5、qwen3.5-plus、kimi-k2.6

out of context length limite: minimax-m2.5、 qwen3.6-max-preview、 kimi-k2.6、 glm-4.6、 glm-5.1、 glm-4.7 、 deepseek-chat

主动跳过：qwen3.5-plus、kimi-k2.5、kimi-k2.6、deepseek-v4-flash、deepseek-reasoner 、deepseek-chat、

**事例分析**
针对不同失败归因，打开执行过程内部做分析

最好能量化：
message 类型比例：




**Imc 对比**
唯一的因素就是agent的长程工作带来的影响。这里倒是能讲讲agent的上下文截断了。






## 未来启示
若要演示当前 agent prompt 机制，可以用 deepseek-v4-pro 的例子。

对未来实验框架的启示：不要搞自动提示。试试只有在开头进行提示？

\subsection{Comprehensive Metric Analysis}

\subsubsection{Agent Productivity Index}

The preceding subsections analyze task completion, progressive workload behavior, cost-performance trade-offs, and failure mechanisms separately.
We now ask a more operational question: \emph{how much engineering utility does an agent produce per unit of aggregate resource consumption?}
To answer this question, we use the Agent Productivity Index (API), a composite productivity metric that combines task utility and resource efficiency:
\[
\mathrm{API}
=
1000 \times
\frac{
\sqrt{P \cdot R}
}{
\sqrt[3]{T \cdot C \cdot K}
},
\]
where $P$ denotes the pipeline score, $R$ denotes the mean reward, $T$ is the execution time, $C$ is the monetary cost, and $K$ is the total token usage.
Higher API values indicate greater engineering productivity, reflecting better task utility per unit of aggregate resource consumption.
Because API uses the geometric mean of pipeline score and reward in the numerator, it rewards agents that make useful progress across the benchmark rather than optimizing only one scoring view.
Because the denominator is the cubic root of time, cost, and token usage, it penalizes agents that obtain similar utility through longer execution, higher monetary expense, or heavier context consumption.
Figure~\ref{fig:efficiency_profiles} visualizes this trade-off directly by plotting pipeline score, mean reward, inverted wall-clock time, inverted LLM cost, inverted token usage, and API on a common normalized scale.
The resulting shapes should be interpreted as relative quality--efficiency profiles rather than absolute measurements, since each axis is min--max normalized across models.
One run, \texttt{glm-4.6}, is excluded from API comparison because its monetary cost is unavailable.

\textbf{Finding 9: API substantially reorders the model ranking relative to raw task performance.}
The highest pipeline score is achieved by \texttt{deepseek-v4-pro} ($P=87.03$, $R=85.34$), but its API is only 64.54.
By contrast, \texttt{qwen3-coder-flash} obtains a much lower pipeline score ($P=35.51$, $R=25.97$) yet achieves the highest API, 256.13.
This inversion is not a statistical artifact: \texttt{qwen3-coder-flash} consumes only 608.36 seconds, \$0.0469, and 3.48M tokens, whereas \texttt{deepseek-v4-pro} consumes 7461.57 seconds, \$8.68, and 136.76M tokens.
Thus, \texttt{qwen3-coder-flash} is approximately 3.97$\times$ more productive by API despite achieving only 41\% of \texttt{deepseek-v4-pro}'s pipeline score.

This result highlights the central role of API: it is not a replacement for correctness or end-to-end completion, but a measure of engineering throughput under resource constraints.
A model that cheaply solves a smaller fraction of the benchmark can be more productive than a model that solves more tasks only by consuming orders of magnitude more budget.
This distinction is important for agent deployment, where users often care not only whether a model can eventually make progress, but whether the progress is worth the wall-clock delay, monetary cost, and context pressure it imposes.
In this sense, API exposes a different axis of evaluation from the raw pipeline score: raw score measures achieved capability, whereas API measures capability converted into usable work.

\textbf{Finding 10: Among high-performing agents, API exposes the cost of over-deliberation and context-heavy execution.}
The comparison between \texttt{deepseek-v4-pro} and \texttt{gpt-5.5} is especially informative.
\texttt{deepseek-v4-pro} achieves a higher pipeline score than \texttt{gpt-5.5} (87.03 vs. 74.71), but \texttt{gpt-5.5} has a higher API (82.98 vs. 64.54).
The two runs have nearly identical monetary cost (\$8.68 vs. \$8.77), so the productivity gap is not explained by price alone.
Instead, \texttt{deepseek-v4-pro} uses 6.17$\times$ more tokens and 1.37$\times$ more time, indicating that its additional score is obtained through substantially heavier interaction with the environment and a much larger accumulated context footprint.
API therefore penalizes a behavior that raw score alone would hide: high competence can still be operationally inefficient when it requires excessive tool calls, repeated debugging cycles, or verbose context accumulation.

A similar pattern appears for other strong models.
\texttt{deepseek-v4-flash} reaches a competitive pipeline score of 67.93 and mean reward of 66.48, but its API is only 67.98 because it consumes 157.85M tokens.
\texttt{qwen3.6-max-preview} reaches $P=66.78$ and $R=56.72$, but its API falls to 58.54 due primarily to its very high monetary cost of \$67.28.
These cases show that resource inefficiency can arise through different channels: some agents are token-inefficient, some are price-inefficient, and some are time-inefficient.
The multiplicative denominator in API is useful precisely because it does not allow one resource dimension to be ignored when the others look acceptable.

\textbf{Finding 11: API separates fast partial solvers from balanced productive agents and capability-heavy solvers.}
The API ranking reveals three qualitatively different operating regimes.
The profile shapes in Figure~\ref{fig:efficiency_profiles} make this separation visible: some models form efficiency-heavy profiles with weak quality axes, while others form quality-heavy profiles with compressed efficiency axes.
First, there are fast and inexpensive partial solvers, represented by \texttt{qwen3-coder-flash} and \texttt{deepseek-chat}.
They achieve the two highest API values, 256.13 and 148.29, because they produce non-trivial benchmark progress with very low cost.
However, their pipeline scores remain modest, so their high API should be interpreted as high marginal productivity rather than strong end-to-end task mastery.

Second, there are balanced productive agents that maintain relatively high task utility without excessive resource consumption.
\texttt{gpt-5.5} is the clearest example in this group: it has the second-highest valid pipeline score ($P=74.71$) while still ranking fifth by API (82.98).
If we impose a practical capability floor of $P \geq 60$, \texttt{gpt-5.5} becomes the most productive model by API, ahead of \texttt{deepseek-v4-flash}, \texttt{deepseek-v4-pro}, and \texttt{qwen3.6-max-preview}.
This suggests that \texttt{gpt-5.5} offers the strongest balance between task completion and resource discipline among the high-performing agents in our evaluation.

Third, there are capability-heavy solvers such as \texttt{deepseek-v4-pro}, \texttt{deepseek-v4-flash}, and \texttt{qwen3.6-max-preview}.
These agents achieve strong raw scores, but their productivity is reduced by long runtimes, high token usage, or high monetary cost.
They are valuable when maximum attainable task score is the primary objective, but they are less attractive when the evaluation criterion is engineering output per unit budget.
API therefore makes explicit a deployment-relevant trade-off that is obscured by completion metrics alone: the best model for maximizing benchmark score is not necessarily the best model for scalable agentic engineering.

Overall, API complements the earlier analyses by combining outcome quality and resource discipline into a single operational view.
API ties all important dimensions together and shows that current LLM agents differ not only in capability, but also in how efficiently they spend time, money, and context to realize that capability.
This is a central consideration for long-horizon agent evaluation: an agent that is powerful but expensive, slow, or context-hungry may be less productive in practice than a more modest agent that produces reliable progress with disciplined resource use.

