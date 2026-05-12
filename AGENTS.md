# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Build/Test Commands
```bash
# Setup (one-time)
cd YatCC && ./antlr/setup.sh && ./llvm/setup.sh && ./pybind11/setup.sh

# Build specific task
cmake -S . -B build -GNinja
cmake --build build -t task0    # or task1, task2, task3, task4, task5

# Run test/score for specific task
cmake --build build -t task0-score
```

## Code Style (C++)
- C++17 standard enforced via CMake
- `.clang-format` and `.clang-tidy` present in YatCC/
- LLVM coding style for IR-related code

## Key Architecture
- **EvoBench runner** (`src/`): Orchestrates agent evaluation across 6 serial tasks
- **YatCC** (`data/YatCC/`): The compiler project being evaluated (submodule)
- **Eval scripts** (`eval/`): Automation scripts for running benchmarks
- **Website** (`site/`): Leaderboard and blog hosted via GitHub Pages

## Non-Obvious Patterns
- Task 4/5 score files are named `score-classic.json` (not `score.json` like Tasks 0-3)
- Each agent needs an independent workspace copy to avoid CMake build conflicts
- The resurrection mechanism modifies `config.cmake` REVIVE flags
- `YatCC-docs/` contains detailed task documentation that should be injected into agent context

## File Locations
- Task source: `data/YatCC/task/{0-5}/`
- Task README: `data/YatCC/task/{0-5}/README.md`
- Test cases: `data/YatCC/test/cases/`
- Scoring scripts: `data/YatCC/test/task{0-5}/score.py`
- Leaderboard data: `site/assets/data/leaderboard.json`