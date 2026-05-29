from datetime import datetime, timezone
import time

from ..models import TrendingResult
from ..summarizers.custom_openai import CustomOpenAIConfigError


class TrendingService:
    def __init__(self, providers: dict[str, object], summarizer_factory, cache_ttl_seconds: int = 300) -> None:
        self.providers = providers
        self.summarizer_factory = summarizer_factory
        self.cache_ttl_seconds = cache_ttl_seconds
        # 缓存结构: {source: (result, expire_time)}
        self._cache: dict[str, tuple[TrendingResult, float]] = {}

    async def fetch_trending(self, source: str, event, session=None) -> TrendingResult:
        # 检查缓存
        cached_result = self._get_from_cache(source)
        if cached_result is not None:
            return cached_result

        provider = self.providers.get(source)
        if provider is None:
            raise ValueError(f"Unsupported trending source: {source}")

        if session is None:
            import httpx

            async with httpx.AsyncClient() as owned_session:
                result = await self._fetch_with_session(provider=provider, source=source, event=event, session=owned_session)
        else:
            result = await self._fetch_with_session(provider=provider, source=source, event=event, session=session)

        # 存入缓存
        self._put_to_cache(source, result)
        return result

    def _get_from_cache(self, source: str) -> TrendingResult | None:
        """从缓存获取数据，如果过期则返回None"""
        if source not in self._cache:
            return None

        result, expire_time = self._cache[source]
        current_time = time.time()

        if current_time > expire_time:
            # 缓存过期，删除
            del self._cache[source]
            return None

        return result

    def _put_to_cache(self, source: str, result: TrendingResult) -> None:
        """将数据存入缓存"""
        expire_time = time.time() + self.cache_ttl_seconds
        self._cache[source] = (result, expire_time)

    def clear_cache(self, source: str | None = None) -> None:
        """清除缓存。如果指定source则只清除该source，否则清除全部"""
        if source is None:
            self._cache.clear()
        elif source in self._cache:
            del self._cache[source]

    async def _fetch_with_session(self, provider, source: str, event, session) -> TrendingResult:
        items = await provider.fetch_items(session)
        summarizer = self.summarizer_factory()

        # 检查 summarizer 是否支持批量翻译
        if hasattr(summarizer, 'summarize_batch'):
            try:
                # 批量翻译所有描述
                descriptions = [item.description for item in items]
                summaries = await summarizer.summarize_batch(descriptions, event=event, session=session)

                # 将翻译结果赋值给对应的 item
                for item, summary in zip(items, summaries):
                    item.summary_zh = summary
            except CustomOpenAIConfigError:
                raise
            except Exception:
                # 批量翻译失败，所有项目的摘要设为空
                for item in items:
                    item.summary_zh = ""
        else:
            # 降级到逐个翻译（兼容旧的 summarizer）
            for item in items:
                try:
                    item.summary_zh = await summarizer.summarize(item.description, event=event, session=session)
                except CustomOpenAIConfigError:
                    raise
                except Exception:
                    item.summary_zh = ""

        return TrendingResult(
            source=source,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            items=items,
        )


def format_trending_message(result: TrendingResult) -> str:
    source_labels = {
        "github": "GitHub",
    }
    title = f"{source_labels.get(result.source, result.source.capitalize())} 热榜"
    lines = [title]

    for index, item in enumerate(result.items, start=1):
        lines.extend(
            [
                "",
                f"{index}. {item.name}",
                f"链接: {item.url}",
                f"今日Star: {item.stars_today}",
                f"语言: {item.language}",
                f"描述: {item.description or '-'}",
                f"中文摘要: {item.summary_zh or '-'}",
            ]
        )

    if not result.items:
        lines.append("")
        lines.append("未从热榜页面解析到任何项目。")

    return "\n".join(lines)
