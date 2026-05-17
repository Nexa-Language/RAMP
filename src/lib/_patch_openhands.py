

def patch_openhands_cache_whitelist(
    extra_models: tuple[str, ...] = (
        "qwen",
        "glm",
        "deepseek",
        "kimi",
        "minimax",
        "mimo",
    ),
) -> None:
    import warnings

    from openhands.sdk.llm.utils import model_features

    # 不同 SDK 版本：较新为 PROMPT_CACHE_PATTERNS，旧为 PROMPT_CACHE_MODELS（均为子串列表）。
    for name in ("PROMPT_CACHE_MODELS", "PROMPT_CACHE_PATTERNS"):
        if hasattr(model_features, name):
            current = list(getattr(model_features, name))
            for m in extra_models:
                if m not in current:
                    current.append(m)
            setattr(model_features, name, current)
            return

    warnings.warn(
        "openhands.sdk.llm.utils.model_features 上未找到 PROMPT_CACHE_MODELS / "
        "PROMPT_CACHE_PATTERNS，已跳过 OpenHands prompt cache 白名单补丁。",
        stacklevel=2,
    )
