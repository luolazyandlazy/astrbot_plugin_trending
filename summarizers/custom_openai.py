class CustomOpenAIConfigError(ValueError):
    pass


class CustomOpenAISummarizer:
    def __init__(self, base_url: str, api_key: str, model: str, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def summarize(self, description: str, event, session=None, **kwargs) -> str:
        if not description:
            return ""
        if not self.base_url or not self.api_key or not self.model:
            raise CustomOpenAIConfigError("Custom OpenAI-compatible summary config is incomplete.")

        if session is None:
            import httpx

            async with httpx.AsyncClient() as owned_session:
                return await self._summarize_with_session(description, owned_session)
        return await self._summarize_with_session(description, session)

    async def _summarize_with_session(self, description: str, session) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You summarize GitHub project descriptions into concise Chinese.",
                },
                {
                    "role": "user",
                    "content": description,
                },
            ],
        }
        response = await session.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"].strip()

    async def summarize_batch(self, descriptions: list[str], event, session=None, **kwargs) -> list[str]:
        """批量翻译多个描述，返回对应的中文摘要列表"""
        if not descriptions:
            return []
        if not self.base_url or not self.api_key or not self.model:
            raise CustomOpenAIConfigError("Custom OpenAI-compatible summary config is incomplete.")

        if session is None:
            import httpx

            async with httpx.AsyncClient() as owned_session:
                return await self._summarize_batch_with_session(descriptions, owned_session)
        return await self._summarize_batch_with_session(descriptions, session)

    async def _summarize_batch_with_session(self, descriptions: list[str], session) -> list[str]:
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

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You summarize GitHub project descriptions into concise Chinese.",
                },
                {
                    "role": "user",
                    "content": "".join(prompt_parts),
                },
            ],
        }

        response = await session.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        response_data = response.json()
        response_text = response_data["choices"][0]["message"]["content"].strip()

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
