def patch_openhands_cache_whitelist(extra_models=("qwen", "glm", "deepseek", "kimi", "minimax", "mimo")) -> None:
    from openhands.sdk.llm.utils import model_features

    name  = "PROMPT_CACHE_MODELS"
    current = list(getattr(model_features, name))
    for m in extra_models:
        if m not in current:
            current.append(m)
    setattr(model_features, name, current)