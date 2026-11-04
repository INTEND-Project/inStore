from typing import Any

from pkg.config import KnowledgeGraphInfo, LLMInfo, UseCaseInfo


class IntentManagerConfig:

    llm_info: LLMInfo
    kg_info: KnowledgeGraphInfo
    use_case: UseCaseInfo
    port: int

    def __init__(self, cfg: dict[str, Any]):
        if cfg is not None:
            self.llm_info = LLMInfo(cfg["llm_info"])
            self.kg_info = KnowledgeGraphInfo(cfg["knowledge_graph"])
            # Optional, defaults to the MOG CDN use case
            self.use_case = UseCaseInfo(cfg.get("use_case"))
            self.port = cfg["port"]
