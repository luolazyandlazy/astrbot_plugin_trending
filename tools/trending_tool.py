from ..models import TrendingResult


class TrendingTool:
    def __init__(self, service) -> None:
        self.service = service

    async def run(self, source: str, event=None, session=None) -> dict:
        result = await self.service.fetch_trending(source=source, event=event, session=session)
        return self._result_to_payload(result)

    def _result_to_payload(self, result: TrendingResult) -> dict:
        return result.to_dict()


def build_trending_function_tool(service):
    try:
        from pydantic import Field
        from pydantic.dataclasses import dataclass

        from astrbot.core.agent.run_context import ContextWrapper
        from astrbot.core.agent.tool import FunctionTool
        from astrbot.core.astr_agent_context import AstrAgentContext
    except ImportError:
        return None

    @dataclass
    class AstrBotTrendingTool(FunctionTool[AstrAgentContext]):
        # Keep the runtime tool schema close to the service contract so future
        # sources can be added without changing the plugin entrypoint.
        name: str = "trending_lookup"
        description: str = "Fetch trending source entries such as GitHub Trending."
        parameters: dict = Field(
            default_factory=lambda: {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Trending source name. Use github for GitHub Trending.",
                    }
                },
                "required": ["source"],
            }
        )

        async def call(self, context: ContextWrapper[AstrAgentContext], **kwargs):
            import json

            event = getattr(context.context, "event", None)
            payload = await TrendingTool(service).run(source=kwargs["source"], event=event, session=None)
            return json.dumps(payload, ensure_ascii=False, indent=2)

    return AstrBotTrendingTool()
