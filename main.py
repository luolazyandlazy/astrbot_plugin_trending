import sys
from pathlib import Path

from .providers import GitHubTrendingProvider
from .services import TrendingService, format_trending_message
from .summarizers import AstrBotDefaultSummarizer, CustomOpenAISummarizer

try:
    from astrbot.api import AstrBotConfig, logger
    from astrbot.api.event import AstrMessageEvent, filter
    from astrbot.api.star import Context, Star, register
except ImportError:  # pragma: no cover - local tests run without AstrBot installed.
    AstrBotConfig = dict
    logger = None

    class Context:  # pragma: no cover
        pass

    class Star:  # pragma: no cover
        def __init__(self, context: Context):
            self.context = context

    class AstrMessageEvent:  # pragma: no cover
        unified_msg_origin = None

        def plain_result(self, text: str):
            return text

    class _Filter:  # pragma: no cover
        @staticmethod
        def command(_name: str):
            def decorator(func):
                return func

            return decorator

        @staticmethod
        def llm_tool(name: str):
            def decorator(func):
                return func

            return decorator

    filter = _Filter()

    def register(*args, **kwargs):  # pragma: no cover
        def decorator(cls):
            return cls

        return decorator


@register(
    "trending",
    "Codex",
    "获取GitHub热榜数据，通过命令和AI工具提供服务。",
    "0.1.0",
)
class TrendingPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)
        self.config = config
        self.service = self._build_service()

    def _build_service(self) -> TrendingService:
        provider = GitHubTrendingProvider(
            timeout_seconds=int(self.config.get("request_timeout_seconds", 20)),
            user_agent=self.config.get("user_agent", "Mozilla/5.0 (AstrBot Trending Plugin)"),
        )
        return TrendingService(
            providers={"github": provider},
            summarizer_factory=self._build_summarizer,
            cache_ttl_seconds=int(self.config.get("cache_ttl_seconds", 300)),
        )

    def _build_summarizer(self):
        summary_mode = self.config.get("summary_mode", "astrbot_default")
        if summary_mode == "custom_openai_compatible":
            return CustomOpenAISummarizer(
                base_url=self.config.get("custom_base_url", ""),
                api_key=self.config.get("custom_api_key", ""),
                model=self.config.get("custom_model", ""),
                timeout_seconds=int(self.config.get("custom_timeout_seconds", 30)),
            )
        return AstrBotDefaultSummarizer(self.context)

    async def _query_trending_message(self, source: str, event: AstrMessageEvent) -> str:
        result = await self.service.fetch_trending(source=source, event=event)
        return format_trending_message(result)

    @filter.command("trending")
    async def trending(self, event: AstrMessageEvent):
        msg = event.message_str.strip()
        args = msg[len("/trending") :].strip()
        source = args or "github"

        try:
            message = await self._query_trending_message(source=source, event=event)
        except Exception as exc:
            if logger is not None:
                logger.error(f"获取热榜失败 {source}: {exc}")
            yield event.plain_result(f"获取热榜 '{source}' 失败: {exc}")
            return

        yield event.plain_result(message)

    @filter.llm_tool(name="get_trending")
    async def get_trending(self, event: AstrMessageEvent, source: str):
        """
        获取热榜数据并格式化结果供AI使用。

        Args:
            source(string): 热榜来源名称。使用 github 获取 GitHub 热榜。
        """
        try:
            yield event.plain_result(await self._query_trending_message(source=source, event=event))
        except Exception as exc:
            if logger is not None:
                logger.error(f"获取热榜失败 {source}: {exc}")
            yield event.plain_result(f"获取热榜 '{source}' 失败: {exc}")
