from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


BUILD_TARGETS = {0: "task0", 1: "task1", 2: "task2", 3: "task3", 4: "task4", 5: "task5-classic"}
SCORE_TARGETS = {
    0: "task0-score",
    1: "task1-score",
    2: "task2-score",
    3: "task3-score",
    4: "task4-score",
    5: "task5-classic-score",
}
ANSWER_TARGETS = ["task0-answer", "task1-answer", "task2-answer", "task3-answer", "task5-answer"]


def configure_workspace(workspace: Path) -> None:
    subprocess.run(
        [
            "cmake",
            "-S",
            ".",
            "-B",
            "build",
            "-GNinja",
            "-DSTUDENT_ID=EvoBench",
            "-DSTUDENT_NAME=Agent",
            "-DTASK1_WITH=antlr",
            "-DTASK2_WITH=antlr",
            "-DTASK2_REVIVE=ON",
            "-DTASK3_REVIVE=ON",
            "-DTASK4_REVIVE=ON",
            "-DTASK5_REVIVE=ON",
        ],
        cwd=str(workspace),
        capture_output=True,
        timeout=60,
    )


def build_answers(workspace: Path) -> None:
    for target in ANSWER_TARGETS:
        subprocess.run(["cmake", "--build", "build", "-t", target], cwd=str(workspace), capture_output=True, timeout=300)


def parse_score(workspace: Path, task_id: int) -> dict[str, Any]:
    score_json = workspace / f"build/test/task{task_id}/score.json"
    if not score_json.exists():
        score_json = workspace / f"build/test/task{task_id}/score-classic.json"
    if not score_json.exists():
        return {"task_id": task_id, "score": 0.0, "max_score": 100.0, "passed": False, "test_count": 0, "passed_count": 0}
    data = json.loads(score_json.read_text(encoding="utf-8"))
    tests = data.get("tests", [])
    leaderboard = data.get("leaderboard", [])
    total = 0.0
    if isinstance(leaderboard, list):
        for item in leaderboard:
            if isinstance(item, dict) and item.get("name") == "总分":
                total = float(item.get("value") or 0)
                break
    if total == 0.0 and isinstance(tests, list) and tests:
        total = sum(float(t.get("score", 0)) for t in tests if isinstance(t, dict)) / len(tests)
    test_count = len(tests) if isinstance(tests, list) else 0
    passed_count = sum(
        1
        for item in tests
        if isinstance(item, dict) and float(item.get("score", 0)) >= float(item.get("max_score", 100))
    )
    return {
        "task_id": task_id,
        "score": total,
        "max_score": 100.0,
        "passed": total >= 60.0,
        "test_count": test_count,
        "passed_count": passed_count,
    }


def build_and_score(workspace: Path, task_id: int) -> dict[str, Any]:
    build = subprocess.run(
        ["cmake", "--build", "build", "-t", BUILD_TARGETS.get(task_id, f"task{task_id}")],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    if build.returncode != 0:
        err = (build.stderr or build.stdout or "")[-1000:]
        return {"task_id": task_id, "score": 0.0, "max_score": 100.0, "passed": False, "error": err}
    subprocess.run(
        ["cmake", "--build", "build", "-t", SCORE_TARGETS.get(task_id, f"task{task_id}-score")],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    return parse_score(workspace, task_id)
