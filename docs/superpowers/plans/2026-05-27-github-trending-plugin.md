# GitHub Trending Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AstrBot plugin that exposes `/trending github` and an AI-callable trending tool, fetches GitHub Trending, and summarizes project descriptions in Chinese through either AstrBot's default model or a custom OpenAI-compatible model.

**Architecture:** Keep AstrBot integration in `main.py`, route all business logic through `services/trending_service.py`, isolate GitHub scraping in `providers/github_trending.py`, and isolate summary generation behind two summarizer implementations. Command output and AI tool output both depend on the same service result model.

**Tech Stack:** Python 3, AstrBot plugin API, `aiohttp`, `beautifulsoup4`, `pytest`, `pytest-asyncio`

---

Repository note: the current workspace is not a Git repository, so commit steps are intentionally omitted from this plan.

### Task 1: Scaffold plugin metadata, configuration, and shared models

**Files:**
- Create: `main.py`
- Create: `metadata.yaml`
- Create: `requirements.txt`
- Create: `_conf_schema.json`
- Create: `README.md`
- Create: `models/__init__.py`
- Create: `models/trending.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing model test**

```python
from models.trending import TrendingItem, TrendingResult


def test_trending_item_defaults():
    item = TrendingItem(
        name="owner/repo",
        url="https://github.com/owner/repo",
        stars_today="123 stars today",
        description="Example project",
    )

    assert item.language == "Unknown"
    assert item.summary_zh == ""


def test_trending_result_holds_items():
    item = TrendingItem(
        name="owner/repo",
        url="https://github.com/owner/repo",
        stars_today="123 stars today",
        description="Example project",
    )

    result = TrendingResult(source="github", fetched_at="2026-05-27T00:00:00Z", items=[item])

    assert result.source == "github"
    assert result.items[0].name == "owner/repo"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError` for `models.trending`

- [ ] **Step 3: Write minimal shared models and plugin skeleton files**

```python
# models/trending.py
from dataclasses import dataclass, field


@dataclass(slots=True)
class TrendingItem:
    name: str
    url: str
    stars_today: str
    description: str
    language: str = "Unknown"
    summary_zh: str = ""


@dataclass(slots=True)
class TrendingResult:
    source: str
    fetched_at: str
    items: list[TrendingItem] = field(default_factory=list)
```

```python
# models/__init__.py
from .trending import TrendingItem, TrendingResult

__all__ = ["TrendingItem", "TrendingResult"]
```

```text
# requirements.txt
aiohttp
beautifulsoup4
pytest
pytest-asyncio
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_models.py -v`
Expected: PASS with 2 passing tests

- [ ] **Step 5: Add initial plugin metadata and config files**

```yaml
# metadata.yaml
name: astrbot_plugin_trending
desc: Fetch trending content sources for AstrBot, starting with GitHub Trending.
version: 0.1.0
author: Codex
repo: ""
```

```json
[
  {
    "name": "summary_mode",
    "type": "select",
    "label": "Summary Mode",
    "description": "Choose whether to summarize descriptions with AstrBot's current model or a custom OpenAI-compatible model.",
    "default": "astrbot_default",
    "options": [
      {
        "label": "AstrBot Default",
        "value": "astrbot_default"
      },
      {
        "label": "Custom OpenAI Compatible",
        "value": "custom_openai_compatible"
      }
    ]
  }
]
```

### Task 2: Add GitHub Trending parser with TDD

**Files:**
- Create: `providers/__init__.py`
- Create: `providers/github_trending.py`
- Create: `tests/test_github_provider.py`

- [ ] **Step 1: Write the failing parser test using representative HTML**

```python
import pytest

from providers.github_trending import GitHubTrendingProvider


@pytest.mark.asyncio
async def test_parse_trending_items_from_html():
    html = """
    <article class="Box-row">
      <h2><a href="/owner/repo"> owner / repo </a></h2>
      <p>Example repository description.</p>
      <span itemprop="programmingLanguage">Python</span>
      <span>123 stars today</span>
    </article>
    """

    provider = GitHubTrendingProvider(timeout_seconds=10, user_agent="test-agent")
    items = provider.parse_items(html)

    assert len(items) == 1
    assert items[0].name == "owner/repo"
    assert items[0].url == "https://github.com/owner/repo"
    assert items[0].description == "Example repository description."
    assert items[0].language == "Python"
    assert items[0].stars_today == "123 stars today"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_github_provider.py::test_parse_trending_items_from_html -v`
Expected: FAIL with `ModuleNotFoundError` or missing class error

- [ ] **Step 3: Write minimal provider implementation**

```python
from bs4 import BeautifulSoup

