from typing import Any

from pkg.config import LLMInfo


class IntentManagerConfig:

    llm_info: LLMInfo
    port: int

    def __init__(self, cfg: dict[str, Any]):
        if cfg is not None:
            self.llm_info = LLMInfo(cfg["llm_info"])
            self.port = cfg["port"]
