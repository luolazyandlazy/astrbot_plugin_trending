class AstrBotDefaultSummarizer:
    def __init__(self, context) -> None:
        self.context = context

    async def summarize(self, description: str, event, **kwargs) -> str:
        if not description:
            return ""

        provider_id = await self.context.get_current_chat_provider_id(umo=event.unified_msg_origin)
        llm_resp = await self.context.llm_generate(
            chat_provider_id=provider_id,
            prompt=(
                "Please summarize this GitHub project description into concise Chinese. "
                "Keep it short and factual.\n"
                f"{description}"
            ),
        )
        return getattr(llm_resp, "completion_text", llm_resp)

    async def summarize_batch(self, descriptions: list[str], event, **kwargs) -> list[str]:
        """批量翻译多个描述，返回对应的中文摘要列表"""
        if not descriptions:
            return []

        # 构建批量请求的 prompt
        prompt_parts = [
            "Please summarize the following GitHub project descriptions into concise Chinese. "
            "Keep each summary short and factual. "
            "Return the summaries in JSON array format, one summary per project in the same order.\n\n"
        ]

        for i, desc in enumerate(descriptions, 1):
            if desc:
                prompt_parts.append(f"Project {i}: {desc}\n")
            else:
                prompt_parts.append(f"Project {i}: (no description)\n")

        prompt_parts.append("\nReturn format: [\"summary1\", \"summary2\", ...]")

        provider_id = await self.context.get_current_chat_provider_id(umo=event.unified_msg_origin)
        llm_resp = await self.context.llm_generate(
            chat_provider_id=provider_id,
            prompt="".join(prompt_parts),
        )

        response_text = getattr(llm_resp, "completion_text", llm_resp)

        # 解析 JSON 响应
        import json
        try:
            summaries = json.loads(response_text)
            if isinstance(summaries, list) and len(summaries) == len(descriptions):
                return summaries
        except (json.JSONDecodeError, ValueError):
            pass

        # 如果解析失败，返回空字符串列表
        return [""] * len(descriptions)