from models import TrendingItem


class GitHubTrendingProvider:
    BASE_URL = "https://github.com/trending"

    def __init__(self, timeout_seconds: int, user_agent: str) -> None:
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent

    def parse_items(self, html: str) -> list[TrendingItem]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[TrendingItem] = []

        for article in soup.select("article.Box-row"):
            link = article.select_one("h2 a")
            if link is None:
                continue

            repo_path = " ".join(link.get_text(" ", strip=True).split()).replace(" / ", "/")
            description_node = article.select_one("p")
            language_node = article.select_one("span[itemprop='programmingLanguage']")
            stars_today = ""

            for span in article.select("span"):
                text = " ".join(span.get_text(" ", strip=True).split())
                if "stars today" in text:
                    stars_today = text
                    break

            items.append(
                TrendingItem(
                    name=repo_path,
                    url=f"https://github.com/{repo_path}",
                    stars_today=stars_today or "Unknown",
                    description=description_node.get_text(" ", strip=True) if description_node else "",
                    language=language_node.get_text(" ", strip=True) if language_node else "Unknown",
                )
            )

        return items
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_github_provider.py::test_parse_trending_items_from_html -v`
Expected: PASS

- [ ] **Step 5: Add fetch-path test and implementation**

```python
@pytest.mark.asyncio
async def test_fetch_items_uses_client_response():
    class FakeResponse:
        async def text(self):
            return """
            <article class="Box-row">
              <h2><a href="/owner/repo"> owner / repo </a></h2>
              <span>123 stars today</span>
            </article>
            """

        def raise_for_status(self):
            return None

    class FakeSession:
        def __init__(self):
            self.requested_url = None
            self.requested_headers = None

        async def get(self, url, headers, timeout):
            self.requested_url = url
            self.requested_headers = headers
            return FakeResponse()

    provider = GitHubTrendingProvider(timeout_seconds=10, user_agent="test-agent")
    session = FakeSession()

    items = await provider.fetch_items(session)

    assert session.requested_url == "https://github.com/trending"
    assert session.requested_headers["User-Agent"] == "test-agent"
    assert items[0].name == "owner/repo"
```

Run red then green with: `uv run pytest tests/test_github_provider.py -v`

### Task 3: Add summarizer abstractions and mode-specific tests

**Files:**
- Create: `summarizers/__init__.py`
- Create: `summarizers/astrbot_default.py`
- Create: `summarizers/custom_openai.py`
- Create: `tests/test_summarizers.py`

- [ ] **Step 1: Write failing tests for both summary modes**

```python
import pytest

from summarizers.astrbot_default import AstrBotDefaultSummarizer
from summarizers.custom_openai import CustomOpenAISummarizer, CustomOpenAIConfigError


@pytest.mark.asyncio
async def test_astrbot_default_summarizer_uses_context_provider():
    class FakeContext:
        async def get_current_chat_provider_id(self, event):
            return "provider-1"

        async def llm_generate(self, *, provider_id, system_prompt, user_prompt):
            assert provider_id == "provider-1"
            assert "Example project" in user_prompt
            return "中文总结"

    summarizer = AstrBotDefaultSummarizer(FakeContext())
    summary = await summarizer.summarize("Example project", event=object())

    assert summary == "中文总结"


@pytest.mark.asyncio
async def test_custom_openai_requires_complete_config():
    summarizer = CustomOpenAISummarizer(
        base_url="",
        api_key="",
        model="",
        timeout_seconds=10,
    )

    with pytest.raises(CustomOpenAIConfigError):
        await summarizer.summarize("Example project", event=None)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_summarizers.py -v`
Expected: FAIL because summarizer modules do not exist

- [ ] **Step 3: Write minimal summarizer implementations**

```python
# summarizers/astrbot_default.py
class AstrBotDefaultSummarizer:
    def __init__(self, context) -> None:
        self.context = context

    async def summarize(self, description: str, event) -> str:
        if not description:
            return ""

        provider_id = await self.context.get_current_chat_provider_id(event)
        return await self.context.llm_generate(
            provider_id=provider_id,
            system_prompt="You summarize GitHub project descriptions into concise Chinese.",
            user_prompt=f"Please summarize this GitHub project description in Chinese:\n{description}",
        )
