import re
from urllib.parse import urljoin

from lxml import html as lxml_html

from ..models import TrendingItem


class GitHubTrendingProvider:
    BASE_URL = "https://github.com/trending"

    def __init__(self, timeout_seconds: int, user_agent: str) -> None:
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent

    async def fetch_items(self, session) -> list[TrendingItem]:
        response = await session.get(
            self.BASE_URL,
            headers={"User-Agent": self.user_agent},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        html_text = response.text
        return self.parse_items(html_text)

    def parse_items(self, html_text: str) -> list[TrendingItem]:
        document = lxml_html.fromstring(html_text)
        items: list[TrendingItem] = []
        for article in document.xpath("//article[contains(@class, 'Box-row')]"):
            hrefs = article.xpath(".//h2//a/@href")
            if not hrefs:
                continue

            repo_path = hrefs[0].strip().strip("/")
            description_nodes = article.xpath(".//p")
            language_values = article.xpath(".//span[@itemprop='programmingLanguage']//text()")

            stars_today = "Unknown"
            for span_text in article.xpath(".//span//text()"):
                span_text = self._clean_text(span_text)
                if "stars today" in span_text.lower():
                    stars_today = span_text
                    break

            items.append(
                TrendingItem(
                    name=repo_path,
                    url=urljoin("https://github.com/", repo_path),
                    stars_today=stars_today,
                    description=self._clean_text(description_nodes[0].text_content()) if description_nodes else "",
                    language=self._clean_text(" ".join(language_values)) if language_values else "Unknown",
                )
            )

        return items

    def _clean_text(self, value: str) -> str:
        return " ".join((value or "").split())
