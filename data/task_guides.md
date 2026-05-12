# YatCC 编译原理实验 — 精简任务指南

## Task 0: 环境准备
- 无需修改代码，只需构建和评测
- `cmake --build build -t task0 && cmake --build build -t task0-score`

## Task 1: 词法分析
- 输入: 预处理后的 C 源码（含 `# linenum filename flags` 行标记）
- 输出: 与 `clang -cc1 -dump-tokens` 格式一致的 token 流
- 格式: `token_name 'value' [StartOfLine] [LeadingSpace] Loc=<file:line:col>`
- 关键: 行标记（`#` 开头）不是源码内容，但决定文件名和行号
- 评分: token 类型 60% + 位置 30% + 无关字符 10%
- 对照: `build/test/task1/*/answer.txt` 是标准答案

## Task 2: 语法分析
- 输入: Task 1 输出的 token 流
- 输出: JSON 格式的 AST
- 关键: 逐节点对比 JSON 结构（kind/name/value 60% + type 20% + inner 20%）
- 对照: `build/test/task2/*/answer.json` 是标准答案

## Task 3: 中间代码生成
- 输入: JSON 格式的 AST（Task 2 输出）
- 输出: LLVM IR（.ll 文件）
- 关键文件: 只需修改 `task/3/EmitIR.hpp` 和 `task/3/EmitIR.cpp`
- 已实现: `Json2Asg` 类将 JSON 转为 ASG，基础框架覆盖 `000_main.sysu.c`
- 评分: 生成的 IR 用 clang 编译后执行，输出和返回值与标准一致即通过
- 注意: LLVM 17+ 所有指针都是 `ptr` 类型（Opaque Pointers）
- 对照: `build/test/task3/*/answer.ll` 是标准答案

## Task 4: 中间代码优化
- 输入: LLVM IR（O0 级别）
- 输出: 优化后的 LLVM IR
- 评分: `score = sqrt(标准时间/学生时间) * 100`（正确性优先）
- 已有基础: `ConstantFolding` 和 `Mem2Reg`
- 禁止: 直接调用 LLVM 内置 Transform Pass
- 建议: 先确保正确性，再追求性能

## Task 5: 后端代码生成
- 输入: LLVM IR
- 输出: RV64 汇编（.s 文件）
- **只需实现 4 个函数**（在 `task/5/EmitMIR.cpp` 的 `TASK 5 START` 到 `TASK 5 END` 之间）:
  1. `emitBinary` — 二元运算 → RV64 MIR
  2. `emitICmpInst` — 整数比较 → 0/1 结果
  3. `emitLoadInst` — load → LD 或 LW
  4. `emitStoreInst` — store → SD 或 SW
- 框架已实现: 函数序言/尾声、分支跳转、函数调用、PHI 处理
- 使用: `emitMC` 和 `emitV*` 辅助函数生成 MIR
- 评测: 用 qemu-riscv64-static 运行，比较输出和返回值