```

```python
# summarizers/custom_openai.py
class CustomOpenAIConfigError(ValueError):
    pass


class CustomOpenAISummarizer:
    def __init__(self, base_url: str, api_key: str, model: str, timeout_seconds: int) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def summarize(self, description: str, event) -> str:
        if not description:
            return ""
        if not self.base_url or not self.api_key or not self.model:
            raise CustomOpenAIConfigError("Custom OpenAI-compatible summary config is incomplete.")
        return ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_summarizers.py -v`
Expected: PASS for the default summarizer test and config validation test

- [ ] **Step 5: Add failing HTTP-path test for custom summarizer and implement it**

```python
@pytest.mark.asyncio
async def test_custom_openai_sends_chat_completion_request():
    class FakeResponse:
        async def json(self):
            return {"choices": [{"message": {"content": "中文总结"}}]}

        def raise_for_status(self):
            return None

    class FakeSession:
        def __init__(self):
            self.last_url = None
            self.last_json = None

        async def post(self, url, headers, json, timeout):
            self.last_url = url
            self.last_json = json
            return FakeResponse()

    summarizer = CustomOpenAISummarizer(
        base_url="https://example.com/v1",
        api_key="key",
        model="gpt-test",
        timeout_seconds=15,
    )

    result = await summarizer.summarize("Example project", event=None, session=FakeSession())

    assert result == "中文总结"
```

Run red then green with: `uv run pytest tests/test_summarizers.py -v`

### Task 4: Add service orchestration and command formatting with TDD

**Files:**
- Create: `services/__init__.py`
- Create: `services/trending_service.py`
- Create: `tests/test_trending_service.py`

- [ ] **Step 1: Write failing service test**

```python
import pytest

from models import TrendingItem
from services.trending_service import TrendingService


@pytest.mark.asyncio
async def test_trending_service_enriches_items_with_summaries():
    class FakeProvider:
        async def fetch_items(self, session):
            return [
                TrendingItem(
                    name="owner/repo",
                    url="https://github.com/owner/repo",
                    stars_today="123 stars today",
                    description="Example project",
                )
            ]

    class FakeSummarizer:
        async def summarize(self, description, event, **kwargs):
            return "中文总结"

    service = TrendingService(
        providers={"github": FakeProvider()},
        summarizer_factory=lambda: FakeSummarizer(),
    )

    result = await service.fetch_trending("github", event=object(), session=object())

    assert result.source == "github"
    assert result.items[0].summary_zh == "中文总结"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_trending_service.py -v`
Expected: FAIL because `TrendingService` does not exist

- [ ] **Step 3: Write minimal service implementation**

```python
from datetime import datetime, timezone

from models import TrendingResult


