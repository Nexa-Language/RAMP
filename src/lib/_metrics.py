from __future__ import annotations

TASK_WEIGHTS = [1.0, 2.0, 2.0, 3.0, 3.0, 4.0]
# TASK_WEIGHTS = [1.0, 4.0, 4.0, 3.0, 6.0, 2.0]
NO_RESURRECTION_BONUS = 1.2
RESURRECTION_BONUS = 1.0
NO_RESURRECTION_PASS_BONUS = 1.5
RESURRECTION_PASS_BONUS = 1.0


def compute_mean_reward(scores: list[float], affected_by_prior: list[bool] | None = None) -> float:
    affected = affected_by_prior or [False] * 6
    numerator = 0.0
    denominator = 0.0
    for i in range(6):
        bonus = RESURRECTION_BONUS if affected[i] else NO_RESURRECTION_BONUS
        numerator += scores[i] * TASK_WEIGHTS[i] * bonus
        denominator += TASK_WEIGHTS[i] * bonus
    return numerator / denominator if denominator else 0.0


def compute_pass_score(scores: list[float], affected_by_prior: list[bool] | None = None) -> float:
    affected = affected_by_prior or [False] * 6
    total = 0.0
    for i in range(6):
        passed = 1 if scores[i] >= 60.0 else 0
        bonus = RESURRECTION_PASS_BONUS if affected[i] else NO_RESURRECTION_PASS_BONUS
        total += passed * bonus
    return total / (6 * NO_RESURRECTION_PASS_BONUS) * 100.0


def prior_non_full_score_count(scores: list[float]) -> int:
    return sum(1 for score in scores[:-1] if score < 100.0)


def prior_non_full_flags(scores: list[float]) -> list[bool]:
    flags: list[bool] = []
    prior_seen = False
    for score in scores:
        flags.append(prior_seen)
        if score < 100.0:
            prior_seen = True
    return flags
