from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class TrendingItem:
    name: str
    url: str
    stars_today: str
    description: str
    language: str = "Unknown"
    summary_zh: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class TrendingResult:
    source: str
    fetched_at: str
    items: list[TrendingItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "fetched_at": self.fetched_at,
            "items": [item.to_dict() for item in self.items],
        }
