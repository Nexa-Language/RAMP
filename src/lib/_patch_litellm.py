

def patch_litellm_keep_cache_control(
    only_when: tuple[str, ...] = (
        "qwen",
        "glm",
        "deepseek",
        "kimi",
        "minimax",
        "mimo",
    ),
) -> None:
    """
    阻止 litellm 的 OpenAI 路径剥掉 cache_control 字段。
    """
    import litellm.llms.openai.chat.gpt_transformation as gpt_t

    cfg_cls = gpt_t.OpenAIGPTConfig
    original = cfg_cls.remove_cache_control_flag_from_messages_and_tools

    def keep(self, model, messages, tools=None):
        if any(k in model.lower() for k in only_when):
            return messages, tools
        return original(self, model, messages, tools)

    cfg_cls.remove_cache_control_flag_from_messages_and_tools = keep