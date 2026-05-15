from __future__ import annotations

from dataclasses import dataclass


SUCCESS_STATUSES = {"success_model_finished", "success_iteration_limit", "success_time_limit"}


@dataclass(frozen=True)
class Termination:
    status: str
    reason: str
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status in SUCCESS_STATUSES


def classify_termination(
    *,
    exit_code: str,
    openhands_status: str,
    last_error_code: str,
    last_error_detail: str,
    has_report: bool,
    missing_outputs: list[str],
) -> Termination:
    detail = last_error_detail[:500] if last_error_detail else ""
    if missing_outputs and not has_report:
        return Termination("error_incomplete_outputs", "输出文件不完整", ", ".join(missing_outputs))
    if exit_code == "124":
        return Termination("error_container_timeout", "容器外层 timeout 终止", detail)
    if exit_code and exit_code not in {"0", "None"}:
        return Termination("error_container_exit", f"容器非零退出: {exit_code}", detail)
    text = f"{last_error_code} {last_error_detail}".lower()
    if "badrequest" in text or "invalidparameter" in text:
        return Termination("error_llm_bad_request", "LLM 请求被服务端拒绝", detail)
    if "ratelimit" in text or "rate limit" in text:
        return Termination("error_llm_rate_limit", "LLM 触发限流", detail)
    if last_error_code == "RunnerError" or "typeerror" in text:
        return Termination("error_container_exit", "Runner 执行异常", detail)
    if openhands_status == "error":
        return Termination("error_container_exit", "OpenHands 会话错误结束", detail)
    if openhands_status in {"finished", "success", "complete", "completed"}:
        return Termination("success_model_finished", "模型主动结束", "")
    if has_report:
        return Termination("success_model_finished", "报告已产出", "")
    return Termination("unknown", "无法判断终止状态", detail)
