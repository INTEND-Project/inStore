from typing import Any

from pkg.config import KnowledgeGraphInfo, LLMInfo


class IntentManagerConfig:

    llm_info: LLMInfo
    kg_info: KnowledgeGraphInfo
    port: int

    def __init__(self, cfg: dict[str, Any]):
        if cfg is not None:
            self.llm_info = LLMInfo(cfg["llm_info"])
            self.kg_info = KnowledgeGraphInfo(cfg["knowledge_graph"])
            self.port = cfg["port"]
