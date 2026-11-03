from typing import Any, Optional

# Used when a config file has no use_case section
DEFAULT_ENGINE = "mog_cdn"
DEFAULT_EXECUTOR = "mog"


class ComponentInfo:
    provider: str
    config: dict[str, Any]

    def __init__(self, cfg: Optional[dict[str, Any]], default_provider: str):
        cfg = cfg or {}
        self.provider = cfg.get("provider", default_provider)
        self.config = cfg.get("config", {})


class UseCaseInfo:
    """Selects the recommendation engine and the executor of the use case."""

    engine: ComponentInfo
    executor: ComponentInfo

    def __init__(self, cfg: Optional[dict[str, Any]]):
        cfg = cfg or {}
        self.engine = ComponentInfo(cfg.get("engine"), DEFAULT_ENGINE)
        self.executor = ComponentInfo(cfg.get("executor"), DEFAULT_EXECUTOR)
