from enum import Enum
from typing import Any


class KnowledgeGraphType(Enum):
    NEO4J = "neo4j"


class Neo4jKnowledgeGraphConfig:

    url: str

    def __init__(self, cfg: dict[str, Any]):
        if cfg is not None:
            # If config is no longer flat, manually set each field
            for key, value in cfg.items():
                setattr(self, key, value)


class KnowledgeGraphInfo:
    provider: str
    config: dict[str, Any]

    def __init__(self, cfg: dict[str, Any]):
        if cfg is not None:
            for key, value in cfg.items():
                setattr(self, key, value)