class TrendingService:
    def __init__(self, providers: dict[str, object], summarizer_factory) -> None:
        self.providers = providers
        self.summarizer_factory = summarizer_factory

    async def fetch_trending(self, source: str, event, session) -> TrendingResult:
        provider = self.providers[source]
        items = await provider.fetch_items(session)
        summarizer = self.summarizer_factory()

        for item in items:
            item.summary_zh = await summarizer.summarize(item.description, event=event, session=session)

        return TrendingResult(
            source=source,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            items=items,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_trending_service.py -v`
Expected: PASS

- [ ] **Step 5: Add failing command-format test and implement formatter**

```python
from models import TrendingItem, TrendingResult
from services.trending_service import format_trending_message


def test_format_trending_message_includes_required_fields():
    result = TrendingResult(
        source="github",
        fetched_at="2026-05-27T00:00:00Z",
        items=[
            TrendingItem(
                name="owner/repo",
                url="https://github.com/owner/repo",
                stars_today="123 stars today",
                description="Example project",
                language="Python",
                summary_zh="中文总结",
            )
        ],
    )

    message = format_trending_message(result)

    assert "GitHub Trending" in message
    assert "owner/repo" in message
    assert "123 stars today" in message
    assert "Python" in message
    assert "中文总结" in message
```

Run red then green with: `uv run pytest tests/test_trending_service.py -v`

### Task 5: Add AI tool wrapper and plugin entry integration

**Files:**
- Create: `tools/__init__.py`
- Create: `tools/trending_tool.py`
- Modify: `main.py`
- Create: `tests/test_trending_tool.py`

- [ ] **Step 1: Write failing tool wrapper test**

```python
import pytest

from models import TrendingResult
from tools.trending_tool import TrendingTool


@pytest.mark.asyncio
async def test_trending_tool_returns_structured_payload():
    class FakeService:
        async def fetch_trending(self, source, event, session):
            return TrendingResult(source=source, fetched_at="now", items=[])

    tool = TrendingTool(service=FakeService())
    payload = await tool.run(source="github", event=object(), session=object())

    assert payload["source"] == "github"
    assert payload["items"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_trending_tool.py -v`
Expected: FAIL because the tool module does not exist

- [ ] **Step 3: Write minimal tool wrapper**

```python
class TrendingTool:
    def __init__(self, service) -> None:
        self.service = service

    async def run(self, source: str, event, session):
        result = await self.service.fetch_trending(source=source, event=event, session=session)
        return {
            "source": result.source,
            "fetched_at": result.fetched_at,
            "items": [item.__dict__ for item in result.items],
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_trending_tool.py -v`
Expected: PASS

- [ ] **Step 5: Integrate plugin entrypoint**

Implement `main.py` so it:

- wires provider and summarizer dependencies from plugin config
- registers `/trending` command
- registers the AI tool in plugin initialization
- formats chat responses through `format_trending_message`

Run: `uv run pytest tests/test_models.py tests/test_github_provider.py tests/test_summarizers.py tests/test_trending_service.py tests/test_trending_tool.py -v`
Expected: PASS

### Task 6: Finalize docs, edge cases, and full verification

**Files:**
- Modify: `providers/github_trending.py`
- Modify: `services/trending_service.py`
- Modify: `main.py`
- Modify: `README.md`
- Create: `tests/test_error_paths.py`

- [ ] **Step 1: Write failing tests for missing description, missing language, and unsupported source**

```python
import pytest

from providers.github_trending import GitHubTrendingProvider
from services.trending_service import TrendingService


def test_parse_items_defaults_missing_language_and_description():
    html = """
    <article class="Box-row">
      <h2><a href="/owner/repo"> owner / repo </a></h2>
      <span>123 stars today</span>
    </article>
    """

    provider = GitHubTrendingProvider(timeout_seconds=10, user_agent="test-agent")
    items = provider.parse_items(html)

    assert items[0].description == ""
    assert items[0].language == "Unknown"


@pytest.mark.asyncio
async def test_trending_service_rejects_unsupported_source():
    service = TrendingService(providers={}, summarizer_factory=lambda: None)

    with pytest.raises(ValueError):
        await service.fetch_trending("weibo", event=None, session=None)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_error_paths.py -v`
Expected: FAIL until edge cases are implemented

- [ ] **Step 3: Implement edge-case handling and README**

`README.md` must include:

- installation path under `AstrBot/data/plugins/astrbot_plugin_trending/`
- `/trending github` command usage
- explanation of both summary modes
- local runtime sync and restart workflow

- [ ] **Step 4: Run the full test suite**

Run: `uv run pytest -v`
Expected: PASS with all tests green

- [ ] **Step 5: Run targeted sanity checks**

Run:

- `Get-ChildItem -Recurse`
- `Get-Content main.py`
- `Get-Content _conf_schema.json`

Expected:

- required plugin files exist
- command path and config schema are present
- repository matches the planned plugin layout

## Self-Review

Spec coverage:

- command and tool entrypoints are covered by Tasks 4 and 5
- GitHub provider is covered by Task 2
- dual summarizer paths are covered by Task 3
- shared service and output formatting are covered by Task 4
- config and docs are covered by Tasks 1 and 6
- error handling and edge cases are covered by Task 6

Placeholder scan:

- no `TODO`, `TBD`, or deferred-code placeholders remain in tasks

Type consistency:

- `TrendingItem`, `TrendingResult`, `TrendingService.fetch_trending`, and `TrendingTool.run` use consistent names across tasks

Plan complete and saved to `docs/superpowers/plans/2026-05-27-github-trending-plugin.md`. Execution will proceed inline in this session unless redirected.
